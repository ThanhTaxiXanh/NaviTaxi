package vn.navitaxi

import okhttp3.Call
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.io.IOException
import java.net.URI
import java.security.MessageDigest
import java.util.Locale

/** An approved, license-attributed catalog record. No public OSM tile-server downloads. */
data class OfflinePackageSpec(
    val id: String,
    val version: String,
    val url: String,
    val sizeBytes: Long,
    val sha256: String,
    val license: String,
    val sourceUri: String,
    val isRealMap: Boolean,
    val hasVerifiedSpeeds: Boolean,
    val hasVerifiedSigns: Boolean
) {
    fun validate(allowLoopbackInTests: Boolean = false) {
        require(Regex("[a-z0-9][a-z0-9-]{1,62}").matches(id)) { "Invalid package ID" }
        require(Regex("[0-9A-Za-z][0-9A-Za-z._-]{0,39}").matches(version) &&
            !version.contains("..")) { "Invalid package version" }
        require(sizeBytes in 127..2_000_000_000L) { "Invalid package size" }
        require(Regex("[0-9a-f]{64}").matches(sha256)) { "Invalid SHA-256" }
        require(license.isNotBlank() && sourceUri.isNotBlank()) { "Missing legal provenance" }
        val parsed = URI(url)
        val host = parsed.host?.lowercase(Locale.ROOT) ?: error("Missing host")
        require(parsed.rawUserInfo == null && parsed.fragment == null && parsed.rawQuery == null) { "Unexpected URL component" }
        require(parsed.scheme == "https" ||
            (allowLoopbackInTests && parsed.scheme == "http" &&
             host in setOf("127.0.0.1", "localhost"))) { "Only HTTPS PMTiles transport is allowed" }
        require(host !in setOf("tile.openstreetmap.org", "demotiles.maplibre.org")) {
            "Public tile servers cannot be downloaded as offline packages"
        }
        require(parsed.path.endsWith(".pmtiles")) { "Expected .pmtiles archive URL" }
    }

    val fileStem: String get() = "$id-$version"
}

class TransferStopped : IOException("Package transfer paused or cancelled")

