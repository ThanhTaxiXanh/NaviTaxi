package vn.navitaxi

import android.graphics.Color as AndroidColor
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.maplibre.android.MapLibre
import org.maplibre.android.camera.CameraPosition
import org.maplibre.android.camera.CameraUpdateFactory
import org.maplibre.android.geometry.LatLng
import org.maplibre.android.maps.MapLibreMap
import org.maplibre.android.maps.MapView
import org.maplibre.android.maps.Style
import org.maplibre.android.style.layers.CircleLayer
import org.maplibre.android.style.layers.LineLayer
import org.maplibre.android.style.layers.PropertyFactory
import org.maplibre.android.style.sources.GeoJsonSource
import org.maplibre.geojson.Point
import java.util.Locale

private val HANOI = LatLng(21.0285, 105.8542)
private val SYNTHETIC_CENTER = LatLng(0.0, 0.0)
private const val ROADS_SOURCE = "navitaxi-verified-roads"
private const val SIGNS_SOURCE = "navitaxi-verified-signs"

/**
 * MapLibre View in Compose: lifecycle is explicit, including late composition
 * while Activity is already RESUMED. No location permission or GPS request.
 */
@Composable
fun MapScreen(selectedPlace: String? = null, onBack: () -> Unit) {
    val context = LocalContext.current
    val owner = LocalLifecycleOwner.current
    var source by remember { mutableStateOf(MapSource.DEMO_VECTOR) }
    var askToUseOsm by remember { mutableStateOf(false) }
    var pmtilesReady by remember { mutableStateOf<OfflinePmtilesStore.Prepared?>(null) }
    var pmtilesMessage by remember { mutableStateOf("Chưa kiểm tra PMTiles") }
    var pmtilesStyleOpened by remember { mutableStateOf(false) }
    LaunchedEffect(source) {
        if (source == MapSource.PMTILES_TEST) {
            pmtilesReady = null
            pmtilesStyleOpened = false
            pmtilesMessage = "Đang xác minh PMTiles (SHA-256)..."
            try {
                pmtilesReady = withContext(Dispatchers.IO) {
                    OfflinePmtilesStore(context).prepareSynthetic()
                }
                pmtilesMessage = "PMTiles thử nghiệm đã xác minh SHA-256"
            } catch (e: Exception) {
                pmtilesMessage = "Không thể mở PMTiles: " + (e.message ?: "dữ liệu lỗi")
            }
        }
    }
    var map by remember { mutableStateOf<MapLibreMap?>(null) }
    var details by remember { mutableStateOf<String?>(null) }
    var clickListenerInstalled by remember { mutableStateOf(false) }
    var dataset by remember(context) { mutableStateOf(VerifiedRoadDataset.EMPTY) }
    LaunchedEffect(context) {
        dataset = withContext(Dispatchers.IO) {
            RoadIntelligenceRepository(context).read()
        }
    }
    val mapView = remember(context) {
        MapLibre.getInstance(context.applicationContext)
        MapView(context).apply { onCreate(null) }
    }

    DisposableEffect(owner.lifecycle, mapView) {
        var started = false
        var resumed = false
        fun start() { if (!started) { mapView.onStart(); started = true } }
        fun resume() { if (!resumed) { start(); mapView.onResume(); resumed = true } }
        fun pause() { if (resumed) { mapView.onPause(); resumed = false } }
        fun stop() { if (started) { pause(); mapView.onStop(); started = false } }
        val observer = LifecycleEventObserver { _, event ->
            when (event) {
                Lifecycle.Event.ON_START -> start()
                Lifecycle.Event.ON_RESUME -> resume()
                Lifecycle.Event.ON_PAUSE -> pause()
                Lifecycle.Event.ON_STOP -> stop()
                else -> Unit
            }
        }
        owner.lifecycle.addObserver(observer)
        if (owner.lifecycle.currentState.isAtLeast(Lifecycle.State.RESUMED)) resume()
        else if (owner.lifecycle.currentState.isAtLeast(Lifecycle.State.STARTED)) start()
        onDispose {
            owner.lifecycle.removeObserver(observer)
            stop()
            mapView.onDestroy()
        }
    }

    LaunchedEffect(mapView, source, dataset, pmtilesReady) {
        mapView.getMapAsync { liveMap ->
            map = liveMap
            if (!clickListenerInstalled) {
                liveMap.addOnMapClickListener { location ->
                    val hit = liveMap.queryRenderedFeatures(
                        liveMap.projection.toScreenLocation(location), "verified-sign-points"
                    ).firstOrNull()
                    val coordinate = hit?.geometry() as? Point
                    if (hit != null && coordinate != null) {
                        val code = hit.getStringProperty("sign_code") ?: "?"
                        val sourceId = hit.getStringProperty("source_id") ?: "?"
                        details = "Biển " + code +
                            " · WGS84 " + String.format(Locale.US, "%.6f", coordinate.latitude()) +
                            ", " + String.format(Locale.US, "%.6f", coordinate.longitude()) +
                            " · nguồn: " + sourceId
                        true
                    } else {
                        false
                    }
                }
                clickListenerInstalled = true
            }
            liveMap.uiSettings.isCompassEnabled = true
            liveMap.uiSettings.isZoomGesturesEnabled = true
            liveMap.uiSettings.isRotateGesturesEnabled = true
            liveMap.uiSettings.isTiltGesturesEnabled = true
            val styleBuilder = if (source == MapSource.PMTILES_TEST && pmtilesReady != null) {
                Style.Builder().fromJson(pmtilesReady!!.styleJson)
            } else {
                Style.Builder().fromUri(
                    if (source == MapSource.PMTILES_TEST) MapSource.EMPTY_OFFLINE.styleUri
                    else source.styleUri
                )
            }
            liveMap.setStyle(styleBuilder) { style ->
                installRoadOverlays(style, dataset)
                if (source == MapSource.PMTILES_TEST && pmtilesReady != null) {
                    pmtilesStyleOpened = style.getSource("synthetic") != null &&
                        style.getLayer("synthetic-grid-line") != null
                }
            }
            liveMap.cameraPosition = CameraPosition.Builder()
                .target(if (source == MapSource.PMTILES_TEST) SYNTHETIC_CENTER else HANOI)
                .zoom(when (source) {
                    MapSource.PMTILES_TEST -> 0.8
                    MapSource.DEMO_VECTOR -> 4.0
                    else -> 12.0
                })
                .build()
        }
    }

    if (askToUseOsm) {
        AlertDialog(
            onDismissRequest = { askToUseOsm = false },
            title = { Text("Chỉ sử dụng thử nghiệm") },
            text = { Text(
                "Bản đồ đường phố này tải tile OSM cho khu vực đang xem qua Internet. " +
                "Dịch vụ cộng đồng không có SLA và cấm tải hàng loạt/offline. " +
                "Gói PMTiles thử nghiệm hoạt động riêng, không dùng máy chủ OSM."
            ) },
            confirmButton = {
                TextButton(onClick = {
                    askToUseOsm = false
                    source = MapSource.OSM_STREETS
                }) { Text("Đồng ý thử nghiệm") }
            },
            dismissButton = {
                TextButton(onClick = { askToUseOsm = false }) { Text("Hủy") }
            }
        )
    }

    Box(Modifier.fillMaxSize().background(Color(0xFFEFF3EF))) {
        AndroidView(factory = { mapView }, modifier = Modifier.fillMaxSize())
        Column(Modifier.fillMaxWidth().align(Alignment.TopCenter).padding(10.dp),
            verticalArrangement = Arrangement.spacedBy(7.dp)) {
            Surface(shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.surface, shadowElevation = 3.dp) {
                Row(Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = onBack, modifier = Modifier.size(35.dp)) {
                        Icon(Icons.Default.ArrowBack, "Quay lại")
                    }
                    Text("Bản đồ NaviTaxi", modifier = Modifier.weight(1f),
                        style = MaterialTheme.typography.titleMedium)
                    Text("BẢN THỬ", color = MaterialTheme.colorScheme.primary,
                        style = MaterialTheme.typography.labelSmall)
                }
            }
            Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                MapSource.entries.forEach { mode ->
                    FilterChip(
                        selected = source == mode,
                        onClick = {
                            if (mode == MapSource.OSM_STREETS && source != mode) askToUseOsm = true
                            else source = mode
                        },
                        label = { Text(mode.label, fontSize = 11.sp) }
                    )
                }
            }
            Surface(color = MaterialTheme.colorScheme.surface.copy(alpha = 0.96f),
                shape = RoundedCornerShape(12.dp)) {
                Column(Modifier.padding(10.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                    Text("Giới hạn tốc độ: " +
                        if (dataset.roadCount == 0) "Không có dữ liệu xác minh"
                        else dataset.roadCount.toString() + " đoạn đường có nguồn",
                        fontSize = 12.sp)
                    Text("Biển báo: " +
                        if (dataset.signCount == 0) "Chưa có tọa độ xác minh"
                        else dataset.signCount.toString() + " vị trí có nguồn",
                        fontSize = 12.sp)
                    if (source == MapSource.PMTILES_TEST) {
                        Text(pmtilesMessage, fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.primary)
                        if (pmtilesStyleOpened) {
                            Text("MapLibre đã mở style PMTiles cục bộ",
                                fontSize = 11.sp, color = MaterialTheme.colorScheme.primary)
                        }
                        Text("Chỉ có 2 đường sơ đồ nhân tạo; KHÔNG phải đường giao thông.",
                            fontSize = 11.sp, color = MaterialTheme.colorScheme.error)
                    }
                    if (details != null) {
                        Text(details!!, fontSize = 11.sp,
                            color = MaterialTheme.colorScheme.primary)
                    }
                    if (selectedPlace != null) {
                        Text("Địa điểm: " + selectedPlace + " (chưa có tọa độ xác minh để ghim)",
                            fontSize = 11.sp, color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }
        Column(Modifier.align(Alignment.CenterEnd).padding(end = 12.dp),
            verticalArrangement = Arrangement.spacedBy(9.dp)) {
            MapControl(Icons.Default.Add, "Phóng to") {
                map?.animateCamera(CameraUpdateFactory.zoomIn())
            }
            MapControl(Icons.Default.Remove, "Thu nhỏ") {
                map?.animateCamera(CameraUpdateFactory.zoomOut())
            }
            MapControl(Icons.Default.NearMe, "Về Hà Nội") {
                map?.animateCamera(CameraUpdateFactory.newLatLngZoom(HANOI, 12.0))
            }
        }
        Surface(modifier = Modifier.align(Alignment.BottomCenter).fillMaxWidth().padding(10.dp),
            color = MaterialTheme.colorScheme.surface.copy(alpha = 0.97f),
            shape = RoundedCornerShape(12.dp), shadowElevation = 2.dp) {
            Column(Modifier.padding(9.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                Text(MapSourcePolicy.DEMO_NOTICE, fontSize = 11.sp,
                    color = MaterialTheme.colorScheme.primary)
                Text(
                    when (source) {
                        MapSource.OSM_STREETS -> "© OpenStreetMap contributors · xem trực tuyến"
                        MapSource.DEMO_VECTOR -> "MapLibre demo · Natural Earth countries"
                        MapSource.EMPTY_OFFLINE -> "Chưa tải gói bản đồ ngoại tuyến"
                        MapSource.PMTILES_TEST -> "Dữ liệu mô phỏng tự tạo · hoàn toàn ngoại tuyến"
                    },
                    fontSize = 10.sp
                )
            }
        }
    }
}

private fun installRoadOverlays(style: Style, dataset: VerifiedRoadDataset) {
    if (dataset.roadCount > 0) {
        style.addSource(GeoJsonSource(ROADS_SOURCE, dataset.roads))
        style.addLayer(LineLayer("verified-road-lines", ROADS_SOURCE)
            .withProperties(
                PropertyFactory.lineColor(AndroidColor.rgb(220, 60, 50)),
                PropertyFactory.lineWidth(5f)
            ))
    }
    if (dataset.signCount > 0) {
        style.addSource(GeoJsonSource(SIGNS_SOURCE, dataset.signs))
        style.addLayer(CircleLayer("verified-sign-points", SIGNS_SOURCE)
            .withProperties(
                PropertyFactory.circleColor(AndroidColor.rgb(230, 60, 40)),
                PropertyFactory.circleRadius(7f),
                PropertyFactory.circleStrokeColor(AndroidColor.WHITE),
                PropertyFactory.circleStrokeWidth(2f)
            ))
    }
}

@Composable
private fun MapControl(icon: androidx.compose.ui.graphics.vector.ImageVector,
                       description: String, onClick: () -> Unit) {
    Surface(onClick = onClick, color = MaterialTheme.colorScheme.surface,
        shape = RoundedCornerShape(16.dp), shadowElevation = 3.dp,
        modifier = Modifier.size(48.dp)) {
        Box(contentAlignment = Alignment.Center) {
            Icon(icon, contentDescription = description)
        }
    }
}
