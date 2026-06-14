import fastuuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import SIM_CONFIG


def generate_events(
    df_sessions: pd.DataFrame, df_users: pd.DataFrame, rng: np.random.Generator
):
    print(f"Generating events for {len(df_sessions)} sessions")

    # pull latent_income_score from parent table for cart additions
    working_df = df_sessions.merge(
        df_users[["user_id", "latent_income_score"]], on="user_id", how="left"
    )

    num_sessions = len(working_df)
    categories = SIM_CONFIG["product_categories"]
    categories_weights = SIM_CONFIG["product_category_weights"]
    android_error_rate = SIM_CONFIG["android_error_rate"]
    android_error_string = SIM_CONFIG["android_error_string"]
    wait_scale = SIM_CONFIG["event_spacing_scale_seconds"]
    dup_rate = SIM_CONFIG["dup_rate_events"]

    # state encoding (ints for fast numpy ops)
    STATE_VIEW_ITEM = 0
    STATE_ADD_TO_CART = 1
    STATE_BEGIN_CHECKOUT = 2
    STATE_PURCHASE = 3
    STATE_DROP_OFF = 4

    state_names = ["view_item", "add_to_cart", "begin_checkout", "purchase", "drop_off"]

    # cumulative transition matrix (5x5) for vectorized next-state sampling
    # row = current state, col = cumulative prob of next state
    trans_cum = np.array([
        [0.40, 0.70, 0.70, 0.70, 1.00],  # view_item
        [0.20, 0.20, 0.70, 0.70, 1.00],  # add_to_cart
        [0.00, 0.00, 0.00, 0.40, 1.00],  # begin_checkout
        [0.00, 0.00, 0.00, 0.00, 1.00],  # purchase -> drop_off
        [0.00, 0.00, 0.00, 0.00, 1.00],  # drop_off -> drop_off
    ])

    # extract session data to numpy arrays (one-time cost)
    session_id_array = working_df["session_id"].to_numpy()
    start_times = working_df["session_start_time"].apply(
        lambda t: t.timestamp()
    ).to_numpy(dtype=np.float64)
    duration_array = working_df["session_duration_seconds"].to_numpy(dtype=np.float64)
    time_limits = start_times + duration_array
    is_android = working_df["device_os_version"].str.contains("Android").to_numpy(dtype=bool)

    # state tracking arrays (updated each step)
    current_state = np.full(num_sessions, STATE_VIEW_ITEM, dtype=np.int32)
    current_time = start_times.copy()
    current_category = np.full(num_sessions, -1, dtype=np.int32)  # -1 = None
    active_mask = np.ones(num_sessions, dtype=bool)

    # event collectors (list of numpy arrays per step -> concat once at end)
    session_id_list = []
    event_timestamp_list = []
    event_type_list = []
    viewed_category_list = []
    error_message_list = []

    # NOTE: vectorized markov chain step-loop
    # all active sessions march forward one step at a time
    # sessions drop out when they reach terminal state or run out of time
    MAX_STEPS = 500

    for _ in range(MAX_STEPS):
        if not active_mask.any():
            break

        n_active = active_mask.sum()

        # category assignment: view_item picks a category, begin_checkout clears it
        in_view = active_mask & (current_state == STATE_VIEW_ITEM)
        n_viewing = in_view.sum()
        if n_viewing > 0:
            current_category[in_view] = rng.choice(
                len(categories), size=n_viewing, p=categories_weights
            ).astype(np.int32)

        in_checkout = active_mask & (current_state == STATE_BEGIN_CHECKOUT)
        current_category[in_checkout] = -1

        # NOTE: INTENTIONAL DATA DEGREDATION: ANDROID TELEMETRY BUG
        error_mask = np.zeros(num_sessions, dtype=bool)
        android_eligible = active_mask & is_android & (current_state == STATE_BEGIN_CHECKOUT)
        n_eligible = android_eligible.sum()
        if n_eligible > 0:
            error_mask[android_eligible] = rng.random(n_eligible) < android_error_rate

        # record event for every active session at this step
        active_idx = active_mask.copy()
        session_id_list.append(session_id_array[active_idx])
        event_timestamp_list.append(current_time[active_idx])
        event_type_list.append(current_state[active_idx])
        viewed_category_list.append(current_category[active_idx])

        err_values = np.full(n_active, None, dtype=object)
        err_values[error_mask[active_idx]] = android_error_string
        error_message_list.append(err_values)

        # 0.5% chance of duplicating events
        dup_mask = np.zeros(num_sessions, dtype=bool)
        dup_mask[active_idx] = rng.random(n_active) < dup_rate
        if dup_mask.any():
            session_id_list.append(session_id_array[dup_mask])
            event_timestamp_list.append(current_time[dup_mask])
            event_type_list.append(current_state[dup_mask])
            viewed_category_list.append(current_category[dup_mask])
            dup_errors = np.full(dup_mask.sum(), None, dtype=object)
            dup_errors[error_mask[dup_mask]] = android_error_string
            error_message_list.append(dup_errors)

        # android error forces session to drop_off
        current_state[error_mask] = STATE_DROP_OFF

        # transition to next state via markov chain (vectorized)
        transitioning = active_mask & (current_state != STATE_DROP_OFF) & (current_state != STATE_PURCHASE)
        n_trans = transitioning.sum()
        if n_trans > 0:
            u = rng.random(n_trans)
            next_states = np.argmax(
                u[:, None] < trans_cum[current_state[transitioning]],
                axis=1
            ).astype(np.int32)
            current_state[transitioning] = next_states

        # advance clock (right-skewed wait times, only for transitioning sessions)
        wait_seconds = np.zeros(num_sessions, dtype=np.float64)
        if n_trans > 0:
            wait_seconds[transitioning] = np.floor(
                rng.exponential(scale=wait_scale, size=n_trans)
            )
        current_time += wait_seconds

        # sessions that exceed time limit in non-terminal state -> timeout event
        past_limit = active_mask & (current_time >= time_limits)
        timeout_now = past_limit & (current_state != STATE_DROP_OFF) & (current_state != STATE_PURCHASE)
        if timeout_now.any():
            session_id_list.append(session_id_array[timeout_now])
            event_timestamp_list.append(time_limits[timeout_now])
            event_type_list.append(np.full(timeout_now.sum(), STATE_DROP_OFF, dtype=np.int32))
            viewed_category_list.append(current_category[timeout_now])
            error_message_list.append(
                np.full(timeout_now.sum(), "ERR_SESSION_TIMEOUT", dtype=object)
            )

        # deactivate sessions in terminal state or past time limit
        terminal = active_mask & (
            (current_state == STATE_DROP_OFF)
            | (current_state == STATE_PURCHASE)
            | (current_time >= time_limits)
        )
        active_mask[terminal] = False

    # concat all step data into single arrays
    all_session_ids = np.concatenate(session_id_list)
    all_timestamps = np.concatenate(event_timestamp_list)
    all_event_types = np.concatenate(event_type_list)
    all_categories = np.concatenate(viewed_category_list)
    all_errors = np.concatenate(error_message_list)
    total_events = len(all_session_ids)

    # generate event primary keys
    event_id = fastuuid.uuid7_as_strings_bulk(total_events)

    # decode ints back to strings (vectorized index lookup)
    event_type_str = np.array(state_names)[all_event_types]

    cat_lookup = np.array(categories + [None])
    cat_idx = np.where(all_categories >= 0, all_categories, len(categories))
    viewed_category_str = cat_lookup[cat_idx]

    # turn into dataframe (pandas)
    df_events = pd.DataFrame(
        {
            "event_id": event_id,
            "session_id": all_session_ids,
            "event_timestamp": pd.to_datetime(all_timestamps, unit="s"),
            "event_type": event_type_str,
            "viewed_category": viewed_category_str,
            "android_error": all_errors,
        }
    )

    print("events table generated!")
    return df_events
