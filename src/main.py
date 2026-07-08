import os
import numpy as np
from config import SIM_CONFIG
from users import generate_users
from sessions import generate_sessions
from events import generate_events
from orders import generate_orders
from order_items import generate_order_items

if __name__ == "__main__":
    master_ss = np.random.SeedSequence(SIM_CONFIG["random_seed"])
    stage_seeds = master_ss.spawn(5)
    rng_users = np.random.default_rng(stage_seeds[0])
    rng_sessions = np.random.default_rng(stage_seeds[1])
    rng_events = np.random.default_rng(stage_seeds[2])
    rng_orders = np.random.default_rng(stage_seeds[3])
    rng_order_items = np.random.default_rng(stage_seeds[4])

    n_workers = SIM_CONFIG.get("n_workers", 1)

    # TEST: FOR TESTING ONLY

    # test_users_df = generate_users(SIM_CONFIG["target_users"], rng_users)
    test_users_df = generate_users(20, rng_users)
    test_sessions_df = generate_sessions(test_users_df, rng_sessions)
    test_events_df = generate_events(
        test_sessions_df, test_users_df, rng_events, n_workers
    )
    test_orders_df = generate_orders(test_events_df, test_sessions_df, rng_orders)
    test_order_items_df = generate_order_items(
        test_orders_df, test_users_df, rng_order_items
    )

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

    # TEST: EXPORT TO test_data
    print("\nTEST: EXPORTING TO CSV")

    os.makedirs("test_data", exist_ok=True)

    clean_users_df = test_users_df.drop(
        columns=[
            "latent_income_score",
            "latent_digital_literacy",
            "latent_trust_in_platform",
        ]
    )

    sorted_test_events_df = test_events_df.sort_values(
        by="event_timestamp"
    ).reset_index(drop=True)
    sorted_test_orders_df = test_orders_df.sort_values(
        by="order_timestamp"
    ).reset_index(drop=True)

    clean_users_df.to_csv("test_data/users.csv", index=False)
    test_sessions_df.to_csv("test_data/sessions.csv", index=False)
    sorted_test_events_df.to_csv("test_data/events.csv", index=False)
    sorted_test_orders_df.to_csv("test_data/orders.csv", index=False)
    test_order_items_df.to_csv("test_data/order_items.csv", index=False)

    print("export completed in test_data folder")
