package vn.navitaxi

import android.database.sqlite.SQLiteDatabase
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File

/**
 * An isolated, fabricated Android test fixture: never a real legal limit or
 * physical roadside sign. The production approval list intentionally stays empty.
 */
@RunWith(AndroidJUnit4::class)
class RoadIntelligenceApprovalSmokeTest {
    @Test fun selfDeclaredLicenseCannotActivateSpeedOrSignOverlays() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val folder = File(context.filesDir, "road_intelligence")
        assertTrue(folder.isDirectory || folder.mkdirs())
        val file = File(folder, "road_intelligence.db")
        // Avoid touching a user's pre-existing DB if this is run outside CI.
        if (file.exists()) return
        try {
            SQLiteDatabase.openOrCreateDatabase(file, null).use { db ->
                db.execSQL("CREATE TABLE data_sources(source_id TEXT, source_uri TEXT, license TEXT)")
                db.execSQL("CREATE TABLE road_segments(segment_id TEXT, speed_kmh INT, geometry_geojson TEXT, source_id TEXT, observed_at TEXT, verified_at TEXT)")
                db.execSQL("CREATE TABLE traffic_signs(sign_id TEXT, sign_code TEXT, longitude REAL, latitude REAL, source_id TEXT, observed_at TEXT, verified_at TEXT)")
                db.execSQL("INSERT INTO data_sources VALUES ('test-fixture','https://example.org/test-only','TEST_ONLY')")
                db.execSQL("INSERT INTO road_segments VALUES ('test-road',50,'{\"type\":\"LineString\",\"coordinates\":[[0,0],[1,1]]}','test-fixture','2026-11-14','2026-11-14')")
                db.execSQL("INSERT INTO traffic_signs VALUES ('test-sign','TEST',0.0,0.0,'test-fixture','2026-11-14','2026-11-14')")
            }
            val result = RoadIntelligenceRepository(context).read()
            assertFalse(result.verifiedDatasetPresent)
            assertEquals(0, result.roadCount)
            assertEquals(0, result.signCount)
            assertEquals("{\"type\":\"FeatureCollection\",\"features\":[]}", result.roads)
            assertEquals("{\"type\":\"FeatureCollection\",\"features\":[]}", result.signs)
        } finally {
            file.delete()
            File(file.path + "-wal").delete()
            File(file.path + "-shm").delete()
            File(file.path + "-journal").delete()
        }
    }
}
