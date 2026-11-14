package vn.navitaxi

import android.content.SharedPreferences
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBackIosNew
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.StarOutline
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

object NaviColors {
    val Green = Color(0xFF008B72)
    val Deep = Color(0xFF064C48)
    val Dark = Color(0xFF0E2130)
    val Background = Color(0xFFF7F3EF)
    val Card = Color(0xFFFFFCFA)
    val PaleGreen = Color(0xFFE2F2EC)
    val Muted = Color(0xFF667078)
    val Golden = Color(0xFFDAB36B)
    val Stroke = Color(0xFFE5DEDA)
    val Danger = Color(0xFFB4413B)
    val LightGray = Color(0xFFDBDBDD)
    val TealBrush = Brush.horizontalGradient(listOf(Green, Deep))
}
fun lightNaviColorScheme() = lightColorScheme(
    primary = NaviColors.Green, onPrimary = Color.White,
    background = NaviColors.Background, surface = NaviColors.Card,
    secondaryContainer = NaviColors.PaleGreen, onSecondaryContainer = NaviColors.Deep,
    onSurface = NaviColors.Dark
)
fun darkNaviColorScheme() = darkColorScheme(
    primary = Color(0xFF56CBB5), onPrimary = NaviColors.Dark,
    background = Color(0xFF12191E), surface = Color(0xFF222A30),
    secondaryContainer = Color(0xFF12433D), onSecondaryContainer = Color.White,
    onSurface = Color.White
)

class UiPreferences(private val store: SharedPreferences) {
    var isDark by mutableStateOf(store.getBoolean("dark", false)); private set
    var volume by mutableFloatStateOf(store.getFloat("volume", .8f)); private set
    var voice by mutableStateOf(store.getString("voice", "Giọng nữ") ?: "Giọng nữ"); private set
    var mapTheme by mutableStateOf(store.getString("theme", "Thực tế") ?: "Thực tế"); private set
    var buildings3d by mutableStateOf(store.getBoolean("3d", true)); private set
    var traffic by mutableStateOf(store.getBoolean("traffic", true)); private set
    var gps by mutableStateOf(store.getString("gps", "Cân bằng") ?: "Cân bằng"); private set
    var speedAlerts by mutableStateOf(store.getBoolean("speed_alerts", true)); private set
    var laneGuidance by mutableStateOf(store.getBoolean("lane", true)); private set
    var poi by mutableStateOf(store.getBoolean("poi", true)); private set
    var density by mutableStateOf(store.getString("density", "Vừa") ?: "Vừa"); private set
    var wifiUpdate by mutableStateOf(store.getBoolean("wifi", true)); private set
    var cellularDownload by mutableStateOf(store.getBoolean("cellular", false)); private set

    fun setDark(value: Boolean) { isDark = value; store.edit().putBoolean("dark", value).apply() }
    fun setVolume(value: Float) { volume = value; store.edit().putFloat("volume", value).apply() }
    fun setVoice(value: String) { voice = value; store.edit().putString("voice", value).apply() }
    fun setMapTheme(value: String) { mapTheme = value; store.edit().putString("theme", value).apply() }
    fun setBuildings3d(value: Boolean) { buildings3d = value; store.edit().putBoolean("3d", value).apply() }
    fun setTraffic(value: Boolean) { traffic = value; store.edit().putBoolean("traffic", value).apply() }
    fun setGps(value: String) { gps = value; store.edit().putString("gps", value).apply() }
    fun setSpeedAlerts(value: Boolean) { speedAlerts = value; store.edit().putBoolean("speed_alerts", value).apply() }
    fun setLaneGuidance(value: Boolean) { laneGuidance = value; store.edit().putBoolean("lane", value).apply() }
    fun setPoi(value: Boolean) { poi = value; store.edit().putBoolean("poi", value).apply() }
    fun setDensity(value: String) { density = value; store.edit().putString("density", value).apply() }
    fun setWifiUpdate(value: Boolean) { wifiUpdate = value; store.edit().putBoolean("wifi", value).apply() }
    fun setCellularDownload(value: Boolean) { cellularDownload = value; store.edit().putBoolean("cellular", value).apply() }
}

