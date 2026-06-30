"""
Flask API — run with: python app.py
API at: http://localhost:5000
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))

from flask import Flask, jsonify, request
from flask_cors import CORS
from transaction_generator import generate_transaction_batch
from rule_detector import RuleBasedDetector
from ai_detector import AIFraudDetector

app = Flask(__name__)
CORS(app)

rule_detector = RuleBasedDetector()
ai_detector   = AIFraudDetector(contamination=0.08)
all_transactions = []
comparison_results = []
is_initialized = False


def initialize(n_transactions=300, fraud_rate=0.08):
    global all_transactions, comparison_results, is_initialized, rule_detector, ai_detector

    rule_detector = RuleBasedDetector()
    ai_detector   = AIFraudDetector(contamination=fraud_rate)

    transactions, _ = generate_transaction_batch(
        n_customers=25, n_transactions=n_transactions, fraud_rate=fraud_rate
    )
    all_transactions = transactions
    ai_detector.train(transactions)

    comparison_results = []
    for txn in transactions:
        rule_result = rule_detector.evaluate(txn)
        ai_result   = ai_detector.predict(txn)
        comparison_results.append({
            "txn_id":        txn["txn_id"],
            "customer_id":   txn["customer_id"],
            "amount":        txn["amount"],
            "merchant_type": txn["merchant_type"],
            "city":          txn["city"],
            "hour_of_day":   txn["hour_of_day"],
            "is_fraud":      txn["is_fraud"],
            "fraud_type":    txn.get("fraud_type"),
            "amount_vs_avg": round(txn["amount_vs_avg_ratio"], 2),
            "velocity":      txn["txn_velocity_1h"],
            "rule_flagged":  rule_result["is_flagged"],
            "rule_triggers": rule_result["triggered_rules"],
            "rule_correct":  rule_result["correct"],
            "ai_flagged":    ai_result["is_flagged"],
            "ai_risk_score": ai_result["combined_risk"],
            "ai_signals":    ai_result["risk_signals"],
            "ai_correct":    ai_result["correct"],
        })

    is_initialized = True
    return len(transactions)


initialize()


@app.route("/api/status")
def status():
    return jsonify({
        "initialized":      is_initialized,
        "total_transactions": len(all_transactions),
        "fraud_count":      sum(1 for t in all_transactions if t["is_fraud"]),
        "legitimate_count": sum(1 for t in all_transactions if not t["is_fraud"]),
    })


@app.route("/api/metrics")
def metrics():
    return jsonify({
        "rule_based": rule_detector.get_metrics(),
        "ai_model":   ai_detector.get_metrics(),
    })


@app.route("/api/transactions")
def transactions():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    filter_  = request.args.get("filter", "all")

    results = comparison_results
    if filter_ == "fraud":
        results = [r for r in results if r["is_fraud"]]
    elif filter_ == "legitimate":
        results = [r for r in results if not r["is_fraud"]]
    elif filter_ == "disagreements":
        results = [r for r in results if r["rule_flagged"] != r["ai_flagged"]]
    elif filter_ == "missed_fraud":
        results = [r for r in results if r["is_fraud"] and not r["rule_flagged"] and r["ai_flagged"]]

    start = (page - 1) * per_page
    return jsonify({
        "transactions": results[start:start + per_page],
        "total":        len(results),
        "page":         page,
        "per_page":     per_page,
        "total_pages":  (len(results) + per_page - 1) // per_page,
        "filter":       filter_,
    })


@app.route("/api/fraud_types")
def fraud_types():
    fraud_txns = [r for r in comparison_results if r["is_fraud"]]
    types = {}
    for txn in fraud_txns:
        ft = txn["fraud_type"] or "unknown"
        if ft not in types:
            types[ft] = {"fraud_type": ft, "count": 0,
                         "rule_caught": 0, "ai_caught": 0, "both_missed": 0}
        types[ft]["count"] += 1
        if txn["rule_flagged"]: types[ft]["rule_caught"] += 1
        if txn["ai_flagged"]:   types[ft]["ai_caught"]   += 1
        if not txn["rule_flagged"] and not txn["ai_flagged"]:
            types[ft]["both_missed"] += 1

    for ft in types.values():
        ft["rule_detection_rate"] = round(ft["rule_caught"] / ft["count"] * 100, 1)
        ft["ai_detection_rate"]   = round(ft["ai_caught"]   / ft["count"] * 100, 1)

    return jsonify(list(types.values()))


@app.route("/api/reinitialize", methods=["POST"])
def reinitialize():
    data  = request.get_json() or {}
    count = initialize(
        n_transactions=data.get("n_transactions", 300),
        fraud_rate=data.get("fraud_rate", 0.08)
    )
    return jsonify({"success": True, "transactions_generated": count})


@app.route("/api/single_transaction", methods=["POST"])
def single_transaction():
    data = request.get_json()
    txn = {
        "txn_id":              data.get("txn_id", "TXNTEST"),
        "customer_id":         data.get("customer_id", "CUST0001"),
        "amount":              float(data.get("amount", 1000)),
        "merchant_type":       data.get("merchant_type", "transfer"),
        "city":                data.get("city", "Mumbai"),
        "hour_of_day":         int(data.get("hour_of_day", 14)),
        "day_of_week":         int(data.get("day_of_week", 2)),
        "is_new_merchant":     bool(data.get("is_new_merchant", False)),
        "is_new_city":         bool(data.get("is_new_city", False)),
        "txn_velocity_1h":     int(data.get("txn_velocity_1h", 1)),
        "amount_vs_avg_ratio": float(data.get("amount_vs_avg_ratio", 1.0)),
        "account_age_days":    int(data.get("account_age_days", 365)),
        "is_fraud":            bool(data.get("is_fraud", False)),
        "fraud_type":          data.get("fraud_type", None),
    }
    return jsonify({
        "transaction":  txn,
        "rule_verdict": rule_detector.evaluate(txn),
        "ai_verdict":   ai_detector.predict(txn),
    })


if __name__ == "__main__":
    print(f"\n🏦 Backend ready — {len(all_transactions)} transactions loaded")
    print(f"   Fraud: {sum(1 for t in all_transactions if t['is_fraud'])}")
    print("   API: http://localhost:5000\n")
    app.run(debug=True, port=5000)