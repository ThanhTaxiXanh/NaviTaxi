package vn.navitaxi

import org.json.JSONObject
import java.net.URI
import java.security.MessageDigest
import java.time.Instant

/**
 * A release catalog has no authority merely because it was downloaded over HTTPS.
 * Its exact bytes must match a separately reviewed, trusted SHA-256 pin.
 *
 * No production pin/catalog is currently bundled. This verifier never downloads
 * PMTiles, creates legal speed limits or claims physical traffic sign locations.
 */
object OfflineCatalogVerifier {
    private const val FORMAT = "navitaxi-offline-catalog/v1"
    private const val MAX_CATALOG_BYTES = 1024 * 1024
    private val shaPattern = Regex("[0-9a-f]{64}")
    private val timestampPattern = Regex("\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z")
    private val topKeys = setOf("format", "published_at", "packages")
    private val entryKeys = setOf(
        "id", "version", "release_sequence", "url", "size_bytes", "sha256",
        "license", "source_uri", "is_real_map",
        "has_verified_speed_limits", "has_verified_signs"
    )

    private fun JSONObject.exactKeys(expected: Set<String>) {
        require(keys().asSequence().toSet() == expected) { "Unexpected catalog fields" }
    }

    private fun JSONObject.strictString(key: String, maxLength: Int): String {
        val value = get(key) as? String ?: error("Missing string: $key")
        require(value.isNotBlank() && value.length <= maxLength && value.none { it.code < 32 }) {
            "Invalid string: $key"
        }
        return value
    }

    private fun JSONObject.strictBoolean(key: String): Boolean {
        val value = get(key)
        require(value is Boolean) { "Expected boolean: $key" }
        return value
    }

    private fun JSONObject.strictLong(key: String): Long {
        val value = get(key)
        require(value is Int || value is Long) { "Expected integer: $key" }
        return (value as Number).toLong()
    }

    private fun validatedSourceUri(raw: String) {
        val uri = URI(raw)
        require(uri.scheme == "https" && !uri.host.isNullOrBlank() && uri.port == -1 &&
            uri.rawUserInfo == null && uri.rawQuery == null && uri.rawFragment == null &&
            uri.rawPath.startsWith("/")) { "Untrusted data provenance URI" }
    }

    fun verify(raw: ByteArray, trustedSha256: String): TrustedOfflineCatalog {
        require(raw.isNotEmpty() && raw.size <= MAX_CATALOG_BYTES) { "Catalog too large" }
        require(shaPattern.matches(trustedSha256)) { "Independently approved SHA-256 pin required" }
        val digest = MessageDigest.getInstance("SHA-256").digest(raw)
            .joinToString("") { "%02x".format(it) }
        require(digest == trustedSha256) { "Catalog digest differs from trusted pin" }

        val document = JSONObject(raw.toString(Charsets.UTF_8))
        document.exactKeys(topKeys)
        require(document.strictString("format", 64) == FORMAT) { "Unknown catalog format" }
        val published = document.strictString("published_at", 32)
        require(timestampPattern.matches(published)) { "Expected UTC catalog timestamp" }
        Instant.parse(published) // reject invalid dates
        val array = document.getJSONArray("packages")
        require(array.length() <= 500) { "Too many packages" }
        val releases = linkedMapOf<String, OfflineCatalogRelease>()
        for (i in 0 until array.length()) {
            val item = array.getJSONObject(i)
            item.exactKeys(entryKeys)
            val releaseSequence = item.strictLong("release_sequence")
            require(releaseSequence > 0) { "Invalid release sequence" }
            val verifiedSpeeds = item.strictBoolean("has_verified_speed_limits")
            val verifiedSigns = item.strictBoolean("has_verified_signs")
            require(!verifiedSpeeds && !verifiedSigns) {
                "PMTiles cannot authenticate road speed limits or physical signs"
            }
            val spec = OfflinePackageSpec(
                id = item.strictString("id", 63),
                version = item.strictString("version", 40),
                url = item.strictString("url", 2048),
                sizeBytes = item.strictLong("size_bytes"),
                sha256 = item.strictString("sha256", 64),
                license = item.strictString("license", 300),
                sourceUri = item.strictString("source_uri", 1024),
                isRealMap = item.strictBoolean("is_real_map"),
                hasVerifiedSpeeds = false, hasVerifiedSigns = false
            )
            spec.validate()
            val url = URI(spec.url)
            require(url.port == -1 && url.rawPath.startsWith("/")) { "Unapproved port or path" }
            validatedSourceUri(spec.sourceUri)
            require(releases.put(spec.id, OfflineCatalogRelease(spec, releaseSequence)) == null) {
                "Duplicate package identity"
            }
        }
        return TrustedOfflineCatalog(digest = digest, publishedAt = published,
            entries = releases.toMap())
    }
}

data class OfflineCatalogRelease internal constructor(
    val spec: OfflinePackageSpec,
    val releaseSequence: Long
)

data class InstalledOfflineRelease(
    val id: String,
    val version: String,
    val releaseSequence: Long,
    val sha256: String
)

enum class OfflineReleaseStatus {
    NOT_INSTALLED, CURRENT, UPDATE_AVAILABLE, ROLLBACK_REJECTED, SAME_SEQUENCE_CONFLICT
}

/** Verified catalog entries are immutable and not created from unapproved network JSON. */
class TrustedOfflineCatalog internal constructor(
    val digest: String,
    val publishedAt: String,
    private val entries: Map<String, OfflineCatalogRelease>
) {
    val size: Int get() = entries.size
    fun get(packageId: String): OfflineCatalogRelease? = entries[packageId]

    fun status(packageId: String, installed: InstalledOfflineRelease?): OfflineReleaseStatus {
        val proposed = requireNotNull(get(packageId)) { "Unknown package" }
        if (installed == null) return OfflineReleaseStatus.NOT_INSTALLED
        require(installed.id == packageId && installed.releaseSequence > 0) {
            "Invalid installed release record"
        }
        return when {
            proposed.releaseSequence < installed.releaseSequence ->
                OfflineReleaseStatus.ROLLBACK_REJECTED
            proposed.releaseSequence > installed.releaseSequence ->
                OfflineReleaseStatus.UPDATE_AVAILABLE
            proposed.spec.version == installed.version &&
                proposed.spec.sha256 == installed.sha256 ->
                OfflineReleaseStatus.CURRENT
            else -> OfflineReleaseStatus.SAME_SEQUENCE_CONFLICT
        }
    }
}
