package vn.navitaxi

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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.Normalizer
import java.util.Locale

private data class PlaceItem(val id: String, val name: String,
                             val address: String, val type: String, val icon: ImageVector)

private val places = listOf(
    PlaceItem("lake", "Hồ Hoàn Kiếm", "P. Hàng Trống, Q. Hoàn Kiếm, Hà Nội", "Địa điểm", Icons.Default.Place),
    PlaceItem("opera", "Nhà hát Lớn Hà Nội", "Số 1 Tràng Tiền, P. Tràng Tiền, Q. Hoàn Kiếm, Hà Nội", "Địa điểm", Icons.Default.Place),
    PlaceItem("temple", "Văn Miếu – Quốc Tử Giám", "Số 58 Quốc Tử Giám, P. Văn Miếu, Q. Đống Đa, Hà Nội", "Địa điểm", Icons.Default.Place),
    PlaceItem("hospital", "Bệnh viện Việt Đức", "Số 40 Tràng Thi, P. Hàng Bông, Q. Hoàn Kiếm, Hà Nội", "POI", Icons.Default.LocalHospital),
    PlaceItem("hangbai", "Phố Hàng Bài", "P. Hàng Bài, Q. Hoàn Kiếm, Hà Nội", "Địa chỉ", Icons.Default.Place),
    PlaceItem("airport", "Sân bay Nội Bài", "Sóc Sơn, Hà Nội", "POI", Icons.Default.Flight),
    PlaceItem("station", "Ga Hà Nội", "120 Lê Duẩn, Hà Nội", "POI", Icons.Default.Train),
    PlaceItem("bus", "Bến xe Mỹ Đình", "20 Phạm Hùng, Hà Nội", "POI", Icons.Default.DirectionsBus)
)
private fun simplify(text: String): String =
    Normalizer.normalize(text.lowercase(Locale.ROOT).replace('đ', 'd'), Normalizer.Form.NFD)
        .replace(Regex("\\p{M}+"), "")

