# 🏦 AI vs Rule-Based Fraud Detection
### Banking Demo — Indian UCB Context (TJSB / AJHC)

A full working project that demonstrates **why AI-powered fraud detection outperforms traditional rule-based systems** in Indian banking — using realistic UPI, phishing, account-takeover, card-skimming, and mule-account fraud patterns.

Built around the real digital fraud problem at Indian Urban Co-operative Banks:
- **TJSB Sahakari Bank** — 18.69 crore UPI transactions worth ₹29,800+ crore (FY25-26)
- **Ambarnath Jai-Hind Co-operative Bank** — smaller UCB relying on vendor-provided fraud tools
- **RBI data** — digital payment fraud up 27% YoY, ₹36,014 crore lost in FY2024-25

---

## 📁 Project Structure

```
fraud-detection-demo/
│
├── README.md
│
├── backend/
│   ├── app.py                    ← Flask REST API (run this first)
│   ├── rule_detector.py          ← Traditional rule-based system (5 fixed rules)
│   └── ai_detector.py            ← AI model: Isolation Forest + Behavioral Scoring
│
├── data/
│   └── transaction_generator.py  ← Generates realistic Indian banking transactions
│
└── frontend/
    └── index.html                ← Dark-mode dashboard (open in browser)
```

---

## ⚡ Quick Start

### Step 1 — Install dependencies

```bash
pip install flask flask-cors scikit-learn numpy pandas
```

### Step 2 — Start the backend API

```bash
cd backend
python app.py
```

You should see:

```
🏦 TJSB/AJHC Fraud Detection Demo — Backend Ready
==================================================
  Transactions generated : 300
  Fraud transactions     : ~24
  Legitimate transactions: ~276
  API running at: http://localhost:5000
```

> Keep this terminal open. The API must be running for the dashboard to work.

### Step 3 — Open the dashboard

Open a **second terminal** and run:

```bash
# Windows
start frontend/index.html

# Mac
open frontend/index.html

# Linux
xdg-open frontend/index.html
```

Or in **VS Code**: right-click `frontend/index.html` → **Open with Live Server**

---

## 🖥️ What the Dashboard Shows

The dashboard has 5 sections:

| Section | What it shows |
|---|---|
| **Head-to-Head Performance** | 3 banner cards: fraud missed by rules (not AI), AI recall advantage %, false alarms saved |
| **Detection Metrics** | Side-by-side panels (red = rules, green = AI) with Recall, False Positive Rate, Precision, F1 Score |
| **Fraud Type Detection Rates** | Table showing how each detector handles each of the 5 fraud patterns |
| **Transaction Feed** | Every transaction with both detectors' verdict side by side + AI risk score out of 100 |
| **Filter buttons** | All · Only Fraud · Only Legitimate · AI vs Rule Disagreements · Fraud AI Caught Rules Missed |

---

## 🔬 What's Being Simulated

### 5 Fraud Patterns (mirroring RBI fraud taxonomy)

| Fraud Type | How it works | Key signals |
|---|---|---|
| **UPI Account Takeover** | Large transfer, odd hour (2am), new city | Amount ratio >10x, velocity spike, night hour |
| **Phishing / Credential Theft** | Many rapid transactions after credentials stolen | High velocity, new merchant, large amount |
| **Social Engineering** | Victim tricked into authorising a transfer | New merchant, very large amount |
| **Card / ATM Skimming** | ATM withdrawal in different city at midnight | New city, ATM merchant, deep night hour |
| **Mule Account** | Many small rapid transfers for laundering | Very high velocity, new merchant, moderate amount |

### Why the Results Are Realistic

- **~8% fraud rate** matches RBI's reported digital payment fraud incidence
- **Customer profiles** have realistic spending averages, home cities, active hours
- **Amounts** are drawn from merchant-type ranges matching Indian spending patterns

---

## 🤖 How the AI Detector Works

**Stage 1 — Isolation Forest (Unsupervised ML)**
- Trains on all 300 transactions without needing fraud labels
- Learns the "normal" behavioural envelope of the transaction dataset
- Assigns an anomaly score to each transaction (how unusual vs. normal)
- Key advantage: adapts to new fraud patterns without manual rule updates

**Stage 2 — Behavioral Scoring Layer (Explainable AI)**

7 risk signals, each weighted and added into a 0–100 score:

| Signal | Weight | Why |
|---|---|---|
| Amount vs customer average (>10x) | +35 | Extreme anomaly |
| Transaction velocity >10/hr | +30 | Mule / takeover pattern |
| Deep night hour (0–3am) | +20 | Fraud timing signal |
| New merchant + large amount | +20 | Phishing pattern |
| New city | +15 | Geographic anomaly |
| New account (<30 days) | +15 | Higher inherent risk |
| High absolute amount (>₹75,000) | +10 | Additional signal |

