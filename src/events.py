import multiprocessing as mp
import numpy as np
import pandas as pd
import fastuuid
from config import SIM_CONFIG

_SEARCH = 0
_VIEW_ITEM_LIST = 1
_SELECT_ITEM = 2
_VIEW_ITEM = 3
_ADD_TO_WISHLIST = 4
_SHARE = 5
_ADD_TO_CART = 6
_REMOVE_FROM_CART = 7
_VIEW_CART = 8
_BEGIN_CHECKOUT = 9
_ADD_SHIPPING_INFO = 10
_ADD_PAYMENT_INFO = 11
_PURCHASE = 12
_GENERATE_LEAD = 13
_REFUND = 14
_DROP_OFF = 15

_STATE_NAMES = [
    "search",
    "view_item_list",
    "select_item",
    "view_item",
    "add_to_wishlist",
    "share",
    "add_to_cart",
    "remove_from_cart",
    "view_cart",
    "begin_checkout",
    "add_shipping_info",
    "add_payment_info",
    "purchase",
    "generate_lead",
    "refund",
    "drop_off",
]


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
            _SEARCH: (
                np.array([_VIEW_ITEM_LIST, _DROP_OFF], dtype=np.int8),
                np.array(
                    [bt["search"]["view_item_list"], bt["search"]["drop_off"]],
                    dtype=np.float64,
                ),
            ),
            _VIEW_ITEM_LIST: (
                np.array([_SELECT_ITEM, _SEARCH, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["view_item_list"]["select_item"],
                        bt["view_item_list"]["search"],
                        bt["view_item_list"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _SELECT_ITEM: (
                np.array([_VIEW_ITEM, _VIEW_ITEM_LIST, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["select_item"]["view_item"],
                        bt["select_item"]["view_item_list"],
                        bt["select_item"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _VIEW_ITEM: (
                np.array(
                    [
                        _ADD_TO_CART,
                        _ADD_TO_WISHLIST,
                        _SHARE,
                        _VIEW_ITEM_LIST,
                        _DROP_OFF,
                    ],
                    dtype=np.int8,
                ),
                np.array(
                    [
                        bt["view_item"]["add_to_cart"],
                        bt["view_item"]["add_to_wishlist"],
                        bt["view_item"]["share"],
                        bt["view_item"]["view_item_list"],
                        bt["view_item"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _ADD_TO_WISHLIST: (
                np.array([_VIEW_ITEM, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["add_to_wishlist"]["view_item"],
                        bt["add_to_wishlist"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _SHARE: (
                np.array([_VIEW_ITEM, _DROP_OFF], dtype=np.int8),
                np.array(
                    [bt["share"]["view_item"], bt["share"]["drop_off"]],
                    dtype=np.float64,
                ),
            ),
            _ADD_TO_CART: (
                np.array(
                    [_VIEW_CART, _VIEW_ITEM, _REMOVE_FROM_CART, _DROP_OFF],
                    dtype=np.int8,
                ),
                np.array(
                    [
                        bt["add_to_cart"]["view_cart"],
                        bt["add_to_cart"]["view_item"],
                        bt["add_to_cart"]["remove_from_cart"],
                        bt["add_to_cart"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _REMOVE_FROM_CART: (
                np.array([_VIEW_CART, _VIEW_ITEM, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["remove_from_cart"]["view_cart"],
                        bt["remove_from_cart"]["view_item"],
                        bt["remove_from_cart"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _VIEW_CART: (
                np.array([_BEGIN_CHECKOUT, _VIEW_ITEM, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["view_cart"]["begin_checkout"],
                        bt["view_cart"]["view_item"],
                        bt["view_cart"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _BEGIN_CHECKOUT: (
                np.array([_ADD_SHIPPING_INFO, _VIEW_CART, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["begin_checkout"]["add_shipping_info"],
                        bt["begin_checkout"]["view_cart"],
                        bt["begin_checkout"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _ADD_SHIPPING_INFO: (
                np.array([_ADD_PAYMENT_INFO, _VIEW_CART, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["add_shipping_info"]["add_payment_info"],
                        bt["add_shipping_info"]["view_cart"],
                        bt["add_shipping_info"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _ADD_PAYMENT_INFO: (
                np.array([_PURCHASE, _VIEW_CART, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["add_payment_info"]["purchase"],
                        bt["add_payment_info"]["view_cart"],
                        bt["add_payment_info"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _PURCHASE: (
                np.array([_GENERATE_LEAD, _REFUND, _DROP_OFF], dtype=np.int8),
                np.array(
                    [
                        bt["purchase"]["generate_lead"],
                        bt["purchase"]["refund"],
                        bt["purchase"]["drop_off"],
                    ],
                    dtype=np.float64,
                ),
            ),
            _GENERATE_LEAD: (
                np.array([_DROP_OFF], dtype=np.int8),
                np.array([bt["generate_lead"]["drop_off"]], dtype=np.float64),
            ),
            _REFUND: (
                np.array([_DROP_OFF], dtype=np.int8),
                np.array([bt["refund"]["drop_off"]], dtype=np.float64),
            ),
            _DROP_OFF: (
                np.array([_DROP_OFF], dtype=np.int8),
                np.array([bt["drop_off"]["drop_off"]], dtype=np.float64),
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
    start_time_ns = (
        chunk_df["session_start_time"].astype("datetime64[ns]").to_numpy(dtype=np.int64)
    )
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

            event_id.append(str(fastuuid.uuid4()))
            session_id_fk.append(session_id_arr[i])
            event_timestamp_ns.append(current_time)
            event_type_int.append(current_state)
            error_message.append(error)
            viewed_category.append(current_category)

            if rng.random() < dup_rate:
                event_id.append(str(fastuuid.uuid4()))
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
                probs[0] += literacy_effect * literacy
                probs[4] -= literacy_effect * literacy
                if is_mobile:
                    probs[0] += mobile_penalty
                    probs[4] -= mobile_penalty
            elif current_state == _BEGIN_CHECKOUT:
                adj = trust_effect * (trust - trust_mean)
                probs[0] += adj
                probs[2] -= adj

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
            event_id.append(str(fastuuid.uuid4()))
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
