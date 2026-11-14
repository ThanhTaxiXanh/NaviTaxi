package vn.navitaxi

import android.os.Environment
import android.os.StatFs
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.platform.LocalContext
import java.util.Locale

private data class OfflineRegion(val name: String, val icon: String)
private val offlineSamples = listOf(
    OfflineRegion("Hà Nội", "⌂"),
    OfflineRegion("TP. Hồ Chí Minh", "▥"),
    OfflineRegion("Đà Nẵng", "⌁"),
    OfflineRegion("Khánh Hòa", "♧")
)
private fun gb(bytes: Long): String = String.format(Locale("vi", "VN"), "%.1f GB", bytes / 1_000_000_000.0)

@Composable
fun OfflineScreen(preferences: UiPreferences, notify: (String) -> Unit, onBack: () -> Unit) {
    val context = LocalContext.current
    val manager = remember(context) { OfflinePackageManager.get(context) }
    val managerState by manager.state.collectAsState()
    var allVietnam by rememberSaveable { mutableStateOf(false) }
    var provinceQuery by rememberSaveable { mutableStateOf("") }
    val space = remember {
        val stat = StatFs(Environment.getDataDirectory().absolutePath)
        Pair(stat.totalBytes, stat.availableBytes)
    }
    val used = (space.first - space.second).coerceAtLeast(0L)
    val fraction = if (space.first <= 0L) 0f else used.toFloat() / space.first.toFloat()
    val missingSource: () -> Unit = {
        notify("Chưa có danh mục bản đồ PMTiles Việt Nam được xác minh. Gói tải theo tỉnh/toàn quốc còn chờ dữ liệu ở Phase 5.")
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())
        .padding(horizontal = 14.dp).padding(bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(13.dp)) {
        BrandHeader()
        PageHeading("Bản đồ ngoại tuyến",
            "Tải và quản lý bản đồ để dẫn đường ổn định khi không có mạng", onBack)
        NaviCard {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Layers, null, tint = NaviColors.Green,
                    modifier = Modifier.size(42.dp))
                Spacer(Modifier.width(14.dp))
                Column(Modifier.weight(1f)) {
                    Text("Dung lượng thiết bị", color = NaviColors.Muted, fontSize = 12.sp)
                    Text(gb(space.first), fontWeight = FontWeight.Bold, fontSize = 25.sp,
                        color = MaterialTheme.colorScheme.onSurface)
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Đã dùng: " + gb(used), fontSize = 11.sp)
                    Text("Còn trống: " + gb(space.second), fontSize = 11.sp)
                }
            }
            Spacer(Modifier.height(12.dp))
            LinearProgressIndicator(progress = { fraction.coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth().height(12.dp).clip(RoundedCornerShape(10.dp)),
                color = NaviColors.Green, trackColor = NaviColors.LightGray)
            Spacer(Modifier.height(10.dp))
            Row(Modifier.fillMaxWidth().clip(RoundedCornerShape(18.dp))
                .background(MaterialTheme.colorScheme.secondaryContainer).padding(10.dp),
                horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Tổng dung lượng bản đồ ngoại tuyến", fontSize = 12.sp)
                Text(if (managerState.demoInstalled) "462 B (mô phỏng)" else "0 B", fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary, fontSize = 12.sp)
            }
        }
        SegmentedChoice(
            listOf("Tải theo tỉnh/thành", "Toàn Việt Nam"),
            if (allVietnam) "Toàn Việt Nam" else "Tải theo tỉnh/thành",
            { allVietnam = it == "Toàn Việt Nam" }, Modifier.fillMaxWidth()
        )
        NaviCard {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Box(
                    Modifier.width(112.dp).height(218.dp)
                        .clip(RoundedCornerShape(15.dp)).background(Color(0xFFF0F4F1)),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.Public, null, tint = NaviColors.Green,
                            modifier = Modifier.size(76.dp))
                        Text("Việt Nam", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                        Text("Sơ đồ minh họa", fontSize = 9.sp, color = NaviColors.Muted)
                    }
                }
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                    OutlinedTextField(
                        value = provinceQuery, onValueChange = { provinceQuery = it },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        shape = RoundedCornerShape(24.dp),
                        leadingIcon = { Icon(Icons.Default.Search, null,
                            modifier = Modifier.size(18.dp)) },
                        placeholder = { Text("Tìm tỉnh/thành...", fontSize = 12.sp) }
                    )
                    Text("☆  Khu vực gợi ý", color = MaterialTheme.colorScheme.primary,
                        fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    offlineSamples.filter {
                        provinceQuery.isBlank() || it.name.contains(provinceQuery, ignoreCase = true)
                    }.forEach { region ->
                        Surface(onClick = missingSource, shape = RoundedCornerShape(14.dp),
                            color = MaterialTheme.colorScheme.surface,
                            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                            Row(Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 9.dp),
                                verticalAlignment = Alignment.CenterVertically) {
                                Text(region.icon, color = NaviColors.Green, fontSize = 21.sp)
                                Spacer(Modifier.width(7.dp))
                                Column(Modifier.weight(1f)) {
                                    Text(region.name, fontSize = 12.sp, fontWeight = FontWeight.Bold,
                                        maxLines = 1)
                                    Text("Chưa có gói", fontSize = 10.sp, color = NaviColors.Muted)
                                }
                                Icon(Icons.Default.AddCircleOutline, "Thêm gói",
                                    tint = NaviColors.Green, modifier = Modifier.size(22.dp))
                            }
                        }
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(11.dp).clip(RoundedCornerShape(3.dp))
                    .background(NaviColors.Green))
                Spacer(Modifier.width(5.dp))
                Text("Đã tải (0)", fontSize = 11.sp)
                Spacer(Modifier.width(14.dp))
                Box(Modifier.size(11.dp).clip(RoundedCornerShape(3.dp))
                    .background(NaviColors.LightGray))
                Spacer(Modifier.width(5.dp))
                Text("Chưa tải", fontSize = 11.sp)
            }
            if (allVietnam) {
                Spacer(Modifier.height(12.dp))
                Button(onClick = missingSource, modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = NaviColors.Green)) {
                    Icon(Icons.Default.CloudDownload, null)
                    Spacer(Modifier.width(8.dp))
                    Text("Tải bộ dữ liệu toàn Việt Nam")
                }
            }
        }
        NaviCard {
            SectionHeading(Icons.Default.CloudDownload,
                if (managerState.downloading) "Đang tải (1)" else "Đang tải (0)")
            Spacer(Modifier.height(9.dp))
            Text(managerState.status, fontSize = 12.sp,
                color = MaterialTheme.colorScheme.onSurface)
            if (managerState.totalBytes > 0L) {
                Spacer(Modifier.height(7.dp))
                LinearProgressIndicator(
                    progress = { (managerState.bytesRead.toFloat() /
                        managerState.totalBytes.toFloat()).coerceIn(0f, 1f) },
                    modifier = Modifier.fillMaxWidth().height(8.dp),
                    color = NaviColors.Green
                )
                Text(managerState.bytesRead.toString() + "/" +
                    managerState.totalBytes.toString() + " byte",
                    fontSize = 11.sp, color = NaviColors.Muted)
            }
            if (managerState.error != null) {
                Text(managerState.error ?: "", fontSize = 11.sp,
                    color = MaterialTheme.colorScheme.error)
            }
            if (managerState.downloading || managerState.paused) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    if (managerState.downloading) {
                        OutlinedButton(onClick = { manager.pause() }) { Text("Tạm dừng") }
                    }
                    if (managerState.paused) {
                        Button(onClick = { manager.resume(preferences.cellularDownload) }) {
                            Text("Tiếp tục")
                        }
                    }
                    OutlinedButton(onClick = { manager.cancel() }) { Text("Hủy tải") }
                }
            }
            Spacer(Modifier.height(5.dp))
            Text("Chỉ tải từ nguồn PMTiles HTTPS được duyệt; có hỗ trợ Range/ETag và SHA-256.",
                fontSize = 11.sp, color = NaviColors.Muted)
            Text("Chưa cấu hình danh mục tải đường phố thực tế.",
                fontSize = 11.sp, color = MaterialTheme.colorScheme.error)
        }
        NaviCard {
            SectionHeading(Icons.Default.CheckCircleOutline,
                if (managerState.demoInstalled) "Đã tải (1 gói thử nghiệm)" else "Đã tải (0)",
                if (managerState.demoInstalled) "462 B" else "0 B")
            Spacer(Modifier.height(10.dp))
            Text("Gói PMTiles mô phỏng gồm 2 nét sơ đồ nhân tạo, không có đường phố, " +
                "giới hạn tốc độ hoặc vị trí biển báo thực địa.",
                fontSize = 12.sp, color = NaviColors.Muted)
            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                Button(onClick = { manager.installDemo() },
                    colors = ButtonDefaults.buttonColors(containerColor = NaviColors.Green),
                    modifier = Modifier.weight(1f)) {
                    Text(if (managerState.demoInstalled) "Xác minh lại" else "Cài bản thử",
                        fontSize = 12.sp, maxLines = 1)
                }
                if (managerState.demoInstalled) {
                    OutlinedButton(onClick = { manager.removeDemo() },
                        modifier = Modifier.weight(1f)) {
                        Text("Xóa gói", fontSize = 12.sp)
                    }
                }
            }
        }
        NaviCard {
            OfflineSettingRow(Icons.Default.Wifi, "Tự động cập nhật qua Wi-Fi",
                "Tự động kiểm tra khi có dữ liệu phát hành", preferences.wifiUpdate,
                preferences::updateWifiUpdate)
            SettingsDivider()
            OfflineSettingRow(Icons.Default.SignalCellularAlt, "Cho phép tải qua dữ liệu di động",
                "Dùng 4G/5G khi nguồn dữ liệu sẵn sàng", preferences.cellularDownload,
                preferences::updateCellularDownload)
        }
    }
}

@Composable
private fun OfflineSettingRow(icon: androidx.compose.ui.graphics.vector.ImageVector,
                              title: String, description: String,
                              checked: Boolean, onCheck: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(25.dp))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(title, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
            Text(description, color = NaviColors.Muted, fontSize = 11.sp)
        }
        NaviToggle(checked, onCheck)
    }
}
