"""
Rule-Based Fraud Detector
Traditional approach used by most Indian cooperative banks today.
Problems: fixed thresholds miss novel fraud, high false positive rate.
"""

class RuleBasedDetector:

    def __init__(self):
        self.rules = {
            "high_amount_threshold":  50000,
            "odd_hour_start":         23,
            "odd_hour_end":           5,
            "velocity_threshold":     5,
            "amount_ratio_threshold": 5.0,
        }
        self.results = []
        self.stats = {
            "true_positives":  0,
            "false_positives": 0,
            "true_negatives":  0,
            "false_negatives": 0,
        }

    def evaluate(self, txn: dict) -> dict:
        triggered_rules = []
        is_flagged = False

        # Rule 1: High amount
        if txn["amount"] > self.rules["high_amount_threshold"]:
            triggered_rules.append(f"AMOUNT > ₹{self.rules['high_amount_threshold']:,}")
            is_flagged = True

        # Rule 2: Odd-hour transaction
        hour = txn["hour_of_day"]
        if hour >= self.rules["odd_hour_start"] or hour <= self.rules["odd_hour_end"]:
            triggered_rules.append(f"ODD_HOUR ({hour}:00)")
            is_flagged = True

        # Rule 3: High transaction velocity
        if txn["txn_velocity_1h"] > self.rules["velocity_threshold"]:
            triggered_rules.append(f"VELOCITY > {self.rules['velocity_threshold']}/hr")
            is_flagged = True

        # Rule 4: Amount ratio vs customer average
        if txn["amount_vs_avg_ratio"] > self.rules["amount_ratio_threshold"]:
            triggered_rules.append(f"AMOUNT_RATIO > {self.rules['amount_ratio_threshold']}x avg")
            is_flagged = True

        # Rule 5: New city ONLY combined with another signal (standalone = too many FPs)
        existing_flags = len(triggered_rules)
        if txn["is_new_city"] and existing_flags > 0:
            triggered_rules.append("NEW_CITY (+ other signal)")
            is_flagged = True

        actual_fraud = txn["is_fraud"]
        if is_flagged and actual_fraud:       self.stats["true_positives"]  += 1
        elif is_flagged and not actual_fraud: self.stats["false_positives"] += 1
        elif not is_flagged and not actual_fraud: self.stats["true_negatives"]  += 1
        elif not is_flagged and actual_fraud: self.stats["false_negatives"] += 1

        result = {
            "txn_id":          txn["txn_id"],
            "amount":          txn["amount"],
            "merchant_type":   txn["merchant_type"],
            "is_flagged":      is_flagged,
            "triggered_rules": triggered_rules,
            "actual_fraud":    actual_fraud,
            "fraud_type":      txn.get("fraud_type"),
            "correct":         (is_flagged == actual_fraud),
            "detector":        "rule_based"
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
            "detector":            "Rule-Based System",
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
            "color":               "#e74c3c"
        }

    def reset(self):
        self.results = []
        self.stats = {k: 0 for k in self.stats}