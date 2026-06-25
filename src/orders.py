import fastuuid
import pandas as pd
import numpy as np
from config import SIM_CONFIG


def generate_orders(
    df_events: pd.DataFrame, df_sessions: pd.DataFrame, rng: np.random.Generator
):
    # only get purchase
    purchase = df_events[df_events["event_type"] == "purchase"].copy()
    print(f"Generating {len(purchase)} orders for purchases events")

    purchase = purchase.merge(
        df_sessions[["session_id", "user_id"]], on="session_id", how="left"
    )

    order_id = fastuuid.uuid4_as_strings_bulk(len(purchase))

    session_id_fk = purchase["session_id"].tolist()

    user_id_fk = purchase["user_id"].tolist()

    order_timestamp = purchase["event_timestamp"].tolist()

    payment_method = rng.choice(
        SIM_CONFIG["payment_methods"],
        size=len(purchase),
        p=SIM_CONFIG["payment_method_weights"],
    )

    df_orders = pd.DataFrame(
        {
            "order_id": order_id,
            "session_id": session_id_fk,
            "user_id": user_id_fk,
            "order_timestamp": order_timestamp,
            "payment_method": payment_method,
        }
    )
    print("orders table generated!")
    return df_orders
