package vn.navitaxi

import org.json.JSONObject

/** Defensive validation before sourced geographic data is mapped. */
object RoadDataValidation {
    fun validWgs84(latitude: Double, longitude: Double): Boolean =
        latitude.isFinite() && longitude.isFinite() &&
            latitude in -90.0..90.0 && longitude in -180.0..180.0

    fun validSpeed(kmh: Int, sourceId: String?): Boolean =
        kmh in 1..250 && !sourceId.isNullOrBlank()

    fun validLineString(geometry: JSONObject): Boolean {
        if (geometry.optString("type") != "LineString") return false
        val coords = geometry.optJSONArray("coordinates") ?: return false
        if (coords.length() < 2) return false
        for (i in 0 until coords.length()) {
            val p = coords.optJSONArray(i) ?: return false
            if (p.length() < 2 || !validWgs84(
                p.optDouble(1, Double.NaN),
                p.optDouble(0, Double.NaN)
            )) return false
        }
        return true
    }
}
