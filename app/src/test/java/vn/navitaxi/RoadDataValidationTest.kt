package vn.navitaxi

import org.junit.Assert.*
import org.junit.Test

class RoadDataValidationTest {
    @Test fun wgs84RejectsOutOfRangeAndNonFinitePoints() {
        assertTrue(RoadDataValidation.validWgs84(21.0, 105.0))
        assertFalse(RoadDataValidation.validWgs84(91.0, 105.0))
        assertFalse(RoadDataValidation.validWgs84(21.0, 181.0))
        assertFalse(RoadDataValidation.validWgs84(Double.NaN, 105.0))
        assertFalse(RoadDataValidation.validWgs84(21.0, Double.POSITIVE_INFINITY))
    }
    @Test fun speedRequiresPositiveBoundedValueAndNonEmptySource() {
        assertTrue(RoadDataValidation.validSpeed(50, "synthetic-test-only"))
        assertFalse(RoadDataValidation.validSpeed(0, "synthetic-test-only"))
        assertFalse(RoadDataValidation.validSpeed(251, "synthetic-test-only"))
        assertFalse(RoadDataValidation.validSpeed(50, ""))
        assertFalse(RoadDataValidation.validSpeed(50, null))
    }
}
