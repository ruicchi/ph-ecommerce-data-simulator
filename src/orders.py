import uuid
import pandas as pd
from numpy.random import default_rng

from config import SIM_CONFIG

rng = default_rng(SIM_CONFIG["random_seed"])


def generate_orders(df_events: pd.DataFrame, df_sessions: pd.DataFrame):
    # only get purchase
    purchase = df_events[df_events["event_type"] == "purchase"].copy()
    print(f"Generating {len(purchase)} orders for purchases events")

    purchase = purchase.merge(
        df_sessions[["session_id", "user_id"]], on="session_id", how="left"
    )

    order_id = []
    for _ in range(len(purchase)):
        new_id = str(uuid.uuid4())
        order_id.append(new_id)

    session_id_fk = purchase["session_id"].tolist()

    user_id_fk = purchase["user_id"].tolist()

    order_timestamp = purchase["event_timestamp"].tolist()

    order_total_amount = 0.0

    # turn into dataframe (pandas)
    df_orders = pd.DataFrame(
        {
            "order_id": order_id,
            "session_id": session_id_fk,
            "user_id": user_id_fk,
            "order_timestamp": order_timestamp,
            "order_total_amount": order_total_amount,
        }
    )
    return df_orders