**Decision: Combined Risk Score > 40 → Flag transaction**

This explainability layer satisfies RBI's model governance requirements — every flag comes with a human-readable reason.

---

## 📊 Expected Results

| Metric | Rule-Based | AI Model |
|---|---|---|
| Recall (fraud caught) | ~58–70% | ~80–95% |
| False Positive Rate | ~12–18% | ~1–3% |
| F1 Score | ~45–60% | ~65–80% |
| Mule account detection | **~80–100%** (velocity rule) | **~10–30%** (per-txn misses rings) |
| Social engineering detection | ~15–25% | **~75–90%** |

> The honest result: neither system wins on everything. Rules catch mule accounts via velocity threshold; AI catches social engineering and novel patterns that rules miss. This mirrors why RBI built **MuleHunter.AI** as a separate graph-based system — per-transaction scoring alone cannot catch mule networks.

---

## 🔧 API Endpoints

Base URL: `http://localhost:5000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/status` | Dataset summary (total, fraud, legit counts) |
| GET | `/api/metrics` | Side-by-side accuracy metrics for both detectors |
| GET | `/api/transactions` | Paginated transaction list with both verdicts |
| GET | `/api/fraud_types` | Per-fraud-type detection rates |
| POST | `/api/reinitialize` | Generate new random dataset and retrain |
| POST | `/api/single_transaction` | Test any custom transaction against both detectors |

### Query parameters for `/api/transactions`

```
?page=1
?per_page=15
?filter=all | fraud | legitimate | disagreements | missed_fraud
```

### Test a custom suspicious transaction

```bash
curl -X POST http://localhost:5000/api/single_transaction \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 85000,
    "merchant_type": "transfer",
    "hour_of_day": 2,
    "is_new_city": true,
    "txn_velocity_1h": 8,
    "amount_vs_avg_ratio": 12.5,
    "account_age_days": 15
  }'
```

### Generate a fresh dataset

```bash
curl -X POST http://localhost:5000/api/reinitialize \
  -H "Content-Type: application/json" \
  -d '{"n_transactions": 500, "fraud_rate": 0.10}'
```

---

## 🏦 Banking Context

### Why this matters for TJSB

TJSB processed **20 crore digital transactions in FY2025-26**, with 18.69 crore via UPI worth ₹29,800+ crore. The bank has already implemented:
- Enterprise Fraud Risk Management System (EFRMS) for real-time IMPS monitoring
- Early Warning System (EWS) for credit risk
- Collaboration with I4C (Cyber Coordination Centre, Ministry of Home Affairs)

TJSB is ahead of most UCBs — but even its current system is rule-based at its core. This demo shows what the next layer (ML-based anomaly detection) adds.

### Why this matters for AJHC

Ambarnath Jai-Hind Co-operative Bank (~₹1,000 crore business mix, 25 branches) has no publicly disclosed AI or ML fraud detection. It relies entirely on vendor-provided CBS fraud modules — exactly the rule-based system this demo benchmarks as the weaker baseline.

### The RBI regulatory push

RBI's **Digital Payment Intelligence Platform (DPIP)** is being built with 5–10 banks using AI/ML. RBI's **MuleHunter.AI** (launched Dec 2024) is already piloted in two public sector banks. The **FREE-AI framework** provides structured guidance for responsible AI adoption in Indian banking. Banks that invest in AI fraud detection now are building infrastructure that will be expected by regulators within 2–3 years.

---

## 📦 Dependencies

```
flask          — REST API server
flask-cors     — Cross-origin requests from browser
scikit-learn   — Isolation Forest model
numpy          — Numerical operations
pandas         — (available, not required at runtime)
```

Install all at once:

```bash
pip install flask flask-cors scikit-learn numpy pandas
```

---

## 🛠️ Troubleshooting

**Dashboard shows "Loading..." and never loads**
→ Backend is not running. Start it with `python backend/app.py` first.

**Port 5000 already in use**
```bash
# Mac/Linux — find and kill the process
lsof -i :5000
kill -9 <PID>

# Or change the port in app.py (last line): app.run(port=5001)
# And update API url in index.html line 206: const API = 'http://localhost:5001/api'
```

**ModuleNotFoundError**
```bash
pip install flask flask-cors scikit-learn numpy pandas
```

**Browser blocks the API (CORS error)**
→ Make sure you're opening `index.html` directly as a file, not serving it from a different port. Or use VS Code Live Server.

---

*Built to demonstrate AI fraud detection concepts in the context of Indian cooperative banking — TJSB Sahakari Bank and Ambarnath Jai-Hind Co-operative Bank.*
