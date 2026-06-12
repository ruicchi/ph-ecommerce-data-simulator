import pandas as pd
import numpy as np
import uuid
import os
from datetime import datetime, timedelta

# set seed to 42 for determinism (numpy)
rng = np.random.default_rng(42)

# NOTE: this will change, depending on the configurables based on the funnel optimization analyst
SIM_CONFIG = {
    "as_of_date": "2023-12-31",
    "target_users": 10000,
    # user config
    "android_share": 0.65,
    "ios_share": 0.35,
    "channels": ["Organic", "Facebook", "TikTok", "Direct"],
    "channel_weights": [0.40, 0.30, 0.20, 0.10],
    # session config
    "session_count": [1, 2, 3, 4, 5, 8, 15],
    "session_count_weights": [0.65, 0.15, 0.08, 0.05, 0.04, 0.02, 0.01],
    "burst_session_weights": [0.70, 0.30],
    "average_dropoff": 5,
    "peak_hours": [13, 21],
    "session_base_max_seconds": 300,
    "session_base_min_seconds": 10,
    "os_distribution": ["Android", "iOS", "Windows", "macOS"],
    "os_weights": [0.40, 0.25, 0.20, 0.15],
    "android_software_version": ["14", "13", "12", "11"],
    "android_software_version_weights": [0.5, 0.3, 0.15, 0.05],
    "ios_software_version": ["17.3", "16.5", "15.2"],
    "ios_software_version_weights": [0.6, 0.3, 0.1],
    "windows_software_version": ["11", "10"],
    "windows_software_version_weights": [0.7, 0.3],
    "macos_software_version": ["Sonoma", "Ventura", "Monterey"],
    "savviness_time_reduction": 150,
    # NOTE: think about the degredation of data more
    "android_error_rate": 0.05,
    "android_error_string": "ERR_VERSION_NOT_FOUND",
    # events config
    "event_spacing_seconds": 15,
    "base_transactions": {
        # if user is viewing an item
        "view_item": {"view_item": 0.40, "add_to_cart": 0.30, "drop_off": 0.30},
        # if user added to cart
        "add_to_cart": {"view_item": 0.20, "begin_checkout": 0.50, "drop_off": 0.30},
        # if user begins checkout
        "begin_checkout": {"purchase": 0.40, "drop_off": 0.60},
        # end states (if user purchases or drop off, session is over
        "purchase": {"drop_off": 1.0},
        "drop_off": {"drop_off": 1.0},
    },
    # order items config"
    "items_per_order_counts": [1, 2, 3, 4, 5],
    "items_per_order_weights": [0.50, 0.30, 0.10, 0.05, 0.05],
    "item_quantity_counts": [1, 2, 3, 5],
    "item_quantity_weights": [0.85, 0.10, 0.04, 0.01],
    "product_categories": ["Apparel", "Electronics", "Home Goods", "Consumables"],
    "product_category_weights": [0.50, 0.20, 0.15, 0.15],
    "category_base_prices": {
        "Apparel": 35.00,
        "Electronics": 250.00,
        "Home Goods": 85.00,
        "Consumables": 15.00,
    },
    "promo_code_probability": 0.25,
    "promo_discount_tiers": [0.10, 0.15, 0.20, 0.50],
    "promo_discount_weights": [0.50, 0.30, 0.15, 0.05],
}


def generate_users(total_users: int):
    print(f"Generating {total_users} users")

    # user primary keys
    user_ids = []
    for _ in range(total_users):
        new_id = str(uuid.uuid4())
        user_ids.append(new_id)

    # assigns acquisition channel
    acq_channel = rng.choice(
        SIM_CONFIG["channels"], size=total_users, p=SIM_CONFIG["channel_weights"]
    )

    # account created timestamps
    base_date = datetime.strptime(SIM_CONFIG["as_of_date"], "%Y-%m-%d")
    days_ago_array = rng.integers(0, 365, size=total_users)
    seconds_ago_array = rng.integers(0, 86400, size=total_users)

    created_at = []
    for days, seconds in zip(days_ago_array, seconds_ago_array):
        past_date = base_date - timedelta(days=int(days), seconds=int(seconds))
        created_at.append(past_date)

    # engine for latent variables (numpy) | creates a gaussian distribution | NOTE: this might change, defeats the purpose of funnel optimization analyst
    latent_income_score = rng.normal(loc=0, scale=1.0, size=total_users)
    latent_tech_savviness = rng.uniform(low=0, high=1.0, size=total_users)

    # turn into dataframe (pandas)
    df_users = pd.DataFrame(
        {
            "user_id": user_ids,
            "account_created_at": created_at,
            "acquisition_channel": acq_channel,
            "latent_income_score": latent_income_score,
            "latent_tech_savviness": latent_tech_savviness,
        }
    )

    print("users tables generated!")
    return df_users


