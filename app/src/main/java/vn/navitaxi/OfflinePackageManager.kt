package vn.navitaxi

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import androidx.work.WorkInfo
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import java.io.File
import java.util.UUID

data class OfflineManagerState(
    val status: String = "Chưa có tiến trình tải",
    val bytesRead: Long = 0L,
    val totalBytes: Long = 0L,
    val downloading: Boolean = false,
    val paused: Boolean = false,
    val demoInstalled: Boolean = false,
    val installedBytes: Long = 0L,
    val error: String? = null
)

/**
 * WorkManager owns remote downloads, not a short-lived app coroutine. Durable
 * requests + private .part/.etag persist across process reconstruction. Explicit
 * pause/cancel are user actions, distinct from WorkManager's automatic retry.
 * Production downloads require a future approved catalog; none is shipped.
 */
class OfflinePackageManager private constructor(private val app: Context) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val folder = File(app.filesDir, "offline_packages")
    private val scheduler = OfflineWorkScheduler(app)
    private val transfer = OfflinePackageTransfer(OkHttpClient(), folder)
    private val stateMutable = MutableStateFlow(OfflineManagerState())
    val state: StateFlow<OfflineManagerState> = stateMutable
    private val guard = Any()
    private var watcher: Job? = null

    init {
        refreshDemo()
        scheduler.savedId()?.let(::watch)
    }

    private fun demoValid(): Boolean {
        val file = File(folder, "synthetic_test.pmtiles")
        if (!file.isFile || file.length() != 462L) return false
        return try {
            val manifest = app.assets.open("pmtiles/synthetic_manifest.json")
                .bufferedReader().use { org.json.JSONObject(it.readText()) }
            OfflinePmtilesStore.digest(file) == manifest.getString("sha256")
        } catch (_: Exception) { false }
    }

    fun refreshDemo() {
        val exists = demoValid()
        stateMutable.value = stateMutable.value.copy(
            demoInstalled = exists, installedBytes = if (exists) 462L else 0L
        )
    }

    fun installDemo() {
        synchronized(guard) {
            if (stateMutable.value.downloading) return
            stateMutable.value = stateMutable.value.copy(
                status = "Đang xác minh gói mô phỏng nội bộ", error = null)
        }
        scope.launch {
            try {
                val ready = OfflinePmtilesStore(app).prepareSynthetic()
                stateMutable.value = stateMutable.value.copy(
                    status = "Đã cài gói PMTiles mô phỏng, SHA-256 hợp lệ",
                    demoInstalled = true, installedBytes = ready.sizeBytes, error = null)
            } catch (ex: Exception) {
                stateMutable.value = stateMutable.value.copy(
                    status = "Không thể cài gói mô phỏng", error = ex.message)
            }
        }
    }

    fun removeDemo() {
        synchronized(guard) { if (stateMutable.value.downloading) return }
        scope.launch {
            // Only the known synthetic fixture, not a user map.
            val file = File(folder, "synthetic_test.pmtiles")
            val success = !file.exists() || file.delete()
            refreshDemo()
            stateMutable.value = stateMutable.value.copy(
                status = if (success) "Đã xóa gói thử nghiệm" else "Không thể xóa gói thử nghiệm",
                error = if (success) null else "Tệp đang được sử dụng hoặc không có quyền xóa")
        }
    }

    /**
     * Called only with an approved first-party catalog record. No live catalog
     * exists, so the Offline page never exposes this action to drivers yet.
     * WorkManager waits for Wi-Fi/unmetered transport instead of falsely failing.
     */
    fun startRemote(spec: OfflinePackageSpec, allowMobileData: Boolean) {
        spec.validate()
        synchronized(guard) {
            if (stateMutable.value.downloading) return
            val id = scheduler.enqueue(spec, allowMobileData)
            stateMutable.value = stateMutable.value.copy(
                status = "Đã xếp hàng tải gói " + spec.id,
                bytesRead = 0L, totalBytes = spec.sizeBytes,
                downloading = true, paused = false, error = null)
            watch(id)
        }
    }

    private fun watch(id: UUID) {
        watcher?.cancel()
        watcher = scope.launch {
            scheduler.workFlow(id).collect { info ->
                if (info == null) return@collect
                val spec = scheduler.savedSpec()
                val size = spec?.sizeBytes ?: stateMutable.value.totalBytes
                val bytes = info.progress.getLong(
                    OfflineWorkContract.PROGRESS_BYTES, stateMutable.value.bytesRead)
                val paused = scheduler.isPaused()
                val old = stateMutable.value
                stateMutable.value = when (info.state) {
                    WorkInfo.State.ENQUEUED, WorkInfo.State.BLOCKED ->
                        old.copy(status = "Đang chờ điều kiện mạng được phép",
                            downloading = true, paused = false, totalBytes = size, error = null)
                    WorkInfo.State.RUNNING ->
                        old.copy(status = "Đang tải và xác minh PMTiles (nền)",
                            downloading = true, paused = false, totalBytes = size,
                            bytesRead = bytes.coerceIn(0L, size.coerceAtLeast(0L)), error = null)
                    WorkInfo.State.SUCCEEDED ->
                        old.copy(status = "Đã xác minh và kích hoạt gói PMTiles",
                            downloading = false, paused = false,
                            totalBytes = size, bytesRead = size, error = null)
                    WorkInfo.State.FAILED ->
                        old.copy(status = "Gói chưa được cài: kiểm tra máy chủ hoặc dữ liệu",
                            downloading = false, paused = false,
                            error = info.outputData.getString(OfflineWorkContract.STATUS_MESSAGE))
                    WorkInfo.State.CANCELLED ->
                        old.copy(
                            status = if (paused) "Đã tạm dừng; có thể tiếp tục" else "Đã hủy tải",
                            downloading = false, paused = paused,
                            error = null)
                }
            }
        }
    }

    fun pause() {
        synchronized(guard) {
            if (!stateMutable.value.downloading) return
            scheduler.pause()
            stateMutable.value = stateMutable.value.copy(
                downloading = false, paused = true, status = "Đã tạm dừng; có thể tiếp tục")
        }
    }

    fun resume(allowMobileData: Boolean) {
        synchronized(guard) {
            if (stateMutable.value.downloading || !stateMutable.value.paused) return
            val id = scheduler.resume(allowMobileData) ?: return
            val spec = scheduler.savedSpec() ?: return
            stateMutable.value = stateMutable.value.copy(
                downloading = true, paused = false, totalBytes = spec.sizeBytes,
                status = "Đã xếp hàng tiếp tục tải", error = null)
            watch(id)
        }
    }

    fun cancel() {
        scope.launch {
            stateMutable.value = stateMutable.value.copy(
                downloading = false, paused = false, status = "Đang hủy tải...")
            try {
                scheduler.cancelAndDiscard()
                stateMutable.value = stateMutable.value.copy(
                    downloading = false, paused = false, bytesRead = 0L,
                    totalBytes = 0L, status = "Đã hủy và xóa dữ liệu tải dở", error = null)
            } catch (ex: Exception) {
                stateMutable.value = stateMutable.value.copy(
                    status = "Không thể xóa tệp tải dở", error = ex.message)
            }
        }
    }

    fun deleteInstalled(spec: OfflinePackageSpec): Boolean =
        synchronized(guard) {
            if (stateMutable.value.downloading) false else transfer.deleteVersion(spec)
        }

    private fun networkAllowed(allowMobile: Boolean): Boolean {
        val manager = app.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            ?: return false
        val network = manager.activeNetwork ?: return false
        val caps = manager.getNetworkCapabilities(network) ?: return false
        if (!caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)) return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) ||
            caps.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) ||
            (allowMobile && caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR))
    }

    companion object {
        @Volatile private var instance: OfflinePackageManager? = null
        fun get(context: Context): OfflinePackageManager =
            instance ?: synchronized(this) {
                instance ?: OfflinePackageManager(context.applicationContext).also { instance = it }
            }
    }
}
