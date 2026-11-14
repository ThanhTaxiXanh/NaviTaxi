package vn.navitaxi

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Reads only source-linked, already-provisioned local data. NEVER generates limits/signs. */
class RoadIntelligenceRepository(context: Context) {
    private val sourceDb = File(context.filesDir, "road_intelligence/road_intelligence.db")

    fun read(): VerifiedRoadDataset {
        if (!sourceDb.isFile) return VerifiedRoadDataset.EMPTY
        return try {
            val db = SQLiteDatabase.openDatabase(
                sourceDb.absolutePath, null, SQLiteDatabase.OPEN_READONLY
            )
            try {
                val signs = JSONArray()
                val roads = JSONArray()
                db.rawQuery(
                    """SELECT s.sign_id, s.sign_code, s.longitude, s.latitude, s.source_id
                       FROM traffic_signs s
                       INNER JOIN data_sources d ON s.source_id = d.source_id
                       WHERE length(d.license) > 0 AND length(d.source_uri) > 0
                       ORDER BY s.sign_id LIMIT 5000""", null
                ).use { cursor ->
                    while (cursor.moveToNext()) {
                        val lon = cursor.getDouble(2)
                        val lat = cursor.getDouble(3)
                        val sourceId = cursor.getString(4)
                        if (!RoadDataValidation.validWgs84(lat, lon) ||
                            sourceId.isNullOrBlank()) continue
                        signs.put(JSONObject()
                            .put("type", "Feature")
                            .put("geometry", JSONObject().put("type", "Point")
                                .put("coordinates", JSONArray().put(lon).put(lat)))
                            .put("properties", JSONObject()
                                .put("id", cursor.getString(0))
                                .put("sign_code", cursor.getString(1))
                                .put("source_id", sourceId)))
                    }
                }
                db.rawQuery(
                    """SELECT r.segment_id, r.speed_kmh, r.geometry_geojson, r.source_id
                       FROM road_segments r
                       INNER JOIN data_sources d ON r.source_id = d.source_id
                       WHERE length(d.license) > 0 AND length(d.source_uri) > 0
                       ORDER BY r.segment_id LIMIT 5000""", null
                ).use { cursor ->
                    while (cursor.moveToNext()) {
                        val speed = cursor.getInt(1)
                        val sourceId = cursor.getString(3)
                        if (!RoadDataValidation.validSpeed(speed, sourceId)) continue
                        val geometry = JSONObject(cursor.getString(2))
                        if (!RoadDataValidation.validLineString(geometry)) continue
                        // No unverified/synthetic legal default is ever inserted.
                        roads.put(JSONObject()
                            .put("type", "Feature").put("geometry", geometry)
                            .put("properties", JSONObject()
                                .put("id", cursor.getString(0))
                                .put("speed_kmh", speed)
                                .put("source_id", sourceId)))
                    }
                }
                VerifiedRoadDataset(
                    roads = JSONObject().put("type", "FeatureCollection")
                        .put("features", roads).toString(),
                    signs = JSONObject().put("type", "FeatureCollection")
                        .put("features", signs).toString(),
                    roadCount = roads.length(),
                    signCount = signs.length(),
                    verifiedDatasetPresent = true
                )
            } finally { db.close() }
        } catch (_: Exception) {
            // Data import path requires schema+source validation in Phase 11.
            VerifiedRoadDataset.EMPTY
        }
    }
}

data class VerifiedRoadDataset(
    val roads: String,
    val signs: String,
    val roadCount: Int,
    val signCount: Int,
    val verifiedDatasetPresent: Boolean
) {
    companion object {
        private const val EMPTY_GEOJSON = "{\"type\":\"FeatureCollection\",\"features\":[]}"
        val EMPTY = VerifiedRoadDataset(EMPTY_GEOJSON, EMPTY_GEOJSON, 0, 0, false)
    }
}