def generate_sessions(df_users: pd.DataFrame):
    num_users = len(df_users)
    sessions_per_user = rng.choice(
        SIM_CONFIG["session_count"],
        size=num_users,
        p=SIM_CONFIG["session_count_weights"],
    )
    total_sessions = sessions_per_user.sum()

    print(f"Generating {total_sessions} sessions")

    # repeat the parent rows so they line with total_sessions
    exploded_users = df_users.loc[df_users.index.repeat(sessions_per_user)].reset_index(
        drop=True
    )

    # session primary keys
    session_id = []
    for _ in range(total_sessions):
        new_id = str(uuid.uuid4())
        session_id.append(new_id)

    # parent foreign keys
    user_id_fk = exploded_users["user_id"].tolist()

    # session start timestamps (bimodal diurnal peak hours) | NOTE: random days is only limited to 30
    parent_created_at = exploded_users["account_created_at"].tolist()
    base_date = datetime.strptime(SIM_CONFIG["as_of_date"], "%Y-%m-%d")

    lifespan_days = [(base_date - created).days for created in parent_created_at]

    is_burst_session = rng.choice(
        [True, False], size=total_sessions, p=SIM_CONFIG["burst_session_weights"]
    )

    burst_days = rng.exponential(
        scale=SIM_CONFIG["average_dropoff"], size=total_sessions
    )
    loyalty_days = rng.uniform(low=0, high=lifespan_days, size=total_sessions)

    raw_days = np.where(is_burst_session, burst_days, loyalty_days)

    random_days_array = np.minimum(raw_days, lifespan_days).astype(int)

    chosen_peaks = rng.choice(SIM_CONFIG["peak_hours"], size=total_sessions)
    normal_dist_hours = rng.normal(loc=chosen_peaks, scale=1.0)
    random_seconds_array = ((normal_dist_hours % 24) * 3600).astype(int)

    session_start_time = []
    for created_date, days, seconds in zip(
        parent_created_at, random_days_array, random_seconds_array
    ):
        start_date = created_date + timedelta(days=int(days), seconds=int(seconds))
        session_start_time.append(start_date)

    # session duration | NOTE: exponential decay is based on tech savviness
    latent_savviness = exploded_users["latent_tech_savviness"].to_numpy()
    base_duration = rng.exponential(
        scale=SIM_CONFIG["session_base_max_seconds"], size=total_sessions
    )
    savviness_reduction = latent_savviness * SIM_CONFIG["savviness_time_reduction"]

    # no session is shorter than 10 seconds
    session_duration_seconds = (
        np.maximum(
            SIM_CONFIG["session_base_min_seconds"], base_duration - savviness_reduction
        )
        .astype(int)
        .tolist()
    )

    # device OS versions
    base_os_array = rng.choice(
        SIM_CONFIG["os_distribution"],
        size=total_sessions,
        p=SIM_CONFIG["os_weights"],
    )

    device_os_version = []
    for os_type in base_os_array:
        if os_type == "Android":
            version = rng.choice(
                SIM_CONFIG["android_software_version"],
                p=SIM_CONFIG["android_software_version_weights"],
            )

        elif os_type == "iOS":
            version = rng.choice(
                SIM_CONFIG["ios_software_version"],
                p=SIM_CONFIG["ios_software_version_weights"],
            )
        elif os_type == "Windows":
            version = rng.choice(
                SIM_CONFIG["windows_software_version"],
                p=SIM_CONFIG["windows_software_version_weights"],
            )

        else:
            version = rng.choice(
                SIM_CONFIG["macos_software_version"],
            )

        device_os_version.append(f"{os_type} {version}")

    # turn into dataframe (pandas)
    df_sessions = pd.DataFrame(
        {
            "session_id": session_id,
            "user_id": user_id_fk,
            "session_start_time": session_start_time,
            "session_duration_seconds": session_duration_seconds,
            "device_os_version": device_os_version,
        }
    )

    print("sessions table generated!")
    return df_sessions


