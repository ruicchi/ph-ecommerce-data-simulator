import fastuuid
import pandas as pd
import numpy as np
from config import SIM_CONFIG


def generate_orders(
    df_events: pd.DataFrame,
    df_sessions: pd.DataFrame,
    df_users: pd.DataFrame,
    rng: np.random.Generator,
):
    purchase = df_events[df_events["event_name"] == "purchase"].copy()
    print(f"Generating {len(purchase)} orders for purchases events")

    purchase = purchase.merge(
        df_sessions[["session_id", "user_id"]], on="session_id", how="left"
    )

    purchase = purchase.merge(
        df_users[["user_id", "latent_income_score"]], on="user_id", how="left"
    )

    order_id = fastuuid.uuid4_as_strings_bulk(len(purchase))
    session_id_fk = purchase["session_id"].tolist()
    user_id_fk = purchase["user_id"].tolist()
    order_timestamp = purchase["event_timestamp"].tolist()

    income = purchase["latent_income_score"].to_numpy()

    income_thresholds = SIM_CONFIG["income_payment_thresholds"]
    income_tier = np.full(len(purchase), "mid", dtype=object)
    income_tier[income < income_thresholds[0]] = "low"
    income_tier[income >= income_thresholds[1]] = "high"

    income_tier_names = list(SIM_CONFIG["payment_weights_by_income"].keys())
    payment_type = np.empty(len(purchase), dtype=object)

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
