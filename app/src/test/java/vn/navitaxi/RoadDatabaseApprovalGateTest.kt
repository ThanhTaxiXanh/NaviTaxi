package vn.navitaxi

import org.junit.Assert.*
import org.junit.Test
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest

class RoadDatabaseApprovalGateTest {
    private fun pin(bytes: ByteArray): String =
        MessageDigest.getInstance("SHA-256").digest(bytes)
            .joinToString("") { "%02x".format(it) }

    private fun temporaryDb(): File = Files.createTempFile("navitaxi-road-test-", ".db").toFile()
        .apply { deleteOnExit(); writeBytes("NOT_REAL_ROAD_DATA_TEST_ONLY".toByteArray()) }

    @Test fun unapprovedDatabaseCannotBeDisplayedJustBecauseItExists() {
        val file = temporaryDb()
        try {
            assertNull(RoadDatabaseApprovalGate().check(file))
            assertNull(RoadDatabaseApprovalGate(emptyList()).check(file))
        } finally {
            file.delete()
        }
    }

    @Test fun independentlyPinnedBytesAllowOnlyApprovedDomain() {
        val file = temporaryDb()
        try {
            val bytes = file.readBytes()
            val speedsOnly = ApprovedRoadDatabase(
                sha256 = pin(bytes), approvedSpeeds = true, approvedSigns = false)
            val matched = RoadDatabaseApprovalGate(listOf(speedsOnly)).check(file)
            assertEquals(speedsOnly, matched)
            assertTrue(matched!!.approvedSpeeds)
            assertFalse(matched.approvedSigns)
            file.appendText("tampered")
            assertNull(RoadDatabaseApprovalGate(listOf(speedsOnly)).check(file))
        } finally {
            file.delete()
        }
    }

    @Test fun refuseDatabaseWithUnhashedWalOrJournalEvenIfDbHashMatches() {
        val file = temporaryDb()
        try {
            val approved = ApprovedRoadDatabase(pin(file.readBytes()), true, true)
            val gate = RoadDatabaseApprovalGate(listOf(approved))
            for (suffix in listOf("-wal", "-shm", "-journal")) {
                val sidecar = File(file.path + suffix)
                sidecar.writeText("not-pinned")
                try {
                    assertNull(gate.check(file))
                } finally {
                    sidecar.delete()
                }
            }
            assertEquals(approved, gate.check(file))
        } finally {
            file.delete()
        }
    }

    @Test fun malformedPinsOrConflictingSourceApprovalsAreRejected() {
        assertThrows(IllegalArgumentException::class.java) {
            ApprovedRoadDatabase("ABC", true, true)
        }
        assertThrows(IllegalArgumentException::class.java) {
            ApprovedRoadDatabase("f".repeat(64), false, false)
        }
        val a = ApprovedRoadDatabase("f".repeat(64), true, false)
        val b = ApprovedRoadDatabase("f".repeat(64), false, true)
        assertThrows(IllegalArgumentException::class.java) {
            RoadDatabaseApprovalGate(listOf(a, b))
        }
    }

    @Test fun missingAndEmptyFilesFailClosed() {
        val file = temporaryDb()
        file.writeBytes(byteArrayOf())
        try {
            val gate = RoadDatabaseApprovalGate(
                listOf(ApprovedRoadDatabase(pin(byteArrayOf()), true, true)))
            assertNull(gate.check(file))
            file.delete()
            assertNull(gate.check(file))
        } finally {
            file.delete()
        }
    }
}