def generate_events(df_sessions: pd.DataFrame, df_users: pd.DataFrame):
    print(f"Generating events for {len(df_sessions)} sessions")

    # pull latent_income_score from parent table for cart additions
    working_df = df_sessions.merge(
        df_users[["user_id", "latent_income_score"]], on="user_id", how="left"
    )

    # event field names
    event_id = []
    session_id_fk = []
    event_timestamp = []
    event_type = []
    error_message = []

    # markov chain
    for row in working_df.itertuples():
        current_state = "view_item"
        current_time = row.session_start_time
        time_limit = row.session_start_time + timedelta(
            seconds=row.session_duration_seconds
        )

        # NOTE: device check for intentional data degredation
        is_android = "Android" in row.device_os_version

        while current_state != "drop_off" and current_time < time_limit:
            error = None

            # NOTE: INTENTIONAL DATA DEGREDATION: ANDROID TELEMETRY BUG
            if current_state == "begin_checkout" and is_android:
                if rng.random() < SIM_CONFIG["android_error_rate"]:
                    error = SIM_CONFIG["android_error_string"]
                    current_state = "drop_off"

            # append row data to columns
            event_id.append(str(uuid.uuid4()))
            session_id_fk.append(row.session_id)
            event_timestamp.append(current_time)
            event_type.append(current_state)
            error_message.append(error)

            # loop exit
            if current_state == "drop_off":
                break

            # calculate next state using the transition matrix
            transitions = SIM_CONFIG["base_transactions"][current_state]
            possible_next_states = list(transitions.keys())
            probabilities = list(transitions.values())

            current_state = rng.choice(possible_next_states, p=probabilities)
            current_time += timedelta(seconds=SIM_CONFIG["event_spacing_seconds"])

    # turn into dataframe (pandas)
    df_events = pd.DataFrame(
        {
            "event_id": event_id,
            "session_id": session_id_fk,
            "event_timestamp": event_timestamp,
            "event_type": event_type,
            "android_error": error_message,
        }
    )

    print("events table generated!")
    return df_events


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


def generate_order_items(df_orders: pd.DataFrame, df_users: pd.DataFrame):
    print(f"Generating order items for {len(df_orders)} orders")

    working_df = df_orders.merge(
        df_users[["user_id", "latent_income_score"]], on="user_id", how="left"
    )

    num_orders = len(working_df)

    # NOTE: vectorized math
    items_per_order = rng.choice(
        SIM_CONFIG["items_per_order_counts"],
        size=num_orders,
        p=SIM_CONFIG["items_per_order_weights"],
    )
    total_items = items_per_order.sum()

    exploded_orders = working_df.loc[
        working_df.index.repeat(items_per_order)
    ].reset_index(drop=True)

    # generate columns (vectors-style)
    item_id_list = []
    for _ in range(total_items):
        new_id = str(uuid.uuid4())
        item_id_list.append(new_id)

    item_order_fk = exploded_orders["order_id"].tolist()

    item_quantity = rng.choice(
        SIM_CONFIG["item_quantity_counts"],
        size=total_items,
        p=SIM_CONFIG["item_quantity_weights"],
    )

    # pricing logic
    item_category = rng.choice(
        SIM_CONFIG["product_categories"],
        size=total_items,
        p=SIM_CONFIG["product_category_weights"],
    )
    base_prices = (
        pd.Series(item_category).map(SIM_CONFIG["category_base_prices"]).to_numpy()
    )
    is_discounted = rng.random(size=total_items) < SIM_CONFIG["promo_code_probability"]
    discount_tiers = rng.choice(
        SIM_CONFIG["promo_discount_tiers"],
        size=total_items,
        p=SIM_CONFIG["promo_discount_weights"],
    )
    actual_discount = np.where(is_discounted, discount_tiers, 0.0)

    income_scores = exploded_orders["latent_income_score"].to_numpy()
    noise = rng.normal(0, 10, size=total_items)
    raw_prices = base_prices + (income_scores * 20) + noise
    item_price = np.maximum(9.99, raw_prices).round(2)
    discounted_prices = raw_prices * (1.0 - actual_discount)
    item_price = np.maximum(4.99, discounted_prices).round(2)

    # turn into dataframe (pandas)
    df_order_items = pd.DataFrame(
        {
            "order_item_id": item_id_list,
            "order_id": item_order_fk,
            "product_category": item_category,
            "item_price": item_price,
            "quantity": item_quantity,
            "discount_percentage": actual_discount,
        }
    )

    print("order items table generated!")
    return df_order_items


# TEST: FOR TESTING ONLY
if __name__ == "__main__":
    # test_users_df = generate_users(SIM_CONFIG["target_users"])

    test_users_df = generate_users(20)
    test_sessions_df = generate_sessions(test_users_df)
    test_events_df = generate_events(test_sessions_df, test_users_df)
    test_orders_df = generate_orders(test_events_df, test_sessions_df)
    test_order_items_df = generate_order_items(test_orders_df, test_users_df)

    # ETL to calculate order total (initialized from generate_orders)
    test_order_items_df["line_total"] = (
        test_order_items_df["item_price"] * test_order_items_df["quantity"]

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

    clean_users_df.to_csv("data/users.csv", index=False)
    test_sessions_df.to_csv("data/sessions.csv", index=False)
    test_events_df.to_csv("data/events.csv", index=False)
    test_orders_df.to_csv("data/orders.csv", index=False)
    test_order_items_df.to_csv("data/order_items.csv", index=False)

    print("export completed in data folder")
