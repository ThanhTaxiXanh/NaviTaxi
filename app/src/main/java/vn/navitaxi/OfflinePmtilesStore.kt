package vn.navitaxi

import android.content.Context
import android.net.Uri
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.security.MessageDigest

/**
 * Small offline fixture only. Never claims road network, sign positions or legal speeds.
 * Native MapLibre requires byte-range reading and does NOT support PMTiles asset://
 * directly. Verify, copy into app-private storage, then load pmtiles://file://.
 */
class OfflinePmtilesStore(private val context: Context) {
    data class Prepared(
        val styleJson: String,
        val localFile: File,
        val sha256: String,
        val sizeBytes: Long
    )

    /**
     * Call from Dispatchers.IO; no GPS permission and no Internet are used.
     * Only the synthetic fixture can be installed by this method; arbitrary
     * package updates and user-managed downloads are Phase 4.
     */
    fun prepareSynthetic(): Prepared {
        val manifest = JSONObject(
            context.assets.open("pmtiles/synthetic_manifest.json").bufferedReader().use { it.readText() }
        )
        require(manifest.getString("id") == "synthetic-grid-test")
        require(manifest.getString("format") == "navitaxi-offline-package/v1")
        require(!manifest.getBoolean("is_real_map"))
        require(!manifest.getBoolean("has_verified_speed_limits"))
        require(!manifest.getBoolean("has_verified_signs"))
        require(manifest.getString("tile_type") == "mvt")
        require(manifest.getString("layer") == "demo_grid")
        val expectedName = "synthetic_test.pmtiles"
        require(manifest.getString("file") == expectedName)
        val expectedSize = manifest.getLong("size_bytes")
        val expectedSha = manifest.getString("sha256")
        require(expectedSize in 127..(20L * 1024 * 1024))
        require(expectedSha.length == 64 && expectedSha.matches(Regex("[a-f0-9]{64}")))

        val directory = File(context.filesDir, "offline_packages")
        require(directory.isDirectory || directory.mkdirs()) { "Cannot create private offline directory" }
        val output = File(directory, expectedName)
        if (!matches(output, expectedSize, expectedSha)) {
            val partial = File(directory, "$expectedName.partial")
            partial.delete() // only NaviTaxi's own synthetic staging file
            try {
                context.assets.open("pmtiles/$expectedName").use { input ->
                    FileOutputStream(partial).use { outputStream ->
                        val buffer = ByteArray(16 * 1024)
                        while (true) {
                            val n = input.read(buffer)
                            if (n < 0) break
                            if (n > 0) outputStream.write(buffer, 0, n)
                        }
                        outputStream.fd.sync()
                    }
                }
                require(matches(partial, expectedSize, expectedSha)) {
                    "PMTiles fixture is corrupt or SHA-256 is wrong"
                }
                // Replacing only a validated, owned synthetic fixture, not user maps.
                require(partial.renameTo(output)) { "Cannot activate verified PMTiles fixture" }
            } finally {
                partial.delete()
            }
        }
        require(matches(output, expectedSize, expectedSha)) { "PMTiles integrity check failed" }

        val style = JSONObject(
            context.assets.open("map_styles/pmtiles_synthetic.json").bufferedReader().use { it.readText() }
        )
        val tileUri = "pmtiles://" + Uri.fromFile(output).toString()
        style.getJSONObject("sources").getJSONObject("synthetic").put("url", tileUri)
        return Prepared(style.toString(), output, expectedSha, expectedSize)
    }

    private fun matches(file: File, expectedSize: Long, expectedSha: String): Boolean {
        if (!file.isFile || file.length() != expectedSize) return false
        return try {
            file.inputStream().use { input ->
                val header = ByteArray(127)
                if (input.read(header) != header.size || !PmtilesV3.isValidHeader(header, expectedSize)) {
                    return false
                }
            }
            digest(file) == expectedSha
        } catch (_: Exception) {
            false
        }
    }

    companion object {
        fun digest(file: File): String {
            val md = MessageDigest.getInstance("SHA-256")
            file.inputStream().buffered().use { input ->
                val buffer = ByteArray(16 * 1024)
                while (true) {
                    val n = input.read(buffer)
                    if (n < 0) break
                    if (n > 0) md.update(buffer, 0, n)
                }
            }
            return md.digest().joinToString("") { "%02x".format(it) }
        }
    }
}

/**
 * Fast structural guard against corrupted PMTiles v3 headers. MapLibre Native
 * performs the actual indexed tile-range reads and gzip/MVT decompression.
 * The fixture SHA-256 guards all bytes, not only the header.
 */
object PmtilesV3 {
    fun isValidHeader(header: ByteArray, fileBytes: Long): Boolean {
        if (header.size != 127 || fileBytes < 127) return false
        if (!header.copyOfRange(0, 8).contentEquals(
                byteArrayOf(80, 77, 84, 105, 108, 101, 115, 3))) return false
        val buf = ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN)
        val rootOffset = buf.getLong(8)
        val rootLength = buf.getLong(16)
        val metaOffset = buf.getLong(24)
        val metaLength = buf.getLong(32)
        val leafOffset = buf.getLong(40)
        val leafLength = buf.getLong(48)
        val tileOffset = buf.getLong(56)
        val tileLength = buf.getLong(64)
        val tileCount = buf.getLong(72)
        val entryCount = buf.getLong(80)
        val contentCount = buf.getLong(88)
        fun inside(offset: Long, length: Long): Boolean =
            offset >= 127 && length > 0 && offset <= fileBytes && length <= fileBytes - offset
        if (!inside(rootOffset, rootLength) || !inside(metaOffset, metaLength) ||
            !inside(tileOffset, tileLength)) return false
        if (rootOffset + rootLength > 16384) return false
        if (leafLength != 0L && !inside(leafOffset, leafLength)) return false
        if (tileCount < 1 || entryCount < 1 || contentCount < 1) return false
        if (header[97].toInt() !in 1..2 || header[98].toInt() !in 1..2) return false
        if (header[99].toInt() != 1) return false // MVT only, not generic arbitrary binary
        val minZoom = header[100].toInt() and 0xff
        val maxZoom = header[101].toInt() and 0xff
        if (minZoom > maxZoom || maxZoom > 26) return false
        return true
    }
}
