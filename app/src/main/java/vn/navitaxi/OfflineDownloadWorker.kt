package vn.navitaxi

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.ServiceInfo
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.job
import kotlinx.coroutines.withContext
import okhttp3.Call
import okhttp3.OkHttpClient
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Everything needed for a restart is stored in WorkManager's durable Data record.
 * Do not include a customer location, auth token or unapproved URL in worker input.
 */
object OfflineWorkContract {
    const val UNIQUE_NAME = "navitaxi-approved-pmtiles-download"
    const val PROGRESS_BYTES = "received"
    const val TOTAL_BYTES = "expected"
    const val STATUS_MESSAGE = "status"
    const val INSTALLED_NAME = "installed_name"

    fun encode(spec: OfflinePackageSpec): Data {
        spec.validate()
        require(spec.url.length <= 2048 && spec.sourceUri.length <= 1024 &&
            spec.license.length <= 300) { "Metadata too large for durable work" }
        return Data.Builder()
            .putString("id", spec.id)
            .putString("version", spec.version)
            .putString("url", spec.url)
            .putLong("size_bytes", spec.sizeBytes)
            .putString("sha256", spec.sha256)
            .putString("license", spec.license)
            .putString("source_uri", spec.sourceUri)
            .putBoolean("real_map", spec.isRealMap)
            .putBoolean("verified_speed", spec.hasVerifiedSpeeds)
            .putBoolean("verified_sign", spec.hasVerifiedSigns)
            .build()
    }

    fun decode(data: Data): OfflinePackageSpec? = runCatching {
        val spec = OfflinePackageSpec(
            id = requireNotNull(data.getString("id")),
            version = requireNotNull(data.getString("version")),
            url = requireNotNull(data.getString("url")),
            sizeBytes = data.getLong("size_bytes", -1),
            sha256 = requireNotNull(data.getString("sha256")),
            license = requireNotNull(data.getString("license")),
            sourceUri = requireNotNull(data.getString("source_uri")),
            isRealMap = data.getBoolean("real_map", false),
            hasVerifiedSpeeds = data.getBoolean("verified_speed", false),
            hasVerifiedSigns = data.getBoolean("verified_sign", false)
        )
        spec.validate()
        spec
    }.getOrNull()
}

/** WorkManager persists and reschedules the request; .part/.etag persist tile bytes. */
class OfflineDownloadWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {
    @Volatile private var call: Call? = null

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val spec = OfflineWorkContract.decode(inputData) ?: return@withContext
            Result.failure(Data.Builder()
                .putString(OfflineWorkContract.STATUS_MESSAGE, "Invalid approved manifest").build())

        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .callTimeout(5, TimeUnit.MINUTES)
            .followRedirects(false) // no redirected host or scheme surprises
            .build()
        val store = OfflinePackageTransfer(
            client, File(applicationContext.filesDir, "offline_packages")
        )
        val cancellation = currentCoroutineContext().job.invokeOnCompletion {
            call?.cancel() // Release blocked OkHttp reads on coroutine cancellation.
        }
        try {
            setForeground(foreground("Đang tải gói bản đồ đã duyệt", 0, spec.sizeBytes))
            val result = store.download(
                spec,
                stopped = { isStopped || Thread.currentThread().isInterrupted },
                onProgress = { bytes, total ->
                    setProgressAsync(Data.Builder()
                        .putLong(OfflineWorkContract.PROGRESS_BYTES, bytes)
                        .putLong(OfflineWorkContract.TOTAL_BYTES, total)
                        .build())
                },
                onCall = { call = it }
            )
            setProgress(Data.Builder()
                .putLong(OfflineWorkContract.PROGRESS_BYTES, result.sizeBytes)
                .putLong(OfflineWorkContract.TOTAL_BYTES, result.sizeBytes)
                .build())
            Result.success(Data.Builder()
                .putString(OfflineWorkContract.INSTALLED_NAME, result.installedFile.name)
                .putLong(OfflineWorkContract.TOTAL_BYTES, result.sizeBytes)
                .build())
        } catch (cancelled: CancellationException) {
            throw cancelled // WorkManager handles OS stop/cancel and may reschedule
        } catch (stopped: TransferStopped) {
            Result.retry()
        } catch (error: IOException) {
            val message = error.message.orEmpty()
            if (message.contains("SHA-256") || message.contains("header")) {
                Result.failure(Data.Builder()
                    .putString(OfflineWorkContract.STATUS_MESSAGE, "Integrity validation failed")
                    .build())
            } else if (runAttemptCount < 4) {
                Result.retry()
            } else {
                Result.failure(Data.Builder()
                    .putString(OfflineWorkContract.STATUS_MESSAGE, "Download unavailable")
                    .build())
            }
        } catch (_: IllegalArgumentException) {
            Result.failure(Data.Builder()
                .putString(OfflineWorkContract.STATUS_MESSAGE, "Untrusted package metadata")
                .build())
        } catch (_: IllegalStateException) {
            Result.failure(Data.Builder()
                .putString(OfflineWorkContract.STATUS_MESSAGE, "Invalid server range or response")
                .build())
        } finally {
            cancellation.dispose()
            call = null
        }
    }

    private fun foreground(message: String, current: Long, total: Long): ForegroundInfo {
        val notifications = applicationContext.getSystemService(Context.NOTIFICATION_SERVICE)
            as NotificationManager
        val channel = "navitaxi-approved-offline-downloads"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            notifications.createNotificationChannel(
                NotificationChannel(channel, "NaviTaxi – Bản đồ ngoại tuyến",
                    NotificationManager.IMPORTANCE_LOW)
            )
        }
        val note: Notification = NotificationCompat.Builder(applicationContext, channel)
            .setSmallIcon(android.R.drawable.stat_sys_download)
            .setContentTitle("NaviTaxi – Tải bản đồ")
            .setContentText(message)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setProgress(if (total <= 0L) 0 else 100,
                if (total <= 0L) 0 else (current * 100 / total).toInt(), total <= 0L)
            .build()
        return ForegroundInfo(2704, note,
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
    }
}
