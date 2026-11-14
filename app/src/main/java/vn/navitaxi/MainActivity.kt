package vn.navitaxi

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognizerIntent
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.OfflinePin
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.launch
import java.util.Locale

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { NaviTaxiApp() }
    }
}

private enum class Screen(val label: String) {
    SEARCH("Tìm kiếm"), OFFLINE("Ngoại tuyến"), SETTINGS("Cài đặt")
}

@Composable
private fun NaviTaxiApp() {
    val context = LocalContext.current
    val preferences = remember { UiPreferences(context.getSharedPreferences("navitaxi_ui", Context.MODE_PRIVATE)) }
    var screen by rememberSaveable { mutableStateOf(Screen.SEARCH) }
    var query by rememberSaveable { mutableStateOf("") }
    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val notify: (String) -> Unit = { message -> scope.launch { snackbarHostState.showSnackbar(message) } }
    val launcher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
                ?.firstOrNull()?.takeIf(String::isNotBlank)?.let { query = it }
        }
    }

    MaterialTheme(colorScheme = if (preferences.isDark) darkNaviColorScheme() else lightNaviColorScheme()) {
        Scaffold(
            containerColor = MaterialTheme.colorScheme.background,
            snackbarHost = { SnackbarHost(snackbarHostState) },
            bottomBar = {
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface, tonalElevation = 5.dp) {
                    Screen.entries.forEach { target ->
                        val icon = when (target) {
                            Screen.SEARCH -> Icons.Default.Search
                            Screen.OFFLINE -> Icons.Default.OfflinePin
                            Screen.SETTINGS -> Icons.Default.Settings
                        }
                        NavigationBarItem(
                            selected = screen == target,
                            onClick = { screen = target },
                            icon = { Icon(icon, contentDescription = null) },
                            label = { Text(target.label) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = NaviColors.Green,
                                selectedTextColor = NaviColors.Green,
                                indicatorColor = MaterialTheme.colorScheme.secondaryContainer
                            )
                        )
                    }
                }
            }
        ) { insets ->
            Box(Modifier.fillMaxSize().padding(insets)) {
                when (screen) {
                    Screen.SEARCH -> SearchScreen(
                        query = query,
                        onQueryChange = { query = it },
                        onVoiceSearch = {
                            val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                                putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                                putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale("vi", "VN").toLanguageTag())
                                putExtra(RecognizerIntent.EXTRA_PROMPT, "Đọc địa chỉ hoặc địa điểm")
                            }
                            try { launcher.launch(intent) }
                            catch (_: ActivityNotFoundException) {
                                notify("Thiết bị chưa có dịch vụ nhận dạng giọng nói.")
                            }
                        },
                        onOpenMap = {
                            notify("MapLibre và bản đồ được triển khai ở Phase 2. Địa điểm đã được chọn.")
                        }
                    )
                    Screen.OFFLINE -> OfflineScreen(preferences, notify, onBack = { screen = Screen.SEARCH })
                    Screen.SETTINGS -> SettingsScreen(preferences, onBack = { screen = Screen.SEARCH })
                }
            }
        }
    }
}
