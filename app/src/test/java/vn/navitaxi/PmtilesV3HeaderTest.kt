package vn.navitaxi

import org.junit.Assert.*
import org.junit.Test
import java.nio.ByteBuffer
import java.nio.ByteOrder

class PmtilesV3HeaderTest {
    private fun validHeader(): ByteArray = ByteArray(127).apply {
        "PMTiles".toByteArray(Charsets.US_ASCII).copyInto(this)
        this[7] = 3
        val b = ByteBuffer.wrap(this).order(ByteOrder.LITTLE_ENDIAN)
        b.putLong(8, 127)
        b.putLong(16, 30)
        b.putLong(24, 157)
        b.putLong(32, 50)
        b.putLong(40, 207)
        b.putLong(48, 0)
        b.putLong(56, 207)
        b.putLong(64, 50)
        b.putLong(72, 1)
        b.putLong(80, 1)
        b.putLong(88, 1)
        this[97] = 2
        this[98] = 2
        this[99] = 1
    }

    @Test fun acceptsCorrectV3Sections() {
        assertTrue(PmtilesV3.isValidHeader(validHeader(), 257))
    }

    @Test fun rejectsInvalidVersionAndOutOfBounds() {
        val badVersion = validHeader().also { it[7] = 2 }
        assertFalse(PmtilesV3.isValidHeader(badVersion, 257))
        assertFalse(PmtilesV3.isValidHeader(validHeader(), 256))
        val corrupt = validHeader().also {
            ByteBuffer.wrap(it).order(ByteOrder.LITTLE_ENDIAN).putLong(16, Long.MAX_VALUE)
        }
        assertFalse(PmtilesV3.isValidHeader(corrupt, 257))
    }
    @Test fun rejectsUnknownTileTypeAndEmptyArchive() {
        assertFalse(PmtilesV3.isValidHeader(ByteArray(127), 257))
        val badTileType = validHeader().also { it[99] = 0 }
        assertFalse(PmtilesV3.isValidHeader(badTileType, 257))
    }
}
