package vn.navitaxi

import org.junit.Assert.*
import org.junit.Test

class MapSourcePolicyTest {
    @Test fun osmRequiresExplicitConsentAndIsNeverOfflineData() {
        assertTrue(MapSourcePolicy.needsExplicitOsMConsent(MapSource.OSM_STREETS))
        assertFalse(MapSourcePolicy.isOfflineSafe(MapSource.OSM_STREETS))
        assertFalse(MapSourcePolicy.needsExplicitOsMConsent(MapSource.DEMO_VECTOR))
        assertFalse(MapSourcePolicy.isOfflineSafe(MapSource.DEMO_VECTOR))
        assertTrue(MapSourcePolicy.isOfflineSafe(MapSource.EMPTY_OFFLINE))
        assertTrue(MapSourcePolicy.isOfflineSafe(MapSource.PMTILES_TEST))
    }
    @Test fun noLegalSpeedIsGuessed() {
        assertTrue(MapSourcePolicy.NO_SPEED.contains("Không có dữ liệu"))
        assertTrue(MapSourcePolicy.NO_SIGNS.contains("Chưa có dữ liệu"))
        assertTrue(VerifiedRoadDataset.EMPTY.roads.contains("FeatureCollection"))
        assertEquals(0, VerifiedRoadDataset.EMPTY.roadCount)
        assertEquals(0, VerifiedRoadDataset.EMPTY.signCount)
    }
    @Test fun onlyHttpsOsMHostUsedForManualRasterStyle() {
        assertEquals("tile.openstreetmap.org", MapSourcePolicy.OSM_TILE_HOST)
        assertTrue(MapSourcePolicy.APP_USER_AGENT.startsWith("NaviTaxi/"))
        assertEquals("asset://map_styles/osm_streets_experimental.json",
            MapSource.OSM_STREETS.styleUri)
    }
}
