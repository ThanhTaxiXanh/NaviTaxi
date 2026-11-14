package vn.navitaxi

/** Explicit experimental providers: no free service may be described as an SLA. */
enum class MapSource(val label: String, val styleUri: String) {
    DEMO_VECTOR("Vector mẫu", "https://demotiles.maplibre.org/style.json"),
    OSM_STREETS("OSM đường phố", "asset://map_styles/osm_streets_experimental.json"),
    EMPTY_OFFLINE("Chưa có dữ liệu", "asset://map_styles/offline_empty.json")
}

object MapSourcePolicy {
    const val MAPLIBRE_VERSION = "13.7.1"
    const val OSM_TILE_HOST = "tile.openstreetmap.org"
    const val APP_USER_AGENT =
        "NaviTaxi/0.2.0 (+https://github.com/ThanhTaxiXanh/NaviTaxi)"
    const val ATTRIBUTION = "© OpenStreetMap contributors"
    const val DEMO_NOTICE = "Chỉ thử nghiệm hiển thị. Không dùng để dẫn đường."
    const val NO_SPEED = "Giới hạn tốc độ: Không có dữ liệu xác minh"
    const val NO_SIGNS = "Biển báo: Chưa có dữ liệu tọa độ xác minh"

    fun needsExplicitOsMConsent(source: MapSource): Boolean =
        source == MapSource.OSM_STREETS

    fun isOfflineSafe(source: MapSource): Boolean =
        source == MapSource.EMPTY_OFFLINE
}
