package vn.navitaxi

import androidx.work.Data
import org.junit.Assert.*
import org.junit.Test

class OfflineWorkContractTest {
    private fun sample() = OfflinePackageSpec(
        id = "approved-fixture", version = "2026-11-14",
        url = "https://example.org/approved-fixture.pmtiles",
        sizeBytes = 462L,
        sha256 = "d9a53b380463498cc31fd59a30d00e07a2f3f32f9f894eefa7b796d20470de9c",
        license = "NaviTaxi own test-only synthetic geometry",
        sourceUri = "https://github.com/ThanhTaxiXanh/NaviTaxi",
        isRealMap = false, hasVerifiedSpeeds = false, hasVerifiedSigns = false
    )

    @Test fun approvedSpecRoundTripsThroughDurableWorkerData() {
        val spec = sample()
        assertEquals(spec, OfflineWorkContract.decode(OfflineWorkContract.encode(spec)))
        assertEquals("navitaxi-approved-pmtiles-download", OfflineWorkContract.UNIQUE_NAME)
        assertFalse(OfflineWorkContract.decode(OfflineWorkContract.encode(spec))!!.hasVerifiedSpeeds)
        assertFalse(OfflineWorkContract.decode(OfflineWorkContract.encode(spec))!!.hasVerifiedSigns)
    }

    @Test fun missingAndMalformedWorkerDataCannotStartTransfer() {
        assertNull(OfflineWorkContract.decode(Data.EMPTY))
        val bad = Data.Builder()
            .putString("id", "../unsafe")
            .putString("version", "2026-11-14")
            .putString("url", "http://tile.openstreetmap.org/any.pmtiles")
            .putLong("size_bytes", 462)
            .putString("sha256", "0".repeat(64))
            .putString("license", "testing")
            .putString("source_uri", "https://example.org")
            .build()
        assertNull(OfflineWorkContract.decode(bad))
    }

    @Test fun noUncheckedLocationOrUnverifiedGeodataFlagIsCreated() {
        val data = OfflineWorkContract.encode(sample())
        assertFalse(data.keyValueMap.containsKey("latitude"))
        assertFalse(data.keyValueMap.containsKey("longitude"))
        assertFalse(data.getBoolean("real_map", true))
        assertFalse(data.getBoolean("verified_speed", true))
        assertFalse(data.getBoolean("verified_sign", true))
    }

    @Test fun wifiOnlyNeverFallsBackToCellularEvenWhenUnmetered() {
        assertTrue(OfflineConnectionPolicy.allowed(true, false, false, false))
        assertTrue(OfflineConnectionPolicy.allowed(false, true, false, false))
        assertFalse(OfflineConnectionPolicy.allowed(false, false, true, false))
        assertTrue(OfflineConnectionPolicy.allowed(false, false, true, true))
        assertFalse(OfflineConnectionPolicy.allowed(false, false, false, true))
        assertFalse(OfflineWorkContract.encode(sample())
            .getBoolean("allow_cellular", true))
        assertTrue(OfflineWorkContract.encode(sample(), allowMobileData = true)
            .getBoolean("allow_cellular", false))
    }
}
