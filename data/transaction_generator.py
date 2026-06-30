"""
Transaction Generator
Simulates realistic Indian banking/UPI transactions including
various fraud patterns seen in actual bank data.
"""

import random
import time
from datetime import datetime, timedelta
import numpy as np

CITIES = [
    "Mumbai", "Thane", "Pune", "Nashik", "Nagpur",
    "Delhi", "Bengaluru", "Chennai", "Hyderabad", "Kolkata"
]

MERCHANT_TYPES = [
    "grocery", "fuel", "restaurant", "utility", "medical",
    "ecommerce", "transfer", "ATM", "insurance", "education"
]

MERCHANT_SPEND_RANGE = {
    "grocery":    (200,  3000),
    "fuel":       (500,  5000),
    "restaurant": (100,  2000),
    "utility":    (500,  5000),
    "medical":    (300, 10000),
    "ecommerce":  (300, 15000),
    "transfer":   (500, 50000),
    "ATM":        (500, 10000),
    "insurance":  (2000,25000),
    "education":  (5000,50000),
}

class CustomerProfile:
    def __init__(self, customer_id):
        self.customer_id = customer_id
        self.home_city = random.choice(CITIES[:5])
        self.avg_txn_amount = random.uniform(500, 8000)
        self.usual_merchants = random.sample(MERCHANT_TYPES, k=random.randint(3, 6))
        self.active_hours = random.choice([(8, 22), (9, 20), (7, 23)])
        self.monthly_txn_count = random.randint(15, 80)
        self.account_age_days = random.randint(180, 3650)


def generate_normal_transaction(profile: CustomerProfile, txn_id: int) -> dict:
    merchant = random.choice(profile.usual_merchants)
    low, high = MERCHANT_SPEND_RANGE[merchant]
    amount = round(random.uniform(
        max(low, profile.avg_txn_amount * 0.3),
        min(high, profile.avg_txn_amount * 2.0)
    ), 2)
    hour = random.randint(*profile.active_hours)
    city = profile.home_city if random.random() > 0.15 else random.choice(CITIES)

    return {
        "txn_id": f"TXN{txn_id:06d}",
        "customer_id": profile.customer_id,
        "amount": amount,
        "merchant_type": merchant,
        "city": city,
        "hour_of_day": hour,
        "day_of_week": random.randint(0, 6),
        "is_new_merchant": random.random() < 0.1,
        "is_new_city": city != profile.home_city,
        "txn_velocity_1h": random.randint(0, 3),
        "amount_vs_avg_ratio": amount / profile.avg_txn_amount,
        "account_age_days": profile.account_age_days,
        "is_fraud": False,
        "fraud_type": None,
        "label": "LEGITIMATE"
    }


def generate_fraud_transaction(profile: CustomerProfile, txn_id: int) -> dict:
    fraud_type = random.choice([
        "upi_takeover", "phishing_credential",
        "social_engineering", "card_skimming", "mule_account"
    ])
    txn = generate_normal_transaction(profile, txn_id)
    txn["is_fraud"] = True
    txn["fraud_type"] = fraud_type
    txn["label"] = "FRAUD"

    if fraud_type == "upi_takeover":
        txn["amount"] = round(random.uniform(15000, 99000), 2)
        txn["hour_of_day"] = random.choice([0, 1, 2, 3, 4, 23])
        txn["city"] = random.choice([c for c in CITIES if c != profile.home_city])
        txn["is_new_city"] = True
        txn["txn_velocity_1h"] = random.randint(4, 12)
        txn["amount_vs_avg_ratio"] = txn["amount"] / profile.avg_txn_amount

    elif fraud_type == "phishing_credential":
        txn["amount"] = round(random.uniform(5000, 50000), 2)
        txn["txn_velocity_1h"] = random.randint(5, 15)
        txn["is_new_merchant"] = True
        txn["merchant_type"] = random.choice(["transfer", "ecommerce"])
        txn["amount_vs_avg_ratio"] = txn["amount"] / profile.avg_txn_amount

    elif fraud_type == "social_engineering":
        txn["amount"] = round(random.uniform(10000, 100000), 2)
        txn["merchant_type"] = "transfer"
        txn["is_new_merchant"] = True
        txn["amount_vs_avg_ratio"] = txn["amount"] / profile.avg_txn_amount

    elif fraud_type == "card_skimming":
        txn["amount"] = round(random.choice([10000, 20000, 25000, 49000]), 2)
        txn["merchant_type"] = "ATM"
        txn["city"] = random.choice([c for c in CITIES if c != profile.home_city])
        txn["is_new_city"] = True
        txn["hour_of_day"] = random.choice([0, 1, 2, 3])
        txn["amount_vs_avg_ratio"] = txn["amount"] / profile.avg_txn_amount

    elif fraud_type == "mule_account":
        txn["amount"] = round(random.uniform(499, 4999), 2)
        txn["merchant_type"] = "transfer"
        txn["txn_velocity_1h"] = random.randint(8, 20)
        txn["is_new_merchant"] = True
        txn["amount_vs_avg_ratio"] = txn["amount"] / profile.avg_txn_amount

    return txn


def generate_transaction_batch(n_customers=20, n_transactions=200, fraud_rate=0.08):
    customers = [CustomerProfile(f"CUST{i:04d}") for i in range(n_customers)]
    transactions = []
    for i in range(n_transactions):
        profile = random.choice(customers)
        if random.random() < fraud_rate:
            txn = generate_fraud_transaction(profile, i)
        else:
            txn = generate_normal_transaction(profile, i)
        transactions.append(txn)
    return transactions, customers