@Composable
fun SearchScreen(query: String, onQueryChange: (String) -> Unit,
                 onVoiceSearch: () -> Unit, onOpenMap: (String) -> Unit) {
    var tab by rememberSaveable { mutableStateOf("Địa chỉ") }
    var selectedId by rememberSaveable { mutableStateOf("lake") }
    var starred by rememberSaveable { mutableStateOf(false) }
    var category by rememberSaveable { mutableStateOf("") }
    val results = remember(query, tab, category) {
        places.filter { p ->
            val matchesText = query.isBlank() || simplify(p.name + p.address).contains(simplify(query))
            val matchesTab = tab == "Địa chỉ" || p.type == tab
            val matchesCategory = when (category) {
                "Sân bay" -> p.id == "airport"
                "Bến xe" -> p.id == "bus"
                "Bệnh viện" -> p.id == "hospital"
                "Khách sạn", "Nhà hàng", "ATM" -> false
                else -> true
            }
            matchesText && matchesTab && matchesCategory
        }
    }
    val selected = places.firstOrNull { it.id == selectedId } ?: places.first()
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState())
        .padding(horizontal = 14.dp).padding(bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)) {
        BrandHeader()
        OutlinedTextField(
            value = query, onValueChange = { onQueryChange(it); category = "" },
            modifier = Modifier.fillMaxWidth(), singleLine = true,
            shape = RoundedCornerShape(34.dp),
            placeholder = { Text("Tìm địa chỉ, địa điểm, POI hoặc điểm đón/trả...", fontSize = 13.sp) },
            leadingIcon = { Icon(Icons.Default.Search, null, tint = MaterialTheme.colorScheme.onSurface) },
            trailingIcon = {
                IconButton(onClick = onVoiceSearch) {
                    Icon(Icons.Default.Mic, "Tìm kiếm bằng giọng nói", tint = MaterialTheme.colorScheme.onSurface)
                }
            },
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedBorderColor = MaterialTheme.colorScheme.outlineVariant,
                focusedBorderColor = NaviColors.Green
            )
        )
        Row(verticalAlignment = Alignment.Top) {
            Icon(Icons.Default.Info, null, tint = NaviColors.Muted, modifier = Modifier.size(17.dp))
            Spacer(Modifier.width(5.dp))
            Text("Có thể tìm có hoặc không dấu (ví dụ: “Hoan Kiem” hoặc “Hoàn Kiếm”)",
                color = NaviColors.Muted, fontSize = 11.sp)
        }
        SegmentedChoice(listOf("Địa chỉ", "Địa điểm", "POI"), tab,
            { tab = it; category = "" }, Modifier.fillMaxWidth())
        NaviCard {
            val categories = listOf(
                Triple("Sân bay", Icons.Default.Flight, "Sân bay"),
                Triple("Bến xe", Icons.Default.DirectionsBus, "Bến xe"),
                Triple("Khách sạn", Icons.Default.Hotel, "Khách sạn"),
                Triple("Nhà hàng", Icons.Default.Restaurant, "Nhà hàng"),
                Triple("Bệnh viện", Icons.Default.LocalHospital, "Bệnh viện"),
                Triple("ATM", Icons.Default.LocalAtm, "ATM")
            )
            Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                categories.forEach { (label, icon, filter) ->
                    Column(Modifier.weight(1f).clip(RoundedCornerShape(13.dp))
                        .background(if (category == filter) MaterialTheme.colorScheme.secondaryContainer else Color(0xFFF9F7F5))
                        .clickable { category = if (category == filter) "" else filter }
                        .padding(vertical = 12.dp, horizontal = 1.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                        horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(icon, null, tint = NaviColors.Green, modifier = Modifier.size(23.dp))
                        Text(label, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface,
                            maxLines = 1, softWrap = false)
                    }
                }
            }
        }
        NaviCard {
            SectionHeading(Icons.Default.History, "Tìm gần đây", "Xem tất cả")
            Spacer(Modifier.height(7.dp))
            listOf("opera", "temple", "hospital").forEachIndexed { index, id ->
                val item = places.first { it.id == id }
                SearchPlaceRow(item, onClick = { selectedId = id })
                if (index < 2) SettingsDivider()
            }
        }
        NaviCard {
            SectionHeading(Icons.Default.StarOutline, "Gợi ý cho tài xế")
            Spacer(Modifier.height(12.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()),
                horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                listOf("lake", "airport", "station", "bus").forEach { id ->
                    val item = places.first { it.id == id }
                    Surface(
                        onClick = { selectedId = id; onQueryChange(item.name); category = "" },
                        shape = RoundedCornerShape(28.dp), color = MaterialTheme.colorScheme.surface,
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant), shadowElevation = 1.dp
                    ) {
                        Row(Modifier.padding(horizontal = 11.dp, vertical = 9.dp),
                            verticalAlignment = Alignment.CenterVertically) {
                            Icon(item.icon, null, tint = NaviColors.Green, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(7.dp))
                            Text(item.name.replace("Sân bay ", ""), fontSize = 12.sp, maxLines = 1)
                        }
                    }
                }
            }
        }
        NaviCard {
            SectionHeading(Icons.Default.Search, "Kết quả tìm kiếm",
                results.size.toString() + " kết quả")
            Spacer(Modifier.height(10.dp))
            if (results.isEmpty()) {
                Text("Chưa có kết quả trong dữ liệu mẫu ngoại tuyến. Dữ liệu đầy đủ thuộc Phase 9.",
                    fontSize = 12.sp, color = NaviColors.Muted, modifier = Modifier.padding(10.dp))
            } else {
                results.take(5).forEach { item ->
                    Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(15.dp))
                        .background(if (item.id == selectedId) MaterialTheme.colorScheme.secondaryContainer else Color.Transparent)
                        .padding(8.dp)) {
                        SearchPlaceRow(item, compact = true, onClick = { selectedId = item.id })
                    }
                }
            }
        }
        NaviCard {
            Row(verticalAlignment = Alignment.Top) {
                Box(Modifier.size(width = 112.dp, height = 124.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(Brush.linearGradient(listOf(
                        Color(0xFF6DB19B), Color(0xFFB7D4BF), Color(0xFF499D9F)))),
                    contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.Place, null, tint = Color.White, modifier = Modifier.size(37.dp))
                        Text("Ảnh minh họa", fontSize = 9.sp, color = Color.White)
                    }
                }
                Spacer(Modifier.width(12.dp))
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Row {
                        Text(selected.name, modifier = Modifier.weight(1f),
                            fontWeight = FontWeight.Bold, fontSize = 17.sp,
                            color = MaterialTheme.colorScheme.onSurface, maxLines = 2)
                        IconButton(onClick = { starred = !starred }, modifier = Modifier.size(28.dp)) {
                            Icon(if (starred) Icons.Default.Star else Icons.Default.StarBorder,
                                "Yêu thích", tint = if (starred) NaviColors.Golden else NaviColors.Muted)
                        }
                    }
                    Text(selected.address, fontSize = 11.sp, color = NaviColors.Muted,
                        maxLines = 2, overflow = TextOverflow.Ellipsis)
                    Text("Khoảng cách: chờ vị trí GPS", fontSize = 10.sp, color = MaterialTheme.colorScheme.primary)
                    Button(onClick = { onOpenMap(selected.name) }, modifier = Modifier.fillMaxWidth(),
                        contentPadding = PaddingValues(horizontal = 7.dp, vertical = 7.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = NaviColors.Green)) {
                        Icon(Icons.Default.Navigation, null, modifier = Modifier.size(17.dp))
                        Spacer(Modifier.width(4.dp))
                        Text("Xem trên bản đồ", fontSize = 11.sp, maxLines = 1)
                    }
                }
            }
        }
    }
}

@Composable
private fun SearchPlaceRow(item: PlaceItem, compact: Boolean = false, onClick: () -> Unit) {
    Row(Modifier.fillMaxWidth().clickable(onClick = onClick)
        .padding(vertical = if (compact) 3.dp else 5.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(38.dp).clip(RoundedCornerShape(10.dp))
            .background(Color(0xFFF0F3EF)), contentAlignment = Alignment.Center) {
            Icon(item.icon, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(22.dp))
        }
        Spacer(Modifier.width(10.dp))
        Column(Modifier.weight(1f)) {
            Text(item.name, fontWeight = FontWeight.Bold, fontSize = 14.sp,
                color = MaterialTheme.colorScheme.onSurface, maxLines = 1)
            Text(item.address, fontSize = 11.sp, color = NaviColors.Muted,
                maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        if (!compact) Icon(Icons.Default.ChevronRight, null, tint = NaviColors.Muted)
    }
}
