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


def _build_events_config() -> dict:
    # bt = base_transactions
    bt = SIM_CONFIG["base_transactions"]
    return {
        "item_categories": SIM_CONFIG["item_categories"],
        "category_cdf": np.cumsum(SIM_CONFIG["item_category_weights"]),
        "average_wait": SIM_CONFIG["average_wait"],
        "android_error_rate": SIM_CONFIG["android_error_rate"],
        "android_error_string": SIM_CONFIG["android_error_string"],
        "dup_rate_events": SIM_CONFIG["dup_rate_events"],
        "literacy_effect": SIM_CONFIG["funnel_view_item_literacy_effect"],
        "mobile_penalty": SIM_CONFIG["funnel_view_item_mobile_penalty"],
        "trust_effect": SIM_CONFIG["funnel_checkout_trust_effect"],
        "trust_mean": SIM_CONFIG["funnel_checkout_trust_mean"],
        "transitions": {
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


def _events_worker(
    session_data: dict, rng: np.random.Generator, events_config: dict
) -> pd.DataFrame:
    """
    Simulates user events for a chunk of sessions using a Markov Chain approach.

    Key Variables & Abbreviations:
        - rng: np.random.Generator used for all random choices in this worker.
        - *_arr: Suffix indicating a 1D NumPy array covering all sessions in the chunk
        - vi_*: Variables related to the _VIEW_ITEM state.
            - vi_base: Baseline probabilities for transitions out of _VIEW_ITEM.
            - vi_probs_matrix: A 2D array where each row holds personalized _VIEW_ITEM
                               transition probabilities tailored to a specific user's traits.
        - bc_*: Variables related to the _BEGIN_CHECKOUT state.
        - ns: Suffix indicating nanoseconds for fast integer time math.
        - idx: Suffix indicating an integer index used to select from an array.
        - r: A random float between 0 and 1, used for cumulative sum probability choices.
    """
    item_categories = events_config["item_categories"]
    category_cdf = events_config["category_cdf"]
    average_wait = events_config["average_wait"]
    android_error_rate = events_config["android_error_rate"]
    android_error_string = events_config["android_error_string"]
    dup_rate_events = events_config["dup_rate_events"]
    literacy_effect = events_config["literacy_effect"]
    mobile_penalty = events_config["mobile_penalty"]
    trust_effect = events_config["trust_effect"]
    trust_mean = events_config["trust_mean"]
    transitions = events_config["transitions"]

    is_android_arr = session_data["device_operating_system"] == "android"
    is_mobile_arr = session_data["device_group"] == "mobile"
    literacy_arr = session_data["latent_digital_literacy"].astype(np.float64)
    trust_arr = session_data["latent_trust_in_platform"].astype(np.float64)
    session_id_arr = session_data["session_id"]
    start_time_ns = (
        session_data["session_start_time"].astype("datetime64[ns]").astype(np.int64)
    )
    duration_ns = (
        session_data["session_duration_seconds"].astype(np.int64) * 1_000_000_000
    )

    n_sessions = len(session_id_arr)

    # ==========================================
    # FAST VECTORIZED PRE-CALCULATION
    # ==========================================
    # We pre-calculate all the personalized probabilities for _VIEW_ITEM
    # and _BEGIN_CHECKOUT for the entire chunk at once, avoiding millions of np.clip calls.

    vi_states, vi_base = transitions[_VIEW_ITEM]
    vi_probs_matrix = np.tile(vi_base, (n_sessions, 1))
    vi_probs_matrix[:, 0] += literacy_effect * literacy_arr
    vi_probs_matrix[:, 4] -= literacy_effect * literacy_arr
    vi_probs_matrix[is_mobile_arr, 0] += mobile_penalty
    vi_probs_matrix[is_mobile_arr, 4] -= mobile_penalty
    vi_probs_matrix = np.clip(vi_probs_matrix, 0.001, 0.999)
    vi_probs_matrix /= vi_probs_matrix.sum(axis=1, keepdims=True)

    bc_states, bc_base = transitions[_BEGIN_CHECKOUT]
    bc_probs_matrix = np.tile(bc_base, (n_sessions, 1))
    adj = trust_effect * (trust_arr - trust_mean)
    bc_probs_matrix[:, 0] += adj
    bc_probs_matrix[:, 2] -= adj
    bc_probs_matrix = np.clip(bc_probs_matrix, 0.001, 0.999)
    bc_probs_matrix /= bc_probs_matrix.sum(axis=1, keepdims=True)

    # ==========================================
    # MEMORY ALLOCATION
    # ==========================================
    # We remove event_id from the loop entirely.
    session_id_fk = []
    event_timestamp_ns = []
    event_name_int = []
    error_message = []
    viewed_category = []

    # ==========================================
    # FAST EVENT GENERATION LOOP
    # ==========================================
    for i in range(n_sessions):
        current_state = _VIEW_ITEM
        current_time = start_time_ns[i]
        time_limit = start_time_ns[i] + duration_ns[i]
        is_android = is_android_arr[i]
        current_category = None

        # Pre-slice matrices for this specific user to avoid repeated lookups
        user_vi_probs = vi_probs_matrix[i]
        user_bc_probs = bc_probs_matrix[i]

        while current_state != _DROP_OFF and current_time < time_limit:
            error = None

            if current_state == _VIEW_ITEM:
                idx = np.searchsorted(category_cdf, rng.random())
                current_category = item_categories[idx]
            elif current_state == _BEGIN_CHECKOUT:
                current_category = None

            if (
                current_state == _BEGIN_CHECKOUT
                and is_android
                and rng.random() < android_error_rate
            ):
                error = android_error_string

            session_id_fk.append(session_id_arr[i])
            event_timestamp_ns.append(current_time)
            event_name_int.append(current_state)
            error_message.append(error)
            viewed_category.append(current_category)

            # Duplication Glitch logic
            if rng.random() < dup_rate_events:
                session_id_fk.append(session_id_arr[i])
                event_timestamp_ns.append(current_time)
                event_name_int.append(current_state)
                error_message.append(error)
                viewed_category.append(current_category)

            if error:
                current_state = _DROP_OFF
                continue

            if current_state == _DROP_OFF:
                break

            # Extremely fast state transition (No math required inside the loop!)
            if current_state == _VIEW_ITEM:
                next_states = vi_states
                probs = user_vi_probs
            elif current_state == _BEGIN_CHECKOUT:
                next_states = bc_states
                probs = user_bc_probs
            else:
                next_states, probs = transitions[current_state]

            # Fast cumulative sum choice
            r = rng.random()
            cumulative = 0.0
            for j in range(len(probs)):
                cumulative += probs[j]
                if r < cumulative:
                    current_state = next_states[j]
                    break

            current_time += int(rng.exponential(scale=average_wait)) * 1_000_000_000

    # ==========================================
    # FINAL DATAFRAME ASSEMBLY
    # ==========================================
    total_generated_events = len(session_id_fk)

    df_events = pd.DataFrame(
        {
            # 1. Bulk generate UUIDs at C-speed instead of in Python loop
            "event_id": fastuuid.uuid4_as_strings_bulk(total_generated_events),
            "session_id": session_id_fk,
            "event_timestamp": pd.to_datetime(
                np.array(event_timestamp_ns, dtype=np.int64)
            ),
            # 2. Fast NumPy mapping instead of list comprehension
            "event_name": np.array(_STATE_NAMES)[event_name_int],
            "viewed_category": viewed_category,
            "android_error": error_message,
        }
    )

    return df_events


def generate_events(session_data: dict, rng: np.random.Generator, n_workers):
    num_sessions = len(session_data["session_id"])
    print(f"Generating events for {num_sessions} sessions")

    events_config = _build_events_config()

    n_workers = max(1, min(n_workers, num_sessions))

    if n_workers <= 1:
        return _events_worker(session_data, rng, events_config)

    child_bgs = rng.bit_generator.spawn(n_workers)

    indices = np.array_split(np.arange(num_sessions), n_workers)

    chunks = []
    for idx in indices:
        chunk = {
            "session_id": session_data["session_id"][idx],
            "device_operating_system": session_data["device_operating_system"][idx],
            "device_group": session_data["device_group"][idx],
            "latent_digital_literacy": session_data["latent_digital_literacy"][idx],
            "latent_trust_in_platform": session_data["latent_trust_in_platform"][idx],
            "session_start_time": session_data["session_start_time"][idx],
            "session_duration_seconds": session_data["session_duration_seconds"][idx],
        }
        chunks.append(chunk)

    with mp.Pool(n_workers) as pool:
        results = pool.starmap(
            _events_worker,
            [
                (chunk, np.random.default_rng(bg), events_config)
                for chunk, bg in zip(chunks, child_bgs)
            ],
        )

    return pd.concat(results, ignore_index=True)
