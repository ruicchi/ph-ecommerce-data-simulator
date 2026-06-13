import os
import numpy as np

from config import SIM_CONFIG
from users import generate_users
from sessions import generate_sessions
from events import generate_events
from orders import generate_orders
from order_items import generate_order_items

# TEST: FOR TESTING ONLY
if __name__ == "__main__":
    rng = np.random.default_rng(SIM_CONFIG["random_seed"])
    # test_users_df = generate_users(SIM_CONFIG["target_users"])

    test_users_df = generate_users(20, rng)
    test_sessions_df = generate_sessions(test_users_df, rng)
    test_events_df = generate_events(test_sessions_df, test_users_df, rng)
    test_orders_df = generate_orders(test_events_df, test_sessions_df)
    test_order_items_df = generate_order_items(test_orders_df, test_users_df, rng)

    # ETL to calculate order total (initialized from generate_orders)
    test_order_items_df["line_total"] = (
        test_order_items_df["item_price"] * test_order_items_df["quantity"]
    )

    order_totals = (
        test_order_items_df.groupby("order_id")["line_total"].sum().reset_index()
    )

    test_orders_df = (
        test_orders_df.drop(columns=["order_total_amount"])
        .merge(order_totals, on="order_id", how="left")
        .rename(columns={"line_total": "order_total_amount"})
    )
    test_order_items_df = test_order_items_df.drop(columns=["line_total"])

    print("\nTEST: GENERATED USERS")
    print(test_users_df)

    print("\nTEST: GENERATED SESSIONS")
    print(test_sessions_df)

    print("\nTEST: GENERATED EVENTS")
    print(test_events_df)

    print("\nTEST: GENERATED ORDERS")
    print(test_orders_df)

    print("\nTEST: GENERATED ORDER ITEMS")
    print(test_order_items_df)

    print("\nTEST: DATA TYPES (USERS)")
    print(test_users_df.dtypes)

    print("\nTEST: DATA TYPES (SESSIONS)")
    print(test_sessions_df.dtypes)

    print("\nTEST: DATA TYPES (EVENTS)")
    print(test_events_df.dtypes)

    print("\nTEST: DATA TYPES (ORDERS)")
    print(test_orders_df.dtypes)

    print("\nTEST: DATA TYPES (ORDER ITEMS)")
    print(test_order_items_df.dtypes)

    print("\nEXPORTING TO CSV")

    os.makedirs("data", exist_ok=True)

    clean_users_df = test_users_df.drop(
        columns=["latent_income_score", "latent_tech_savviness"]
    )

    sorted_test_events_df = test_events_df.sort_values(
        by="event_timestamp"
    ).reset_index(drop=True)
    sorted_test_orders_df = test_orders_df.sort_values(
        by="order_timestamp"
    ).reset_index(drop=True)

    clean_users_df.to_csv("data/users.csv", index=False)
    test_sessions_df.to_csv("data/sessions.csv", index=False)
    sorted_test_events_df.to_csv("data/events.csv", index=False)
    sorted_test_orders_df.to_csv("data/orders.csv", index=False)
    test_order_items_df.to_csv("data/order_items.csv", index=False)

    print("export completed in data folder")
