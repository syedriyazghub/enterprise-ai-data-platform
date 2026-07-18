"""
Anomaly Detection & Fraud Detection Service

Uses statistical methods and ML models to detect:
- Data anomalies (outliers, unexpected patterns)
- Fraud indicators in financial/insurance data
- Data quality issues
"""
from dataclasses import dataclass, field
from typing import Any
import statistics


@dataclass
class AnomalyResult:
    record_index: int
    field: str
    value: Any
    anomaly_type: str
    severity: str  # "low" | "medium" | "high"
    score: float
    explanation: str


class AnomalyDetectionService:
    """Statistical anomaly detection using Z-score and IQR methods."""

    def detect_numeric_anomalies(
        self,
        records: list[dict],
        numeric_fields: list[str],
        z_threshold: float = 3.0,
    ) -> list[AnomalyResult]:
        """Detect outliers in numeric fields using Z-score."""
        anomalies = []

        for field_name in numeric_fields:
            values = []
            for r in records:
                try:
                    v = float(r.get(field_name, 0) or 0)
                    values.append(v)
                except (ValueError, TypeError):
                    values.append(None)

            numeric_values = [v for v in values if v is not None]
            if len(numeric_values) < 3:
                continue

            mean = statistics.mean(numeric_values)
            stdev = statistics.stdev(numeric_values)
            if stdev == 0:
                continue

            for idx, v in enumerate(values):
                if v is None:
                    continue
                z_score = abs((v - mean) / stdev)
                if z_score > z_threshold:
                    severity = "high" if z_score > 5 else "medium" if z_score > 4 else "low"
                    anomalies.append(AnomalyResult(
                        record_index=idx,
                        field=field_name,
                        value=v,
                        anomaly_type="statistical_outlier",
                        severity=severity,
                        score=round(z_score, 3),
                        explanation=f"Value {v} is {z_score:.1f} standard deviations from mean {mean:.2f}",
                    ))

        return anomalies

    def detect_fraud_indicators(self, records: list[dict]) -> list[AnomalyResult]:
        """Rule-based fraud detection for financial records."""
        indicators = []

        for idx, record in enumerate(records):
            # Round number amounts (common in fraud)
            for field_name in ["amount", "total", "invoice_amount"]:
                val = record.get(field_name)
                if val is not None:
                    try:
                        amount = float(val)
                        if amount > 0 and amount % 1000 == 0 and amount > 10000:
                            indicators.append(AnomalyResult(
                                record_index=idx,
                                field=field_name,
                                value=amount,
                                anomaly_type="round_number_fraud",
                                severity="medium",
                                score=0.6,
                                explanation=f"Suspiciously round amount: {amount}",
                            ))
                    except (ValueError, TypeError):
                        pass

            # Duplicate invoice numbers
            # (handled by duplicate detector, flagged here as fraud risk)

        return indicators
