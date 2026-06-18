import multiprocessing as mp
import numpy as np
import pandas as pd
import fastuuid
from config import SIM_CONFIG

_VIEW_ITEM = 0
_ADD_TO_CART = 1
_BEGIN_CHECKOUT = 2
_PURCHASE = 3
_DROP_OFF = 4

_STATE_NAMES = ["view_item", "add_to_cart", "begin_checkout", "purchase", "drop_off"]


def _build_events_config():
    bt = SIM_CONFIG["base_transactions"]
    return {
        "categories": SIM_CONFIG["product_categories"],
        "cat_cdf": np.cumsum(SIM_CONFIG["product_category_weights"]),
        "avg_wait": SIM_CONFIG["event_spacing_scale_seconds"],
        "android_error_rate": SIM_CONFIG["android_error_rate"],
        "android_error_string": SIM_CONFIG["android_error_string"],
        "dup_rate": SIM_CONFIG["dup_rate_events"],
        "literacy_effect": SIM_CONFIG["funnel_view_item_literacy_effect"],
        "mobile_penalty": SIM_CONFIG["funnel_view_item_mobile_penalty"],
        "trust_effect": SIM_CONFIG["funnel_checkout_trust_effect"],
        "trust_mean": SIM_CONFIG["funnel_checkout_trust_mean"],
        "trans": {
            _VIEW_ITEM: (
                np.array([_VIEW_ITEM, _ADD_TO_CART, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["view_item"]["view_item"],
                        bt["view_item"]["add_to_cart"],
                        bt["view_item"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _ADD_TO_CART: (
                np.array([_VIEW_ITEM, _BEGIN_CHECKOUT, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["add_to_cart"]["view_item"],
                        bt["add_to_cart"]["begin_checkout"],
                        bt["add_to_cart"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _BEGIN_CHECKOUT: (
                np.array([_PURCHASE, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["begin_checkout"]["purchase"],
                        bt["begin_checkout"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _PURCHASE: (
                np.array([_DROP_OFF], dtype=np.int8),
                np.array([1.0], dtype=np.float64),
            ),
        },
    }


def _events_worker(chunk_df, rng_or_seed, config):
    if not isinstance(rng_or_seed, np.random.Generator):
        rng = np.random.default_rng(rng_or_seed)
    else:
        rng = rng_or_seed

    categories = config["categories"]
    cat_cdf = config["cat_cdf"]
    avg_wait = config["avg_wait"]
    android_error_rate = config["android_error_rate"]
    android_error_string = config["android_error_string"]
    dup_rate = config["dup_rate"]
    literacy_effect = config["literacy_effect"]
    mobile_penalty = config["mobile_penalty"]
    trust_effect = config["trust_effect"]
    trust_mean = config["trust_mean"]
    trans = config["trans"]

    is_android_arr = chunk_df["device_os_version"].str.contains("Android").to_numpy()
    is_mobile_arr = (chunk_df["device_group"] == "Mobile").to_numpy()
    literacy_arr = chunk_df["latent_digital_literacy"].to_numpy(dtype=np.float64)
    trust_arr = chunk_df["latent_trust_in_platform"].to_numpy(dtype=np.float64)
    session_id_arr = chunk_df["session_id"].to_numpy()
    start_time_ns = chunk_df["session_start_time"].astype("datetime64[ns]").to_numpy(dtype=np.int64)
    duration_ns = (
        chunk_df["session_duration_seconds"].to_numpy(dtype=np.int64) * 1_000_000_000
    )

    n_sessions = len(chunk_df)

    event_id = []
    session_id_fk = []
    event_timestamp_ns = []
    event_type_int = []
    error_message = []
    viewed_category = []

    for i in range(n_sessions):
        current_state = _VIEW_ITEM
        current_time = start_time_ns[i]
        time_limit = start_time_ns[i] + duration_ns[i]
        is_android = is_android_arr[i]
        is_mobile = is_mobile_arr[i]
        literacy = literacy_arr[i]
        trust = trust_arr[i]
        current_category = None

        while current_state != _DROP_OFF and current_time < time_limit:
            error = None

            if current_state == _VIEW_ITEM:
                idx = np.searchsorted(cat_cdf, rng.random())
                current_category = categories[idx]
            elif current_state == _BEGIN_CHECKOUT:
                current_category = None

            if (
                current_state == _BEGIN_CHECKOUT
                and is_android
                and rng.random() < android_error_rate
            ):
                error = android_error_string

            event_id.append(str(fastuuid.uuid7()))
            session_id_fk.append(session_id_arr[i])
            event_timestamp_ns.append(current_time)
            event_type_int.append(current_state)
            error_message.append(error)
            viewed_category.append(current_category)

            if rng.random() < dup_rate:
                event_id.append(str(fastuuid.uuid7()))
                session_id_fk.append(session_id_arr[i])
                event_timestamp_ns.append(current_time)
                event_type_int.append(current_state)
                error_message.append(error)
                viewed_category.append(current_category)

            if error:
                current_state = _DROP_OFF
                continue

            if current_state == _DROP_OFF:
                break

            next_states, base_probs = trans[current_state]
            probs = base_probs.copy()

            if current_state == _VIEW_ITEM:
                probs[1] += literacy_effect * literacy
                probs[2] -= literacy_effect * literacy
                if is_mobile:
                    probs[1] += mobile_penalty
                    probs[2] -= mobile_penalty
            elif current_state == _BEGIN_CHECKOUT:
                adj = trust_effect * (trust - trust_mean)
                probs[0] += adj
                probs[1] -= adj

            np.clip(probs, 0.001, 0.999, out=probs)
            probs /= probs.sum()

            r = rng.random()
            cumulative = 0.0
            for j in range(len(probs)):
                cumulative += probs[j]
                if r < cumulative:
                    current_state = next_states[j]
                    break

            current_time += int(rng.exponential(scale=avg_wait)) * 1_000_000_000

        if current_state not in (_DROP_OFF, _PURCHASE):
            event_id.append(str(fastuuid.uuid7()))
            session_id_fk.append(session_id_arr[i])
            event_timestamp_ns.append(time_limit)
            event_type_int.append(_DROP_OFF)
            error_message.append("ERR_SESSION_TIMEOUT")
            viewed_category.append(current_category)

    return pd.DataFrame(
        {
            "event_id": event_id,
            "session_id": session_id_fk,
            "event_timestamp": pd.to_datetime(
                np.array(event_timestamp_ns, dtype=np.int64)
            ),
            "event_type": [_STATE_NAMES[s] for s in event_type_int],
            "viewed_category": viewed_category,
            "android_error": error_message,
        }
    )


def generate_events(df_sessions, df_users, rng, n_workers=1):
    print(f"Generating events for {len(df_sessions)} sessions")

    working_df = df_sessions.merge(
        df_users[["user_id", "latent_digital_literacy", "latent_trust_in_platform"]],
        on="user_id",
        how="left",
    )

    config = _build_events_config()

    n_workers = max(1, min(n_workers, len(working_df)))

    if n_workers <= 1:
        return _events_worker(working_df, rng, config)

    child_bgs = rng.bit_generator.spawn(n_workers)

    indices = np.array_split(np.arange(len(working_df)), n_workers)
    chunks = [working_df.iloc[idx].copy() for idx in indices]

    with mp.Pool(n_workers) as pool:
        results = pool.starmap(
            _events_worker,
            [
                (chunk, np.random.default_rng(bg), config)
                for chunk, bg in zip(chunks, child_bgs)
            ],
        )

    return pd.concat(results, ignore_index=True)
