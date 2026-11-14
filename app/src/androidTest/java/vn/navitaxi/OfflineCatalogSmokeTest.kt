package vn.navitaxi

import androidx.test.ext.junit.runners.AndroidJUnit4
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import java.security.MessageDigest

@RunWith(AndroidJUnit4::class)
class OfflineCatalogSmokeTest {
    private fun entry(): JSONObject = JSONObject()
        .put("id", "vn-fixture")
        .put("version", "2026.11")
        .put("release_sequence", 11)
        .put("url", "https://example.org/private/fixture.pmtiles")
        .put("size_bytes", 462)
        .put("sha256", "a".repeat(64))
        .put("license", "NaviTaxi test fixture only")
        .put("source_uri", "https://example.org/source")
        .put("is_real_map", false)
        .put("has_verified_speed_limits", false)
        .put("has_verified_signs", false)

    private fun manifest(item: JSONObject = entry()): ByteArray = JSONObject()
        .put("format", "navitaxi-offline-catalog/v1")
        .put("published_at", "2026-11-14T15:00:00Z")
        .put("packages", JSONArray().put(item))
        .toString().toByteArray(Charsets.UTF_8)

    private fun pin(raw: ByteArray) = MessageDigest.getInstance("SHA-256").digest(raw)
        .joinToString("") { "%02x".format(it) }

    @Test fun separatelyApprovedDigestIsMandatory() {
        val raw = manifest()
        val approved = OfflineCatalogVerifier.verify(raw, pin(raw))
        assertEquals(1, approved.size)
        assertEquals(pin(raw), approved.digest)
        assertFalse(approved.get("vn-fixture")!!.spec.hasVerifiedSigns)
        assertFalse(approved.get("vn-fixture")!!.spec.hasVerifiedSpeeds)
        assertThrows(IllegalArgumentException::class.java) {
            OfflineCatalogVerifier.verify(raw, "0".repeat(64))
        }
    }

    @Test fun cannotAdvertiseSpeedOrPhysicalSignVerification() {
        for (flag in listOf("has_verified_speed_limits", "has_verified_signs")) {
            val entry = entry().put(flag, true)
            val raw = manifest(entry)
            assertThrows(IllegalArgumentException::class.java) {
                OfflineCatalogVerifier.verify(raw, pin(raw))
            }
        }
    }

    @Test fun unsafeEndpointAndFakeFieldAreRejected() {
        val options = listOf(
            entry().put("url", "https://tile.openstreetmap.org/fixture.pmtiles"),
            entry().put("url", "https://example.org/fixture.pmtiles?token=secret"),
            entry().put("source_uri", "file:///etc/passwd"),
            entry().put("id", "../escape"),
            entry().put("release_sequence", true),
            entry().put("unknown_speed_limit", 80)
        )
        for (bad in options) {
            val raw = manifest(bad)
            assertThrows(Exception::class.java) {
                OfflineCatalogVerifier.verify(raw, pin(raw))
            }
        }
    }

    @Test fun versionComparisonUsesSequenceAndBlocksRollback() {
        val raw = manifest()
        val approved = OfflineCatalogVerifier.verify(raw, pin(raw))
        val installed = InstalledOfflineRelease("vn-fixture", "2026.11", 11L, "a".repeat(64))
        assertEquals(OfflineReleaseStatus.NOT_INSTALLED, approved.status("vn-fixture", null))
        assertEquals(OfflineReleaseStatus.CURRENT, approved.status("vn-fixture", installed))
        assertEquals(OfflineReleaseStatus.ROLLBACK_REJECTED,
            approved.status("vn-fixture", installed.copy(releaseSequence = 12)))
        assertEquals(OfflineReleaseStatus.SAME_SEQUENCE_CONFLICT,
            approved.status("vn-fixture", installed.copy(sha256 = "b".repeat(64))))
        assertEquals(OfflineReleaseStatus.UPDATE_AVAILABLE,
            approved.status("vn-fixture", installed.copy(releaseSequence = 10)))
    }

    @Test fun duplicateIdsCannotBeApproved() {
        val raw = JSONObject()
            .put("format", "navitaxi-offline-catalog/v1")
            .put("published_at", "2026-11-14T15:00:00Z")
            .put("packages", JSONArray().put(entry()).put(entry()))
            .toString().toByteArray(Charsets.UTF_8)
        assertThrows(IllegalArgumentException::class.java) {
            OfflineCatalogVerifier.verify(raw, pin(raw))
        }
    }
}
