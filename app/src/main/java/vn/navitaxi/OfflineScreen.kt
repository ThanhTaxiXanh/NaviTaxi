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
    var allVietnam by rememberSaveable { mutableStateOf(false) }
    var provinceQuery by rememberSaveable { mutableStateOf("") }
    val space = remember {
        val stat = StatFs(Environment.getDataDirectory().absolutePath)
        Pair(stat.totalBytes, stat.availableBytes)
    }
    val used = (space.first - space.second).coerceAtLeast(0L)
    val fraction = if (space.first <= 0L) 0f else used.toFloat() / space.first.toFloat()
    val missingSource: () -> Unit = {
        notify("Chưa có máy chủ hoặc bộ PMTiles có nguồn hợp lệ. Tải bản đồ sẽ được tích hợp ở Phase 3–5.")
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
                        color = NaviColors.Dark)
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
                .background(NaviColors.PaleGreen).padding(10.dp),
                horizontalArrangement = Arrangement.SpaceBetween) {
                Text("Tổng dung lượng bản đồ ngoại tuyến", fontSize = 12.sp)
                Text("0 GB", fontWeight = FontWeight.Bold,
                    color = NaviColors.Deep, fontSize = 12.sp)
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
                        Text("Việt Nam", fontWeight = FontWeight.Bold, color = NaviColors.Deep)
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
                    Text("☆  Khu vực gợi ý", color = NaviColors.Deep,
                        fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    offlineSamples.filter {
                        provinceQuery.isBlank() || it.name.contains(provinceQuery, ignoreCase = true)
                    }.forEach { region ->
                        Surface(onClick = missingSource, shape = RoundedCornerShape(14.dp),
                            color = NaviColors.Card,
                            border = BorderStroke(1.dp, NaviColors.Stroke)) {
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
            SectionHeading(Icons.Default.CloudDownload, "Đang tải (0)", "Tạm dừng tất cả")
            Spacer(Modifier.height(10.dp))
            Text("Chưa có tiến trình tải. Dữ liệu PMTiles chưa được kết nối.",
                fontSize = 12.sp, color = NaviColors.Muted)
        }
        NaviCard {
            SectionHeading(Icons.Default.CheckCircleOutline, "Đã tải (0)", "Tổng: 0 GB")
            Spacer(Modifier.height(10.dp))
            Text("Chưa có bản đồ ngoại tuyến được xác thực trên thiết bị.",
                fontSize = 12.sp, color = NaviColors.Muted)
        }
        NaviCard {
            OfflineSettingRow(Icons.Default.Wifi, "Tự động cập nhật qua Wi-Fi",
                "Tự động kiểm tra khi có dữ liệu phát hành", preferences.wifiUpdate,
                preferences::setWifiUpdate)
            SettingsDivider()
            OfflineSettingRow(Icons.Default.SignalCellularAlt, "Cho phép tải qua dữ liệu di động",
                "Dùng 4G/5G khi nguồn dữ liệu sẵn sàng", preferences.cellularDownload,
                preferences::setCellularDownload)
        }
    }
}

@Composable
private fun OfflineSettingRow(icon: androidx.compose.ui.graphics.vector.ImageVector,
                              title: String, description: String,
                              checked: Boolean, onCheck: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, null, tint = NaviColors.Deep, modifier = Modifier.size(25.dp))
        Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) {
            Text(title, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
            Text(description, color = NaviColors.Muted, fontSize = 11.sp)
        }
        NaviToggle(checked, onCheck)
    }
}
