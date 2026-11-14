package vn.navitaxi

import okhttp3.OkHttpClient
import org.maplibre.android.module.http.HttpRequestUtil
import java.util.concurrent.TimeUnit

/**
 * Only visible viewport tile requests, no prefetch/bulk OSM download.
 * Keep MapLibre's own cache semantics; do not inject no-cache headers.
 * Identifiable UA is required by OSMF Tile Usage Policy.
 */
object MapNetwork {
    fun install() {
        val client = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val request = chain.request()
                if (request.url.host == MapSourcePolicy.OSM_TILE_HOST) {
                    chain.proceed(request.newBuilder()
                        .header("User-Agent", MapSourcePolicy.APP_USER_AGENT)
                        .build())
                } else {
                    chain.proceed(request)
                }
            }.build()
        HttpRequestUtil.setOkHttpClient(client)
    }
}
