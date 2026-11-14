package vn.navitaxi

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.work.Data
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkInfo
import androidx.work.WorkManager
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.TimeUnit

/** Proves WorkManager can execute the real worker and reject missing provenance offline. */
@RunWith(AndroidJUnit4::class)
class OfflineWorkManagerSmokeTest {
    @Test fun unapprovedWorkFailsWithoutNetworkOrInstallingAnyMap() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val work = WorkManager.getInstance(context)
        val request = OneTimeWorkRequestBuilder<OfflineDownloadWorker>()
            .setInputData(Data.EMPTY)
            .build()
        work.enqueue(request).result.get(15, TimeUnit.SECONDS)
        var info: WorkInfo? = null
        val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(35)
        while (System.nanoTime() < deadline) {
            info = work.getWorkInfoById(request.id).get(10, TimeUnit.SECONDS)
            if (info?.state?.isFinished == true) break
            Thread.sleep(250)
        }
        assertNotNull("Worker must finish without external server", info)
        assertEquals(WorkInfo.State.FAILED, info!!.state)
        assertEquals("Invalid approved manifest",
            info.outputData.getString(OfflineWorkContract.STATUS_MESSAGE))
    }
}
