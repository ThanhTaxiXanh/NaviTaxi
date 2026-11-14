package vn.navitaxi

import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun SettingsScreen(preferences: UiPreferences, onBack: () -> Unit) {
    var showVoiceMenu by remember { mutableStateOf(false) }
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())
        .padding(horizontal = 14.dp).padding(bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(13.dp)) {
        BrandHeader()
        PageHeading("Cài đặt", onBack = onBack)
        NaviCard {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.weight(1f)) {
                    SettingsSectionHeading(Icons.Default.Palette, "Giao diện")
                }
                SegmentedChoice(listOf("Sáng", "Tối"),
                    if (preferences.isDark) "Tối" else "Sáng",
                    { preferences.updateDark(it == "Tối") }, Modifier.width(182.dp))
            }
        }
        NaviCard {
            SettingsSectionHeading(Icons.Default.VolumeUp, "Âm thanh")
            Spacer(Modifier.height(14.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.VolumeUp, null, tint = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.width(10.dp))
                Text("Âm lượng dẫn đường", fontSize = 13.sp,
                    modifier = Modifier.weight(1f))
                Text((preferences.volume * 100).toInt().toString() + "%",
                    fontSize = 13.sp, fontWeight = FontWeight.Bold)
            }
            Slider(
                value = preferences.volume, onValueChange = preferences::updateVolume,
                valueRange = 0f..1f, colors = SliderDefaults.colors(
                    thumbColor = Color.White, activeTrackColor = NaviColors.Green))
            SettingsDivider()
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Mic, null, tint = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.width(10.dp))
                Text("Giọng đọc dẫn đường", fontSize = 13.sp, modifier = Modifier.weight(1f))
                Box {
                    OutlinedButton(onClick = { showVoiceMenu = true },
                        contentPadding = PaddingValues(horizontal = 10.dp, vertical = 5.dp)) {
                        Text(preferences.voice, fontSize = 11.sp, color = MaterialTheme.colorScheme.primary)
                        Icon(Icons.Default.KeyboardArrowDown, null, tint = MaterialTheme.colorScheme.primary)
                    }
                    DropdownMenu(expanded = showVoiceMenu,
                        onDismissRequest = { showVoiceMenu = false }) {
                        listOf("Giọng nữ", "Giọng nam").forEach { label ->
                            DropdownMenuItem(text = { Text(label) }, onClick = {
                                preferences.updateVoice(label); showVoiceMenu = false
                            })
                        }
                    }
                }
            }
            Text("Lựa chọn sẽ được dùng khi hệ thống dẫn đường bằng giọng nói được tích hợp.",
                fontSize = 10.sp, color = NaviColors.Muted)
        }
        NaviCard {
            SettingsSectionHeading(Icons.Default.Layers, "Bản đồ")
            Spacer(Modifier.height(14.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Map, null, tint = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.width(8.dp))
                Text("Chủ đề bản đồ", fontSize = 13.sp, modifier = Modifier.weight(1f))
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                listOf("Thực tế", "Đơn giản", "Ban đêm").forEach { style ->
                    val chosen = preferences.mapTheme == style
                    Column(Modifier.weight(1f).clickable { preferences.updateMapTheme(style) },
                        horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(Modifier.fillMaxWidth().height(75.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(
                                when (style) {
                                    "Thực tế" -> Color(0xFFB2D0A5)
                                    "Đơn giản" -> Color(0xFFE4E9E6)
                                    else -> Color(0xFF162A3F)
                                })
                            .border(if (chosen) 3.dp else 1.dp,
                                if (chosen) NaviColors.Green else MaterialTheme.colorScheme.outlineVariant,
                                RoundedCornerShape(12.dp)),
                            contentAlignment = Alignment.Center) {
                            Icon(Icons.Default.Map, null,
                                tint = if (style == "Ban đêm") Color(0xFF63C2E8)
                                    else NaviColors.Green, modifier = Modifier.size(33.dp))
                            if (chosen) {
                                Icon(Icons.Default.CheckCircle, null, tint = NaviColors.Green,
                                    modifier = Modifier.align(Alignment.TopEnd).size(21.dp))
                            }
                        }
                        Spacer(Modifier.height(5.dp))
                        Text(style, fontSize = 11.sp)
                    }
                }
            }
            Spacer(Modifier.height(10.dp))
            SettingsDivider()
            ToggleSettingsRow(Icons.Default.Apartment, "Tòa nhà 3D",
                preferences.buildings3d, preferences::updateBuildings3d)
            SettingsDivider()
            ToggleSettingsRow(Icons.Default.Traffic, "Lớp giao thông",
                preferences.traffic, preferences::updateTraffic)
        }
        NaviCard {
            SettingsSectionHeading(Icons.Default.GpsFixed, "GPS")
            Spacer(Modifier.height(10.dp))
            SegmentedChoice(listOf("Tiết kiệm", "Cân bằng", "Cao"), preferences.gps,
                preferences::updateGps, Modifier.fillMaxWidth())
        }
        NaviCard {
            SettingsSectionHeading(Icons.Default.Navigation, "Dẫn đường")
            Spacer(Modifier.height(8.dp))
            ToggleSettingsRow(Icons.Default.Speed, "Cảnh báo giới hạn tốc độ",
                preferences.speedAlerts, preferences::updateSpeedAlerts)
            SettingsDivider()
            ToggleSettingsRow(Icons.Default.AltRoute, "Chỉ dẫn làn đường",
                preferences.laneGuidance, preferences::updateLaneGuidance)
            Text("Cảnh báo chỉ kích hoạt khi có dữ liệu biển báo và giới hạn tốc độ đã xác minh.",
                color = NaviColors.Muted, fontSize = 10.sp,
                modifier = Modifier.padding(top = 6.dp))
        }
        NaviCard {
            SettingsSectionHeading(Icons.Default.Visibility, "Tùy chỉnh hiển thị")
            Spacer(Modifier.height(10.dp))
            ToggleSettingsRow(Icons.Default.Place, "Hiển thị điểm quan tâm (POI)",
                preferences.poi, preferences::updatePoi)
            Text("Cây xăng, bãi đỗ xe, bệnh viện, ATM, ...",
                modifier = Modifier.padding(start = 32.dp),
                color = NaviColors.Muted, fontSize = 10.sp)
            SettingsDivider()
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Layers, null, tint = MaterialTheme.colorScheme.primary)
                Spacer(Modifier.width(10.dp))
                Text("Mật độ hiển thị", fontSize = 13.sp, modifier = Modifier.weight(1f))
            }
            Spacer(Modifier.height(9.dp))
            SegmentedChoice(listOf("Thấp", "Vừa", "Cao"), preferences.density,
                preferences::updateDensity, Modifier.fillMaxWidth())
        }
    }
}

@Composable
private fun ToggleSettingsRow(icon: ImageVector, title: String, checked: Boolean,
                              onCheck: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(23.dp))
        Spacer(Modifier.width(10.dp))
        Text(title, fontSize = 13.sp, modifier = Modifier.weight(1f))
        NaviToggle(checked, onCheck)
    }
}
