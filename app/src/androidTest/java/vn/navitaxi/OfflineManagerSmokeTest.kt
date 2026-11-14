package vn.navitaxi

import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/** The local fixture is genuine 462-byte PMTiles but NOT a geographic basemap. */
@RunWith(AndroidJUnit4::class)
class OfflineManagerSmokeTest {
    @get:Rule val ui = createAndroidComposeRule<MainActivity>()

    @Test fun syntheticPackageCanInstallVerifyAndDeleteWithoutRealMapClaims() {
        ui.onNodeWithText("Ngoại tuyến").performClick()
        ui.onNodeWithText("Chưa cấu hình danh mục tải đường phố thực tế.")
            .performScrollTo().assertExists()
        val install = if (ui.onAllNodesWithText("Cài bản thử").fetchSemanticsNodes().isNotEmpty())
            "Cài bản thử" else "Xác minh lại"
        ui.onNodeWithText(install).performScrollTo().performClick()
        ui.waitUntil(15_000) {
            ui.onAllNodesWithText("Đã tải (1 gói thử nghiệm)")
                .fetchSemanticsNodes().isNotEmpty()
        }
        ui.onNodeWithText("Xóa gói").performScrollTo().performClick()
        ui.waitUntil(15_000) {
            ui.onAllNodesWithText("Đã tải (0)")
                .fetchSemanticsNodes().isNotEmpty()
        }
    }
}
