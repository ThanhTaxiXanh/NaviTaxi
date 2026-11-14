package vn.navitaxi

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequest
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.util.UUID
import java.util.concurrent.TimeUnit

/**
 * Persist a *non-secret*, approved archive identity alongside WorkManager work.
 * Never accept arbitrary URLs typed into the UI. No provider catalog exists yet.
 */
class OfflineWorkScheduler(private val app: Context) {
    private val wm = WorkManager.getInstance(app)
    private val prefs = app.getSharedPreferences("navitaxi_work_queue", Context.MODE_PRIVATE)

    fun buildRequest(spec: OfflinePackageSpec, allowMobile: Boolean): OneTimeWorkRequest {
        val data = OfflineWorkContract.encode(spec, allowMobile)
        val network = if (allowMobile) NetworkType.CONNECTED else NetworkType.UNMETERED
        return OneTimeWorkRequestBuilder<OfflineDownloadWorker>()
            .setInputData(data)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(network).build())
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
            .addTag("navitaxi-approved-pmtiles")
            .build()
    }

    fun enqueue(spec: OfflinePackageSpec, allowMobile: Boolean): UUID {
        val work = buildRequest(spec, allowMobile)
        // Make a durable record before enqueue: recover after process recreation.
        val json = JSONObject()
            .put("id", spec.id).put("version", spec.version).put("url", spec.url)
            .put("size_bytes", spec.sizeBytes).put("sha256", spec.sha256)
            .put("license", spec.license).put("source_uri", spec.sourceUri)
            .put("real_map", spec.isRealMap)
            .put("verified_speed", spec.hasVerifiedSpeeds)
            .put("verified_sign", spec.hasVerifiedSigns)
        check(prefs.edit()
            .putString("spec_json", json.toString())
            .putString("work_id", work.id.toString())
            .putBoolean("paused", false)
            .putBoolean("allow_mobile", allowMobile)
            .commit()) { "Cannot persist approved work request" }
        // Single active task: replacement cancels old WorkManager work.
        wm.enqueueUniqueWork(OfflineWorkContract.UNIQUE_NAME,
            ExistingWorkPolicy.REPLACE, work)
        return work.id
    }

    fun savedId(): UUID? = runCatching {
        UUID.fromString(prefs.getString("work_id", null))
    }.getOrNull()

    fun savedSpec(): OfflinePackageSpec? = runCatching {
        val json = JSONObject(prefs.getString("spec_json", null) ?: return null)
        OfflineWorkContract.decode(androidx.work.Data.Builder()
            .putString("id", json.getString("id"))
            .putString("version", json.getString("version"))
            .putString("url", json.getString("url"))
            .putLong("size_bytes", json.getLong("size_bytes"))
            .putString("sha256", json.getString("sha256"))
            .putString("license", json.getString("license"))
            .putString("source_uri", json.getString("source_uri"))
            .putBoolean("real_map", json.getBoolean("real_map"))
            .putBoolean("verified_speed", json.getBoolean("verified_speed"))
            .putBoolean("verified_sign", json.getBoolean("verified_sign"))
            .build())
    }.getOrNull()

    fun isPaused(): Boolean = prefs.getBoolean("paused", false)

    fun workFlow(id: UUID) = wm.getWorkInfoByIdFlow(id)

    fun pause() {
        prefs.edit().putBoolean("paused", true).apply()
        savedId()?.let { wm.cancelWorkById(it) }
    }

    suspend fun cancelAndDiscard() = withContext(Dispatchers.IO) {
        val spec = savedSpec()
        // Cancel the work before attempting deletion of its staging files.
        savedId()?.let { id -> wm.cancelWorkById(id).result.get() }
        if (spec != null) {
            val transfer = OfflinePackageTransfer(okhttp3.OkHttpClient(),
                File(app.filesDir, "offline_packages"))
            synchronized(OfflineTransferGate.forVersion(spec)) {
                transfer.discardPartial(spec)
            }
        }
        prefs.edit().remove("spec_json").remove("work_id")
            .remove("allow_mobile").putBoolean("paused", false).commit()
    }

    fun resume(allowMobile: Boolean): UUID? {
        if (!isPaused()) return null
        val spec = savedSpec() ?: return null
        return enqueue(spec, allowMobile)
    }
}
