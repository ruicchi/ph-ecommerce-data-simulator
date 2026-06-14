import fastuuid
import pandas as pd
import numpy as np
from datetime import timedelta
from config import SIM_CONFIG


def generate_events(
    df_sessions: pd.DataFrame, df_users: pd.DataFrame, rng: np.random.Generator
):
    print(f"Generating events for {len(df_sessions)} sessions")

    # pull latent_income_score from parent table for cart additions
    working_df = df_sessions.merge(
        df_users[["user_id", "latent_digital_literacy", "latent_trust_in_platform"]],
        on="user_id",
        how="left",
    )
    categories = SIM_CONFIG["product_categories"]
    categories_weights = SIM_CONFIG["product_category_weights"]

    # event field names
    event_id = []
    session_id_fk = []
    event_timestamp = []
    event_type = []
    error_message = []
    viewed_category = []

    # markov chain
    for row in working_df.itertuples():
        current_state = "view_item"
        current_time = row.session_start_time
        time_limit = row.session_start_time + timedelta(
            seconds=row.session_duration_seconds
        )

        # NOTE: device check for intentional data degredation
        is_android = "Android" in row.device_os_version
        current_category = None

        while current_state != "drop_off" and current_time < time_limit:
            error = None

            # assigns category based on user state
            if current_state == "view_item":
                current_category = rng.choice(categories, p=categories_weights)
            elif current_state == "begin_checkout":
                current_category = None

            # NOTE: INTENTIONAL DATA DEGREDATION: ANDROID TELEMETRY BUG
            if current_state == "begin_checkout" and is_android:
                if rng.random() < SIM_CONFIG["android_error_rate"]:
                    error = SIM_CONFIG["android_error_string"]

            # append row data to columns
            event_id.append(str(fastuuid.uuid7()))
            session_id_fk.append(row.session_id)
            event_timestamp.append(current_time)
            event_type.append(current_state)
            error_message.append(error)
            viewed_category.append(current_category)

            # 0.5% chance of triggering
            if rng.random() < SIM_CONFIG["dup_rate_events"]:
                event_id.append(str(fastuuid.uuid7()))
                session_id_fk.append(row.session_id)
                event_timestamp.append(current_time)  # same timestamp
                event_type.append(current_state)
                error_message.append(error)
                viewed_category.append(current_category)

            if error:
                current_state = "drop_off"
                continue

            # loop exit
            if current_state == "drop_off":
                break

            # calculate next state using the transition matrix
            transitions = SIM_CONFIG["base_transactions"][current_state]
            possible_next_states = list(transitions.keys())
            probabilities = list(transitions.values())

            if current_state == "view_item":
                literacy_effect = SIM_CONFIG["funnel_view_item_literacy_effect"]
                literacy_adjustment = literacy_effect * (row.latent_digital_literacy)
                probabilities[1] = probabilities[1] + literacy_adjustment
                probabilities[2] = probabilities[2] - literacy_adjustment

                if "Mobile" in row.device_group:
                    mobile_penalty = SIM_CONFIG["funnel_view_item_mobile_penalty"]
                    probabilities[1] = probabilities[1] + mobile_penalty
                    probabilities[2] = probabilities[2] - mobile_penalty

            elif current_state == "begin_checkout":
                trust_effect = SIM_CONFIG["funnel_checkout_trust_effect"]
                trust_mean = SIM_CONFIG["funnel_checkout_trust_mean"]
                trust_adjustment = trust_effect * (
                    row.latent_trust_in_platform - trust_mean
                )
                probabilities[0] = probabilities[0] + trust_adjustment
                probabilities[1] = probabilities[1] - trust_adjustment

            probabilities = np.clip(probabilities, 0.001, 0.999)
            probabilities = probabilities / np.sum(probabilities)

            current_state = rng.choice(possible_next_states, p=probabilities)

            # create right-skewed distribution on wait time
            avg_wait = SIM_CONFIG["event_spacing_scale_seconds"]
            random_wait = int(rng.exponential(scale=avg_wait))
            current_time += timedelta(seconds=random_wait)

        # session timeout cleanup when (current_time > time_limit)
        if current_state not in ["drop_off", "purchase"]:
            event_id.append(str(fastuuid.uuid7()))
            session_id_fk.append(row.session_id)
            event_timestamp.append(time_limit)
            event_type.append("drop_off")
            error_message.append("ERR_SESSION_TIMEOUT")
            viewed_category.append(current_category)

    # turn into dataframe (pandas)
    df_events = pd.DataFrame(
        {
            "event_id": event_id,
            "session_id": session_id_fk,
            "event_timestamp": event_timestamp,
            "event_type": event_type,
            "viewed_category": viewed_category,
            "android_error": error_message,
        }
    )

    print("events table generated!")
    return df_events
