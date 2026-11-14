package vn.navitaxi

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import okhttp3.Call
import okhttp3.OkHttpClient
import java.io.File
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

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
 * App-owned single transfer controller. A stopped download retains a .part file
 * for a future HTTP Range/If-Range request. Explicit cancel discards partial
 * bytes. Immutable prior package versions remain untouched on upgrades.
 * Process death stops the active request, but the partial file persists.
 */
class OfflinePackageManager private constructor(private val app: Context) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val folder = File(app.filesDir, "offline_packages")
    private val http = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
    private val transfer = OfflinePackageTransfer(http, folder)
    private val stateMutable = MutableStateFlow(OfflineManagerState())
    val state: StateFlow<OfflineManagerState> = stateMutable
    private val guard = Any()
    private var activeSpec: OfflinePackageSpec? = null
    private var resumableSpec: OfflinePackageSpec? = null
    private var activeCall: Call? = null
    private val shouldStop = AtomicBoolean(false)
    private val shouldDiscard = AtomicBoolean(false)

    init { refreshDemo() }

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
                status = "Đang xác minh gói mô phỏng nội bộ", error = null
            )
        }
        scope.launch {
            try {
                val ready = OfflinePmtilesStore(app).prepareSynthetic()
                stateMutable.value = stateMutable.value.copy(
                    status = "Đã cài gói PMTiles mô phỏng, SHA-256 hợp lệ",
                    demoInstalled = true, installedBytes = ready.sizeBytes, error = null
                )
            } catch (ex: Exception) {
                stateMutable.value = stateMutable.value.copy(
                    status = "Không thể cài gói mô phỏng", error = ex.message
                )
            }
        }
    }

    fun removeDemo() {
        synchronized(guard) {
            if (stateMutable.value.downloading) return
        }
        scope.launch {
            // Only the known synthetic fixture; no other map package/user data.
            val file = File(folder, "synthetic_test.pmtiles")
            val success = !file.exists() || file.delete()
            refreshDemo()
            stateMutable.value = stateMutable.value.copy(
                status = if (success) "Đã xóa gói thử nghiệm" else "Không thể xóa gói thử nghiệm",
                error = if (success) null else "Tệp đang được sử dụng hoặc không có quyền xóa"
            )
        }
    }

    /**
     * A verified first-party catalog must supply the spec. No real catalog
     * is installed yet. Not callable from a user-entered arbitrary URL.
     */
    fun startRemote(spec: OfflinePackageSpec, allowMobileData: Boolean) {
        spec.validate()
        synchronized(guard) {
            if (stateMutable.value.downloading) return
            if (!networkAllowed(allowMobileData)) {
                stateMutable.value = stateMutable.value.copy(
                    status = "Chưa có mạng được phép sử dụng",
                    error = "Cần Wi-Fi hoặc cho phép dữ liệu di động"
                )
                return
            }
            shouldStop.set(false)
            shouldDiscard.set(false)
            activeSpec = spec
            resumableSpec = spec
            stateMutable.value = stateMutable.value.copy(
                status = "Đang tải gói " + spec.id,
                bytesRead = 0L, totalBytes = spec.sizeBytes,
                downloading = true, paused = false, error = null
            )
        }
        scope.launch {
            try {
                val result = transfer.download(
                    spec, stopped = { shouldStop.get() },
                    onProgress = { now, total ->
                        stateMutable.value = stateMutable.value.copy(
                            bytesRead = now, totalBytes = total
                        )
                    }, onCall = { synchronized(guard) { activeCall = it } }
                )
                stateMutable.value = stateMutable.value.copy(
                    downloading = false, paused = false, bytesRead = result.sizeBytes,
                    status = "Đã xác minh và kích hoạt " + spec.id,
                    error = null
                )
            } catch (_: TransferStopped) {
                if (shouldDiscard.get()) {
                    transfer.discardPartial(spec)
                    stateMutable.value = stateMutable.value.copy(
                        downloading = false, paused = false, bytesRead = 0,
                        status = "Đã hủy và xóa dữ liệu tải dở", error = null
                    )
                } else {
                    stateMutable.value = stateMutable.value.copy(
                        downloading = false, paused = true,
                        status = "Đã tạm dừng; có thể tiếp tục", error = null
                    )
                }
            } catch (ex: Exception) {
                if (shouldDiscard.get()) transfer.discardPartial(spec)
                stateMutable.value = stateMutable.value.copy(
                    downloading = false, paused = !shouldDiscard.get(),
                    status = "Gói chưa được cài: tải lỗi hoặc chưa xác minh",
                    error = ex.message
                )
            } finally {
                synchronized(guard) {
                    activeCall = null
                    activeSpec = null
                }
            }
        }
    }

    fun pause() {
        synchronized(guard) {
            if (!stateMutable.value.downloading) return
            shouldStop.set(true)
            activeCall?.cancel()
        }
    }

    fun resume(allowMobileData: Boolean) {
        val spec = synchronized(guard) {
            if (stateMutable.value.downloading || !stateMutable.value.paused) null else resumableSpec
        } ?: return
        startRemote(spec, allowMobileData)
    }

    fun cancel() {
        synchronized(guard) {
            if (!stateMutable.value.downloading) {
                resumableSpec?.let { transfer.discardPartial(it) }
                stateMutable.value = stateMutable.value.copy(
                    paused = false, bytesRead = 0L, status = "Đã hủy tải dở", error = null
                )
            } else {
                shouldDiscard.set(true)
                shouldStop.set(true)
                activeCall?.cancel()
            }
        }
    }

    fun deleteInstalled(spec: OfflinePackageSpec): Boolean {
        synchronized(guard) {
            if (stateMutable.value.downloading) return false
            return transfer.deleteVersion(spec)
        }
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
