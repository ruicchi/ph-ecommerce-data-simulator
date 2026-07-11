import os
import numpy as np
from config import SIM_CONFIG
from users import generate_users
from sessions import generate_sessions
from events import generate_events
from orders import generate_orders
from order_items import generate_order_items


def export_test_data(
    df_test_users,
    df_test_sessions,
    df_test_events,
    df_test_orders,
    df_test_order_items,
    output_dir="test_data",
):
    # TEST: EXPORT TO test_data
    print("\nTEST: EXPORTING TO CSV (test_data)")

    os.makedirs(output_dir, exist_ok=True)

    df_clean_users = df_test_users.drop(
        columns=[
            "latent_income_score",
            "latent_digital_literacy",
            "latent_trust_in_platform",
        ]
    )

    df_test_sorted_events = df_test_events.sort_values(
        by="event_timestamp"
    ).reset_index(drop=True)
    df_test_sorted_orders = df_test_orders.sort_values(
        by="order_timestamp"
    ).reset_index(drop=True)

    df_clean_users.to_csv("test_data/users.csv", index=False)
    df_test_sessions.to_csv("test_data/sessions.csv", index=False)
    df_test_sorted_events.to_csv("test_data/events.csv", index=False)
    df_test_sorted_orders.to_csv("test_data/orders.csv", index=False)
    df_test_order_items.to_csv("test_data/order_items.csv", index=False)

    print("export completed in test_data folder")


if __name__ == "__main__":
    # TEST: FOR TESTING ONLY
    master_ss = np.random.SeedSequence(SIM_CONFIG["random_seed"])
    stage_seeds = master_ss.spawn(5)
    rng_users = np.random.default_rng(stage_seeds[0])
    rng_sessions = np.random.default_rng(stage_seeds[1])
    rng_events = np.random.default_rng(stage_seeds[2])
    rng_orders = np.random.default_rng(stage_seeds[3])
    rng_order_items = np.random.default_rng(stage_seeds[4])

    n_workers = SIM_CONFIG["n_workers"]

    # test_users_df = generate_users(SIM_CONFIG["target_users"], rng_users)
    df_test_users = generate_users(20, rng_users)
    df_test_sessions = generate_sessions(df_test_users, rng_sessions)
    df_test_events = generate_events(
        df_test_sessions, df_test_users, rng_events, n_workers
    )
    df_test_orders = generate_orders(df_test_events, df_test_sessions, rng_orders)
    df_test_order_items = generate_order_items(
        df_test_orders, df_test_users, rng_order_items
    )

    print("\nTEST: GENERATED USERS")
    print(df_test_users)

    print("\nTEST: GENERATED SESSIONS")
    print(df_test_sessions)

    print("\nTEST: GENERATED EVENTS")
    print(df_test_events)

    print("\nTEST: GENERATED ORDERS")
    print(df_test_orders)

    print("\nTEST: GENERATED ORDER ITEMS")
    print(df_test_order_items)

    print("\nTEST: DATA TYPES (USERS)")
    print(df_test_users.dtypes)

    print("\nTEST: DATA TYPES (SESSIONS)")
    print(df_test_sessions.dtypes)

    print("\nTEST: DATA TYPES (EVENTS)")
    print(df_test_events.dtypes)

    print("\nTEST: DATA TYPES (ORDERS)")
    print(df_test_orders.dtypes)

    print("\nTEST: DATA TYPES (ORDER ITEMS)")
    print(df_test_order_items.dtypes)

    # export_test_data(
    #     df_test_users,
    #     df_test_sessions,
    #     df_test_events,
    #     df_test_orders,
    #     df_test_order_items,
    #     output_dir="test_data",
    # )
