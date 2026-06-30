"""
AI-Based Fraud Detector
Isolation Forest (unsupervised ML) + Behavioral Scoring Layer
Same architectural approach as NPCI's fraud monitoring solution.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class AIFraudDetector:

    def __init__(self, contamination=0.08):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=200,
            max_samples="auto",
            random_state=42,
            n_jobs=-1
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.results = []
        self.stats = {
            "true_positives":  0,
            "false_positives": 0,
            "true_negatives":  0,
            "false_negatives": 0,
        }

    def _extract_features(self, transactions: list) -> np.ndarray:
        features = []
        for txn in transactions:
            features.append([
                txn["amount"],
                txn["amount_vs_avg_ratio"],
                txn["hour_of_day"],
                txn["txn_velocity_1h"],
                int(txn["is_new_merchant"]),
                int(txn["is_new_city"]),
                txn["day_of_week"],
                txn["account_age_days"],
            ])
        return np.array(features)

    def train(self, transactions: list):
        # Unsupervised — no fraud labels needed
        X = self._extract_features(transactions)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_trained = True

    def _behavioral_risk_score(self, txn: dict) -> tuple[float, list]:
        risk = 0.0
        signals = []

        ratio = txn["amount_vs_avg_ratio"]
        if ratio > 10:
            risk += 35; signals.append(f"Amount is {ratio:.1f}x customer avg (extreme)")
        elif ratio > 5:
            risk += 25; signals.append(f"Amount is {ratio:.1f}x customer avg (high)")
        elif ratio > 3:
            risk += 10; signals.append(f"Amount is {ratio:.1f}x customer avg (moderate)")

        vel = txn["txn_velocity_1h"]
        if vel > 10:
            risk += 30; signals.append(f"Velocity: {vel} txns/hr (mule pattern)")
        elif vel > 5:
            risk += 15; signals.append(f"Velocity: {vel} txns/hr (elevated)")

        hour = txn["hour_of_day"]
        if hour in range(0, 4):
            risk += 20; signals.append(f"Transaction at {hour}:00 (deep night)")
        elif hour in [4, 5, 23]:
            risk += 8;  signals.append(f"Transaction at {hour}:00 (late/early)")

        if txn["is_new_city"]:
            risk += 15; signals.append("New city — outside customer home location")

        if txn["is_new_merchant"] and txn["amount"] > 10000:
            risk += 20; signals.append("Large amount at new/unknown merchant")
        elif txn["is_new_merchant"]:
            risk += 5;  signals.append("First transaction at this merchant")

        if txn["account_age_days"] < 30:
            risk += 15; signals.append("New account (<30 days)")
        elif txn["account_age_days"] < 90:
            risk += 5;  signals.append("Relatively new account (<90 days)")

        if txn["amount"] > 75000:
            risk += 10; signals.append(f"High absolute amount: ₹{txn['amount']:,.0f}")

        return min(risk, 100.0), signals

    def predict(self, txn: dict) -> dict:
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction.")

        X = self._extract_features([txn])
        X_scaled = self.scaler.transform(X)

        anomaly_score = self.model.score_samples(X_scaled)[0]
        ml_risk = max(0, min(100, (-anomaly_score + 0.3) * 200))

        behavioral_risk, risk_signals = self._behavioral_risk_score(txn)

        # Behavioral scoring weighted more heavily (30/70 split)
        combined_risk = (ml_risk * 0.3) + (behavioral_risk * 0.7)
        is_flagged = combined_risk > 40

        actual_fraud = txn["is_fraud"]
        if is_flagged and actual_fraud:           self.stats["true_positives"]  += 1
        elif is_flagged and not actual_fraud:     self.stats["false_positives"] += 1
        elif not is_flagged and not actual_fraud: self.stats["true_negatives"]  += 1
        elif not is_flagged and actual_fraud:     self.stats["false_negatives"] += 1

        result = {
            "txn_id":          txn["txn_id"],
            "amount":          txn["amount"],
            "merchant_type":   txn["merchant_type"],
            "is_flagged":      is_flagged,
            "ml_risk_score":   round(ml_risk, 1),
            "behavioral_risk": round(behavioral_risk, 1),
            "combined_risk":   round(combined_risk, 1),
            "risk_signals":    risk_signals,
            "actual_fraud":    actual_fraud,
            "fraud_type":      txn.get("fraud_type"),
            "correct":         (is_flagged == actual_fraud),
            "detector":        "ai_model"
        }
        self.results.append(result)
        return result

    def get_metrics(self) -> dict:
        tp = self.stats["true_positives"]
        fp = self.stats["false_positives"]
        tn = self.stats["true_negatives"]
        fn = self.stats["false_negatives"]
        total = tp + fp + tn + fn

        precision   = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall      = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1          = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        accuracy    = (tp + tn) / total if total > 0 else 0
        false_pos_r = fp / (fp + tn) if (fp + tn) > 0 else 0

        return {
            "detector":            "AI Model (Isolation Forest + Behavioral Scoring)",
            "accuracy":            round(accuracy * 100, 1),
            "precision":           round(precision * 100, 1),
            "recall":              round(recall * 100, 1),
            "f1_score":            round(f1 * 100, 1),
            "false_positive_rate": round(false_pos_r * 100, 1),
            "true_positives":      tp,
            "false_positives":     fp,
            "true_negatives":      tn,
            "false_negatives":     fn,
            "total_flagged":       tp + fp,
            "fraud_missed":        fn,
            "color":               "#27ae60"
        }

    def reset(self):
        self.results = []
        self.stats = {k: 0 for k in self.stats}