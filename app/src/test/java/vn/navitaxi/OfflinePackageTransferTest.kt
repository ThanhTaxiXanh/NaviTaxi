package vn.navitaxi

import okhttp3.mockwebserver.Dispatcher
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import okhttp3.mockwebserver.RecordedRequest
import okio.Buffer
import okhttp3.OkHttpClient
import org.junit.Assert.*
import org.junit.Test
import java.io.File
import java.nio.file.Files
import java.security.MessageDigest
import java.util.concurrent.atomic.AtomicBoolean

class OfflinePackageTransferTest {
    private val archive = File("src/main/assets/pmtiles/synthetic_test.pmtiles").readBytes()
    private val checksum = MessageDigest.getInstance("SHA-256").digest(archive)
        .joinToString("") { "%02x".format(it) }

    private fun spec(url: String, version: String = "v1", sha: String = checksum) =
        OfflinePackageSpec("synthetic-grid", version, url, archive.size.toLong(),
            sha, "NaviTaxi synthetic fixture only", "test://fixture",
            false, false, false)

    private fun server(): MockWebServer = MockWebServer().apply {
        dispatcher = object : Dispatcher() {
            override fun dispatch(request: RecordedRequest): MockResponse {
                val from = request.getHeader("Range")?.removePrefix("bytes=")
                    ?.removeSuffix("-")?.toIntOrNull() ?: 0
                val response = MockResponse().addHeader("ETag", "\"fixture-v1\"")
                if (from > 0) {
                    response.setResponseCode(206)
                        .addHeader("Content-Range",
                            "bytes " + from + "-" + (archive.size - 1) + "/" + archive.size)
                }
                return response.setBody(Buffer().write(archive, from, archive.size - from))
            }
        }
        start()
    }

    @Test fun pauseResumeUsesByteRangeAndVerifiesSha() {
        val web = server()
        val dir = Files.createTempDirectory("navitaxi-range").toFile()
        try {
            val s = spec(web.url("/grid.pmtiles").toString())
            val transport = OfflinePackageTransfer(OkHttpClient(), dir, true, blockSize = 64)
            val stop = AtomicBoolean(false)
            try {
                transport.download(s,
                    stopped = { stop.get() },
                    onProgress = { read, _ -> if (read >= 128) stop.set(true) })
                fail("expected controlled pause")
            } catch (_: TransferStopped) { }
            assertEquals(128L, File(dir, "synthetic-grid-v1.part").length())
            assertTrue(File(dir, "synthetic-grid-v1.etag").isFile)
            val installed = transport.download(s)
            assertEquals(archive.size.toLong(), installed.sizeBytes)
            assertArrayEquals(archive, installed.installedFile.readBytes())
            assertEquals(null, web.takeRequest().getHeader("Range"))
            assertEquals("bytes=128-", web.takeRequest().getHeader("Range"))
            assertFalse(File(dir, "synthetic-grid-v1.etag").exists())
        } finally {
            web.shutdown()
            dir.deleteRecursively()
        }
    }

    @Test fun corruptionCannotActivateAndVersionUpgradeDoesNotDeleteOld() {
        val web = server()
        val dir = Files.createTempDirectory("navitaxi-versions").toFile()
        try {
            val transport = OfflinePackageTransfer(OkHttpClient(), dir, true)
            val url = web.url("/fixture.pmtiles").toString()
            val v1 = spec(url, "v1")
            assertTrue(transport.download(v1).installedFile.exists())
            val invalid = spec(url, "bad", "0".repeat(64))
            try {
                transport.download(invalid)
                fail("expected SHA mismatch")
            } catch (expected: Exception) {
                assertFalse(transport.installed(invalid).exists())
            }
            val v2 = spec(url, "v2")
            assertTrue(transport.download(v2).installedFile.exists())
            assertTrue(transport.installed(v1).exists())
            assertTrue(transport.deleteVersion(v1))
            assertFalse(transport.installed(v1).exists())
            assertTrue(transport.installed(v2).exists())
        } finally {
            web.shutdown()
            dir.deleteRecursively()
        }
    }

    @Test fun rejectUnknownLicenseDangerousPathAndPublicOsmHost() {
        assertThrows(IllegalArgumentException::class.java) {
            spec("https://tile.openstreetmap.org/maps.pmtiles").validate()
        }
        assertThrows(IllegalArgumentException::class.java) {
            spec("http://example.com/maps.pmtiles").validate()
        }
        assertThrows(IllegalArgumentException::class.java) {
            spec("https://example.org/map.pmtiles", "../unsafe").validate()
        }
        assertThrows(IllegalArgumentException::class.java) {
            spec("https://example.org/map.pmtiles").copy(license = "").validate()
        }
    }
}
