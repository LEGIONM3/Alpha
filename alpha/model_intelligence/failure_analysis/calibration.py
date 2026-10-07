"""Confidence Calibration Engine: Calibrates raw model confidence against empirical performance."""

from typing import List, Tuple, Dict, Any


class ConfidenceCalibrationEngine:
    """Measures Expected Calibration Error (ECE) and adjusts raw confidence scores."""

    def __init__(self):
        # Stores tuples of (confidence, is_correct)
        self._history: List[Tuple[float, bool]] = []

    def record_prediction(self, confidence: float, is_correct: bool):
        self._history.append((max(0.0, min(1.0, confidence)), bool(is_correct)))

    def calculate_expected_calibration_error(self, num_bins: int = 5) -> float:
        """Computes empirical ECE across historical confidence bins."""
        if not self._history:
            return 0.0

        bin_width = 1.0 / num_bins
        total_samples = len(self._history)
        ece = 0.0

        for i in range(num_bins):
            bin_lower = i * bin_width
            bin_upper = (i + 1) * bin_width
            # Filter samples in bin
            bin_samples = [
                (conf, corr) for conf, corr in self._history
                if (bin_lower <= conf < bin_upper) or (i == num_bins - 1 and conf == bin_upper)
            ]
            if not bin_samples:
                continue

            bin_size = len(bin_samples)
            avg_confidence = sum(conf for conf, _ in bin_samples) / bin_size
            avg_accuracy = sum(1.0 if corr else 0.0 for _, corr in bin_samples) / bin_size
            ece += (bin_size / total_samples) * abs(avg_accuracy - avg_confidence)

        return round(ece, 4)

    def calibrate(self, raw_confidence: float, domain_historical_accuracy: float = 0.75) -> float:
        """Shrinks overconfident ratings towards domain base accuracy (Platt scaling / temperature shrink)."""
        ece = self.calculate_expected_calibration_error()
        penalty = ece * 0.5

        # If raw confidence is high (e.g. 0.99) but base accuracy is lower (e.g. 0.70), shrink toward base
        calibrated = (raw_confidence * 0.6) + (domain_historical_accuracy * 0.4) - penalty
        return max(0.05, min(0.99, round(calibrated, 3)))
