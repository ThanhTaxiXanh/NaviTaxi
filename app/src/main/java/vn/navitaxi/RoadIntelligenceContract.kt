package vn.navitaxi

/**
 * Road limits are only "verified" when they came from a known, licensed source.
 * In particular, an unmapped segment MUST NOT inherit an assumed legal limit.
 */
sealed interface SpeedLimitObservation {
    data class Verified(
        val kmh: Int,
        val sourceId: String,
        val observedAt: String?,
        val direction: String
    ) : SpeedLimitObservation {
        init {
            require(kmh in 1..250)
            require(sourceId.isNotBlank())
        }
    }
    data object Unknown : SpeedLimitObservation
}

data class TrafficSignObservation(
    val signId: String,
    val signCode: String,
    val latitude: Double,
    val longitude: Double,
    val sourceId: String,
    val bearingDegrees: Double?
) {
    init {
        require(latitude in -90.0..90.0 && longitude in -180.0..180.0)
        require(sourceId.isNotBlank())
        require(signCode.isNotBlank())
    }
}
