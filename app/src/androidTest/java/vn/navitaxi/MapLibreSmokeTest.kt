package vn.navitaxi

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Native rendering smoke test: deliberately switch to a LOCAL empty style.
 * It does not assert that Internet tile infrastructure is always reachable.
 */
@RunWith(AndroidJUnit4::class)
class MapLibreSmokeTest {
    @get:Rule val ui = createAndroidComposeRule<MainActivity>()

    @Test fun mapViewCanOpenSwitchLocalStyleAndLeaveWithoutCrashing() {
        ui.onNodeWithText("Bản đồ").performClick()
        ui.onNodeWithText("BẢN THỬ").assertExists()
        ui.onNodeWithText("Chưa có dữ liệu").performClick()
        ui.onNodeWithText("Chưa tải gói bản đồ ngoại tuyến").assertExists()
        ui.onNodeWithContentDescription("Quay lại").performClick()
        ui.onNodeWithText("Tìm kiếm").assertExists()
    }
}
