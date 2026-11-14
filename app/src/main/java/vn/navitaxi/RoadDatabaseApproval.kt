package vn.navitaxi

import java.io.File
import java.security.MessageDigest

/**
 * Independent publisher approval for the EXACT SQLite bytes, not a source_id
 * or license string supplied by the SQLite database itself.
 *
 * Speeds and physically surveyed signs are approved separately. A SHA pin
 * only protects integrity after a human/source/license/field-evidence review:
 * SHA-256 alone DOES NOT prove road law or the presence of a physical sign.
 */
internal data class ApprovedRoadDatabase(
    val sha256: String,
    val approvedSpeeds: Boolean,
    val approvedSigns: Boolean
) {
    init {
        require(Regex("[0-9a-f]{64}").matches(sha256)) { "Invalid approved DB SHA-256" }
        require(approvedSpeeds || approvedSigns) { "At least one independently reviewed domain is required" }
    }
}

/**
 * Deliberately empty until an independently reviewed source snapshot and field
 * evidence are approved in a code-reviewed release. Never read candidate pins
 * from the database or from a manifest stored alongside that database.
 */
internal object RoadIntelligenceApprovedPins {
    val entries: List<ApprovedRoadDatabase> = emptyList()
}

internal class RoadDatabaseApprovalGate(
    private val approvals: List<ApprovedRoadDatabase> = RoadIntelligenceApprovedPins.entries
) {
    init {
        require(approvals.map { it.sha256 }.distinct().size == approvals.size) {
            "Conflicting approvals for identical SQLite bytes"
        }
    }

    fun check(file: File): ApprovedRoadDatabase? {
        if (!file.isFile || !file.canRead()) return null
        val length = file.length()
        if (length <= 0L || length > MAX_DATABASE_BYTES) return null

        // SQLite could replay a mutable WAL/journal not covered by the main DB hash.
        // Only an immutable, checkpointed release DB is eligible for approval.
        if (listOf("-wal", "-shm", "-journal").any { File(file.path + it).exists() }) {
            return null
        }
        if (approvals.isEmpty()) return null // avoids reading an unapproved DB at all

        return try {
            val digest = MessageDigest.getInstance("SHA-256")
            file.inputStream().buffered().use { input ->
                val buffer = ByteArray(64 * 1024)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    if (count > 0) digest.update(buffer, 0, count)
                }
            }
            val checksum = digest.digest().joinToString("") { "%02x".format(it) }
            approvals.singleOrNull { it.sha256 == checksum }
        } catch (_: Exception) {
            null // fail closed, never substitute a guessed speed limit/sign position
        }
    }

    private companion object {
        const val MAX_DATABASE_BYTES = 2_000_000_000L
    }
}
