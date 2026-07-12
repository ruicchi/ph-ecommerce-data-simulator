import fastuuid
import pandas as pd
import numpy as np
from config import SIM_CONFIG


def generate_orders(
    purchase_data: dict,
    rng: np.random.Generator,
) -> pd.DataFrame:
    num_purchases = len(purchase_data["session_id"])
    print(f"Generating {num_purchases} orders for purchases events")

    order_id = fastuuid.uuid4_as_strings_bulk(num_purchases)
    session_id_fk = purchase_data["session_id"]
    user_id_fk = purchase_data["user_id"]
    order_timestamp = purchase_data["event_timestamp"]

    income = purchase_data["latent_income_score"]
    income_thresholds = SIM_CONFIG["income_payment_thresholds"]
    income_tier = np.full(num_purchases, "mid", dtype=object)
    income_tier[income < income_thresholds[0]] = "low"
    income_tier[income >= income_thresholds[1]] = "high"

    income_tier_names = list(SIM_CONFIG["payment_weights_by_income"].keys())
    payment_type = np.empty(num_purchases, dtype=object)

    for tier in income_tier_names:
        mask = income_tier == tier
        if mask.any():
            payment_type[mask] = rng.choice(
                SIM_CONFIG["payment_type"],
                size=mask.sum(),
                p=SIM_CONFIG["payment_weights_by_income"][tier],
            )

    df_orders = pd.DataFrame(
        {
            "order_id": order_id,
            "session_id": session_id_fk,
            "user_id": user_id_fk,
            "order_timestamp": order_timestamp,
            "payment_type": payment_type,
        }
    )
    print("orders table generated!")
    return df_orders