@Composable
fun BrandHeader() {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 17.dp, horizontal = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(48.dp).clip(RoundedCornerShape(14.dp)).background(MaterialTheme.colorScheme.secondaryContainer),
                contentAlignment = Alignment.Center) {
                Icon(Icons.Default.DirectionsCar, null, tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(35.dp))
                Text("TAXI", fontSize = 8.sp, color = NaviColors.Green,
                    fontWeight = FontWeight.Bold, modifier = Modifier.align(Alignment.TopCenter))
            }
            Spacer(Modifier.width(9.dp))
            Text("NaviTaxi", fontSize = 28.sp, fontWeight = FontWeight.Black,
                fontStyle = FontStyle.Italic, color = MaterialTheme.colorScheme.onSurface)
            Text("Map", fontSize = 28.sp, fontWeight = FontWeight.Black,
                fontStyle = FontStyle.Italic, color = MaterialTheme.colorScheme.primary)
        }
        Text("⌁", fontSize = 32.sp, color = NaviColors.Golden)
    }
}

@Composable
fun PageHeading(title: String, subtitle: String? = null, onBack: () -> Unit) {
    Column {
        Row(verticalAlignment = Alignment.CenterVertically) {
            SmallIconButton(Icons.Default.ArrowBackIosNew, onBack)
            Spacer(Modifier.width(15.dp))
            Text(title, fontSize = 28.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        }
        if (subtitle != null) {
            Text(subtitle, color = NaviColors.Muted, fontSize = 12.sp,
                modifier = Modifier.padding(start = 67.dp))
        }
    }
}

@Composable
fun SmallIconButton(icon: ImageVector, onClick: () -> Unit) {
    Surface(
        onClick = onClick, shape = RoundedCornerShape(16.dp), color = MaterialTheme.colorScheme.surface,
        shadowElevation = 3.dp, modifier = Modifier.size(46.dp)
    ) { Box(contentAlignment = Alignment.Center) {
        Icon(icon, null, modifier = Modifier.size(23.dp), tint = MaterialTheme.colorScheme.primary)
    } }
}

@Composable
fun NaviCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Surface(modifier = modifier.fillMaxWidth(), color = MaterialTheme.colorScheme.surface,
        shadowElevation = 2.dp, shape = RoundedCornerShape(22.dp)) {
        Column(Modifier.padding(14.dp), content = content)
    }
}

@Composable
fun SectionHeading(icon: ImageVector, title: String, tail: String? = null) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Icon(icon, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(26.dp))
        Spacer(Modifier.width(10.dp))
        Text(title, color = MaterialTheme.colorScheme.onSurface, fontSize = 19.sp,
            fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
        if (tail != null) Text(tail, color = NaviColors.Green, fontSize = 12.sp)
    }
}

@Composable
fun SettingsSectionHeading(icon: ImageVector, title: String) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(38.dp).background(MaterialTheme.colorScheme.secondaryContainer, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center) {
            Icon(icon, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(22.dp))
        }
        Spacer(Modifier.width(12.dp))
        Text(title, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
    }
}

@Composable
fun SegmentedChoice(options: List<String>, selected: String,
                    onSelected: (String) -> Unit, modifier: Modifier = Modifier) {
    Row(modifier.clip(RoundedCornerShape(26.dp)).background(Color(0xFFF0EEEC))
        .padding(3.dp), horizontalArrangement = Arrangement.spacedBy(2.dp)) {
        options.forEach { label ->
            val active = label == selected
            Box(
                Modifier.weight(1f).clip(RoundedCornerShape(23.dp))
                    .then(if (active) Modifier.background(NaviColors.TealBrush)
                        else Modifier.background(Color.Transparent))
                    .clickable { onSelected(label) }.padding(vertical = 12.dp, horizontal = 4.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(label, fontSize = 13.sp,
                    fontWeight = if (active) FontWeight.Bold else FontWeight.Medium,
                    color = if (active) Color.White else MaterialTheme.colorScheme.onSurface, maxLines = 1)
            }
        }
    }
}

@Composable
fun NaviToggle(checked: Boolean, onChange: (Boolean) -> Unit) {
    Switch(
        checked = checked,
        onCheckedChange = onChange,
        colors = SwitchDefaults.colors(checkedThumbColor = Color.White,
            checkedTrackColor = NaviColors.Green, uncheckedThumbColor = Color.White)
    )
}

@Composable
fun SettingsDivider() {
    HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant, modifier = Modifier.padding(vertical = 4.dp))
}
