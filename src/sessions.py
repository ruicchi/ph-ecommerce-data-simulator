import fastuuid
import pandas as pd
import numpy as np
from config import SIM_CONFIG


def generate_sessions(user_data: dict, rng: np.random.Generator):
    tenure_days = user_data["user_tenure_days"]
    base_interval = SIM_CONFIG["base_session_interval_days"]
    base_expected_sessions = tenure_days / base_interval

    literacy = user_data["latent_digital_literacy"]
    max_score = SIM_CONFIG["literacy_max_score"]
    boost_weight = SIM_CONFIG["literacy_session_boost_weight"]

    literacy_multiplier = 1.0 + (literacy / max_score) * boost_weight
    lambda_arr = base_expected_sessions * literacy_multiplier

    raw_sessions = rng.poisson(lam=lambda_arr)
    sessions_per_user = np.maximum(1, raw_sessions)
    total_sessions = int(sessions_per_user.sum())

    print(f"Generating {total_sessions} sessions")

    session_id = fastuuid.uuid4_as_strings_bulk(total_sessions)
    user_id_fk = np.repeat(user_data["user_id"], sessions_per_user)
    session_number = pd.Series(user_id_fk).groupby(user_id_fk).cumcount() + 1

    # assigns acquisition channel, NOTE: based on digital_literacy
    literacy = np.repeat(user_data["latent_digital_literacy"], sessions_per_user)
    thresholds = SIM_CONFIG["literacy_thresholds"]
    literacy_tier = np.full(total_sessions, "mid", dtype=object)
    literacy_tier[literacy < thresholds[0]] = "low"
    literacy_tier[literacy >= thresholds[1]] = "high"

    literacy_tier_names = list(SIM_CONFIG["channel_weights_by_literacy"].keys())
    acq_channel = np.empty(total_sessions, dtype=object)
    for tier in literacy_tier_names:
        mask = literacy_tier == tier
        acq_channel[mask] = rng.choice(
            SIM_CONFIG["channels"],
            size=mask.sum(),
            p=SIM_CONFIG["channel_weights_by_literacy"][tier],
        )

    utm_source = np.full(total_sessions, None, dtype=object)
    utm_medium = np.full(total_sessions, None, dtype=object)
    utm_campaign = np.full(total_sessions, None, dtype=object)

    utm_maps = SIM_CONFIG["utm_maps"]
    for channel, config in utm_maps.items():
        mask = acq_channel == channel
        n_samples = mask.sum()
        if n_samples > 0:
            utm_source[mask] = rng.choice(
                config["source"], size=n_samples, p=config["source_weights"]
            )
            utm_medium[mask] = rng.choice(
                config["medium"], size=n_samples, p=config["medium_weights"]
            )
            utm_campaign[mask] = rng.choice(
                config["campaign"], size=n_samples, p=config["campaign_weights"]
            )

    is_burst_session = rng.choice(
        [True, False], size=total_sessions, p=SIM_CONFIG["burst_session_weights"]
    )
    burst_days = rng.exponential(
        scale=SIM_CONFIG["average_dropoff"], size=total_sessions
    )
    lifespan_days = np.repeat(user_data["user_tenure_days"], sessions_per_user)
    loyalty_days = rng.uniform(low=0, high=lifespan_days, size=total_sessions)
    raw_days = np.where(is_burst_session, burst_days, loyalty_days)

    random_days_array = np.minimum(raw_days, lifespan_days).astype(int)
    random_seconds_array = np.zeros(total_sessions)

    assigned_behavior = rng.choice(
        SIM_CONFIG["diurnal_behavior_types"],
        size=total_sessions,
        p=SIM_CONFIG["diurnal_behavior_weights"],
    )

    baseline_mask = assigned_behavior == "baseline"
    random_seconds_array[baseline_mask] = (
        rng.uniform(0, 24, size=baseline_mask.sum()) * 3600
    )

    lunch_mask = assigned_behavior == "lunch_rush"
    random_seconds_array[lunch_mask] = (
        rng.normal(loc=12.5, scale=1.2, size=lunch_mask.sum()) * 3600
    )

    evening_mask = assigned_behavior == "evening_rush"
    random_seconds_array[evening_mask] = (
        rng.normal(loc=20.5, scale=2.5, size=evening_mask.sum()) * 3600
    )

    random_seconds_array = (random_seconds_array % (24 * 3600)).astype(int)

    #  NOTE: random days is only limited to 30
    parent_created_at = np.repeat(user_data["account_created_at"], sessions_per_user)
    base_midnight = pd.to_datetime(parent_created_at).floor("D")
    session_start_time = (
        base_midnight
        + pd.to_timedelta(random_days_array, unit="D")
        + pd.to_timedelta(random_seconds_array, unit="s")
    )

    shift_probability = SIM_CONFIG["shift_probability"]
    days = session_start_time.day.to_numpy()

    is_payday = np.isin(days, SIM_CONFIG["payday_dates"])
    should_shift = rng.random(size=total_sessions) < shift_probability
    mask_to_shift = ~is_payday & should_shift

    dist_15 = np.abs(days - 15)
    dist_30 = np.abs(days - 30)
    nearest_payday = np.where(dist_15 <= dist_30, 15, 28)

    days_to_add = nearest_payday - days

    session_start_time = np.where(
        mask_to_shift,
        session_start_time + pd.to_timedelta(days_to_add, unit="D"),
        session_start_time,
    )
    session_start_time = pd.to_datetime(session_start_time)

    # session duration | NOTE: exponential decay is based on digital_literacy
    latent_digital_literacy = np.repeat(
        user_data["latent_digital_literacy"], sessions_per_user
    )
    base_duration = rng.exponential(
        scale=SIM_CONFIG["session_base_max_seconds"], size=total_sessions
    )
    literacy_reduction = (
        latent_digital_literacy * SIM_CONFIG["digital_literacy_reduction"]
    )

    noise = rng.normal(loc=0, scale=30, size=total_sessions)

    # no session is shorter than 10 seconds
    session_duration_seconds = np.maximum(
        SIM_CONFIG["session_base_min_seconds"],
        base_duration - literacy_reduction + noise,
    ).astype(int)

    session_end_time = session_start_time + pd.to_timedelta(
        session_duration_seconds, unit="s"
    )

    # NOTE: generated outliers for duration seconds
    outlier_mask = (
        rng.random(size=total_sessions) < SIM_CONFIG["outlier_rate_session_duration"]
    )
    session_duration_seconds[outlier_mask] = (
        session_duration_seconds[outlier_mask]
        * SIM_CONFIG["outlier_duration_multiplier"]
    ).astype(int)
    session_duration_seconds = session_duration_seconds.tolist()

    income = np.repeat(user_data["latent_income_score"], sessions_per_user)
    income_thresholds = SIM_CONFIG["income_os_thresholds"]
    income_tier = np.full(total_sessions, "mid", dtype=object)
    income_tier[income < income_thresholds[0]] = "low"
    income_tier[income >= income_thresholds[1]] = "high"

    income_tier_names = SIM_CONFIG["os_weights_by_income"]
    device_operating_system = np.empty(total_sessions, dtype=object)
    device_operating_system_version = np.empty(total_sessions, dtype=object)
    device_group = np.where(
        np.isin(device_operating_system, ["android", "ios"]), "mobile", "desktop"
    )

    for tier in income_tier_names:
        mask = income_tier == tier
        device_operating_system[mask] = rng.choice(
            SIM_CONFIG["os_types"],
            size=mask.sum(),
            p=SIM_CONFIG["os_weights_by_income"][tier],
        )

    os_types = SIM_CONFIG["os_types"]
    for os_type in os_types:
        mask = device_operating_system == os_type
        n_samples = mask.sum()
        if n_samples > 0:
            versions = rng.choice(
                SIM_CONFIG[f"{os_type}_software_version"],
                size=n_samples,
                p=SIM_CONFIG[f"{os_type}_software_version_weights"],
            )
            device_operating_system_version[mask] = versions.astype(str)

    df_sessions = pd.DataFrame(
        {
            "session_id": session_id,
            "user_id": user_id_fk,
            "session_number": session_number,
            "acq_channel": acq_channel,
            "utm_source": utm_source,
            "utm_medium": utm_medium,
            "utm_campaign": utm_campaign,
            "session_start_time": session_start_time,
            "session_end_time": session_end_time,
            "session_duration_seconds": session_duration_seconds,
            "device_operating_system": device_operating_system,
            "device_operating_system_version": device_operating_system_version,
            "device_group": device_group,
        }
    )

    print("sessions table generated!")
    return df_sessions