/** Resumable byte-range transport, strict ETag and SHA-256, immutable version activation. */
class OfflinePackageTransfer(
    private val client: OkHttpClient,
    private val folder: File,
    private val allowLoopbackInTests: Boolean = false,
    private val blockSize: Int = 16 * 1024
) {
    init { require(blockSize in 1..(1024 * 1024)) }
    data class TransferResult(val installedFile: File, val sizeBytes: Long, val sha256: String)
    private fun partial(spec: OfflinePackageSpec) = File(folder, spec.fileStem + ".part")
    private fun validator(spec: OfflinePackageSpec) = File(folder, spec.fileStem + ".etag")
    fun installed(spec: OfflinePackageSpec) = File(folder, spec.fileStem + ".pmtiles")

    fun discardPartial(spec: OfflinePackageSpec) {
        spec.validate(allowLoopbackInTests)
        partial(spec).delete()
        validator(spec).delete()
    }

    fun deleteVersion(spec: OfflinePackageSpec): Boolean {
        spec.validate(allowLoopbackInTests)
        discardPartial(spec)
        return !installed(spec).exists() || installed(spec).delete()
    }

    fun download(
        spec: OfflinePackageSpec,
        stopped: () -> Boolean = { false },
        onProgress: (Long, Long) -> Unit = { _, _ -> },
        onCall: (Call) -> Unit = {}
    ): TransferResult {
        spec.validate(allowLoopbackInTests)
        require(folder.isDirectory || folder.mkdirs()) { "Cannot create package directory" }
        val target = installed(spec)
        val usable = folder.usableSpace
        if (usable > 0L && usable < spec.sizeBytes + 10L * 1024L * 1024L) {
            throw IOException("Not enough free device storage for verified PMTiles")
        }
        if (validArchive(target, spec)) return TransferResult(target, spec.sizeBytes, spec.sha256)
        require(!target.exists()) { "Conflicting installed version; refusing overwrite" }
        val part = partial(spec)
        val tagFile = validator(spec)
        if (part.length() >= spec.sizeBytes || (part.length() > 0L &&
                (!tagFile.isFile || !strongEtag(tagFile.readText())))) discardPartial(spec)
        if (stopped()) throw TransferStopped()
        val previousBytes = if (part.isFile) part.length() else 0L
        val previousTag = if (previousBytes > 0) tagFile.readText() else null
        val request = Request.Builder().url(spec.url).header("Accept-Encoding", "identity").apply {
            if (previousBytes > 0 && previousTag != null) {
                header("Range", "bytes=$previousBytes-")
                header("If-Range", previousTag)
            }
        }.build()
        val call = client.newCall(request)
        onCall(call)
        try {
            call.execute().use { response ->
                val redirectedUrl = response.request.url
                require(redirectedUrl.scheme == "https" ||
                    (allowLoopbackInTests && redirectedUrl.scheme == "http" &&
                     redirectedUrl.host in setOf("127.0.0.1", "localhost"))) {
                    "Insecure redirect"
                }
                require(redirectedUrl.host == URI(spec.url).host) {
                    "Cross-host redirect from approved package origin"
                }
                val append = previousBytes > 0 && response.code == 206
                when (response.code) {
                    200 -> {
                        if (previousBytes > 0) discardPartial(spec)
                        val length = response.body?.contentLength() ?: -1L
                        require(length < 0 || length == spec.sizeBytes) { "Response length mismatch" }
                    }
                    206 -> {
                        val actualStart = if (append) previousBytes else 0L
                        val range = response.header("Content-Range") ?: ""
                        val match = Regex("""bytes (\d+)-(\d+)/(\d+)""").matchEntire(range)
                            ?: error("Invalid Content-Range")
                        val (start, end, total) = match.destructured
                        require(start.toLong() == actualStart && total.toLong() == spec.sizeBytes &&
                            end.toLong() >= actualStart && end.toLong() < spec.sizeBytes) {
                            "Wrong HTTP byte range"
                        }
                        if (append) require(response.header("ETag") == previousTag) {
                            "ETag changed during ranged download"
                        }
                    }
                    else -> error("Unexpected HTTP status " + response.code)
                }
                val newTag = response.header("ETag")
                if (strongEtag(newTag)) tagFile.writeText(newTag!!) else tagFile.delete()
                val input = response.body?.byteStream() ?: error("Empty response body")
                var count = if (append) previousBytes else 0L
                FileOutputStream(part, append).use { output ->
                    val chunk = ByteArray(blockSize)
                    onProgress(count, spec.sizeBytes)
                    while (true) {
                        if (stopped()) throw TransferStopped()
                        val n = input.read(chunk)
                        if (n == -1) break
                        if (n == 0) continue
                        count += n
                        require(count <= spec.sizeBytes) { "Exceeded declared package size" }
                        output.write(chunk, 0, n)
                        onProgress(count, spec.sizeBytes)
                    }
                    output.fd.sync()
                }
                require(count == spec.sizeBytes) { "Incomplete archive" }
            }
        } catch (error: IOException) {
            if (stopped()) throw TransferStopped()
            throw error
        }
        if (!validArchive(part, spec)) {
            discardPartial(spec)
            throw IOException("PMTiles header or SHA-256 mismatch")
        }
        require(part.renameTo(target)) { "Cannot activate verified version" }
        tagFile.delete()
        return TransferResult(target, spec.sizeBytes, spec.sha256)
    }

    private fun validArchive(file: File, spec: OfflinePackageSpec): Boolean {
        if (!file.isFile || file.length() != spec.sizeBytes) return false
        return try {
            file.inputStream().use { input ->
                val header = ByteArray(127)
                if (input.read(header) != header.size ||
                    !PmtilesV3.isValidHeader(header, spec.sizeBytes)) return false
            }
            val digest = MessageDigest.getInstance("SHA-256")
            file.inputStream().buffered().use { input ->
                val buffer = ByteArray(16 * 1024)
                while (true) {
                    val n = input.read(buffer)
                    if (n < 0) break
                    if (n > 0) digest.update(buffer, 0, n)
                }
            }
            digest.digest().joinToString("") { "%02x".format(it) } == spec.sha256
        } catch (_: Exception) { false }
    }

    private fun strongEtag(text: String?): Boolean =
        text != null && text.length in 3..160 && text.startsWith("\"") &&
        text.endsWith("\"") && !text.any { it == '\n' || it == '\r' }
}
