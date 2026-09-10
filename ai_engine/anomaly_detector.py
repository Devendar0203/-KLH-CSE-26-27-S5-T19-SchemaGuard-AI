import numpy as np
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Tuple

class AnomalyDetector:
    def __init__(self, contamination: float = 0.1):
        self.contamination = contamination
        self.model = IsolationForest(n_estimators=50, contamination=self.contamination, random_state=42)
        self.history: List[List[float]] = []
        self._is_fitted = False

        # Seed with initial baseline metric history
        # Features: [record_count, error_rate, latency_ms, quarantine_rate]
        baseline = [
            [5.0, 0.0, 45.0, 0.0],
            [6.0, 0.0, 50.0, 0.0],
            [5.0, 0.0, 42.0, 0.0],
            [7.0, 0.0, 48.0, 0.0],
            [4.0, 0.0, 40.0, 0.0],
            [6.0, 0.0, 52.0, 0.0],
            [5.0, 0.0, 46.0, 0.0],
            [8.0, 0.0, 55.0, 0.0],
        ]
        self.train_baseline(baseline)

    def train_baseline(self, samples: List[List[float]]):
        self.history.extend(samples)
        X = np.array(self.history)
        self.model.fit(X)
        self._is_fitted = True

    def detect(self, record_count: float, error_rate: float, latency_ms: float, quarantine_rate: float) -> Dict[str, any]:
        sample = np.array([[record_count, error_rate, latency_ms, quarantine_rate]])
        
        if not self._is_fitted:
            self.model.fit(sample)
            self._is_fitted = True

        pred = self.model.predict(sample)[0] # -1 for anomaly, 1 for normal
        raw_score = float(self.model.score_samples(sample)[0]) # negative score, lower = more anomalous
        
        # Convert raw score to 0.0-1.0 anomaly index (higher = more anomalous)
        # Typical raw scores range from -0.8 (extreme) to -0.3 (normal)
        anomaly_index = max(0.0, min(1.0, (0.0 - raw_score) * 1.5 - 0.3))
        
        is_anomaly = pred == -1 or anomaly_index >= 0.65

        # Update history
        self.history.append([record_count, error_rate, latency_ms, quarantine_rate])
        if len(self.history) > 100:
            self.history.pop(0)

        return {
            "is_anomaly": bool(is_anomaly),
            "anomaly_score": round(anomaly_index, 4),
            "raw_score": round(raw_score, 4),
            "metrics": {
                "record_count": record_count,
                "error_rate": error_rate,
                "latency_ms": latency_ms,
                "quarantine_rate": quarantine_rate
            }
        }
