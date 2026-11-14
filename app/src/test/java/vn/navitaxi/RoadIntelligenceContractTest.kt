package vn.navitaxi

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class RoadIntelligenceContractTest {
    @Test fun unknownSpeedDoesNotInventLegalLimit() {
        val observation: SpeedLimitObservation = SpeedLimitObservation.Unknown
        assertTrue(observation is SpeedLimitObservation.Unknown)
    }

    @Test fun verifiedSpeedRequiresProvenanceAndBounds() {
        val observation = SpeedLimitObservation.Verified(50, "synthetic-test-only", null, "both")
        assertEquals(50, observation.kmh)
        assertThrows(IllegalArgumentException::class.java) {
            SpeedLimitObservation.Verified(0, "synthetic-test-only", null, "both")
        }
        assertThrows(IllegalArgumentException::class.java) {
            SpeedLimitObservation.Verified(50, "", null, "both")
        }
    }

    @Test fun trafficSignMustHaveValidWgs84AndSource() {
        val synthetic = TrafficSignObservation("test", "test", 0.0, 0.0, "synthetic-test-only", null)
        assertEquals(0.0, synthetic.latitude, 0.0)
        assertThrows(IllegalArgumentException::class.java) {
            TrafficSignObservation("bad", "test", 91.0, 0.0, "synthetic-test-only", null)
        }
        assertThrows(IllegalArgumentException::class.java) {
            TrafficSignObservation("bad", "test", 0.0, 0.0, "", null)
        }
    }
}
