import fastuuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import SIM_CONFIG


def generate_sessions(df_users: pd.DataFrame, rng: np.random.Generator):
    num_users = len(df_users)
    sessions_per_user = rng.choice(
        SIM_CONFIG["session_count"],
        size=num_users,
        p=SIM_CONFIG["session_count_weights"],
    )
    total_sessions = sessions_per_user.sum()

    print(f"Generating {total_sessions} sessions")

    # match the sessions to the total of users
    exploded_users = df_users.loc[df_users.index.repeat(sessions_per_user)].reset_index(
        drop=True
    )

    # session primary keys
    session_id = fastuuid.uuid7_as_strings_bulk(total_sessions)

    # parent foreign keys
    user_id_fk = exploded_users["user_id"].tolist()

    user_counter = {}
    session_number = []
    for uid in user_id_fk:
        user_counter[uid] = user_counter.get(uid, 0) + 1
        session_number.append(user_counter[uid])

    # session start timestamps (bimodal diurnal peak hours) | NOTE: random days is only limited to 30
    parent_created_at = exploded_users["account_created_at"].tolist()
    base_date = datetime.strptime(SIM_CONFIG["as_of_date"], "%Y-%m-%d")

    lifespan_days = []
    for created in parent_created_at:
        time_delta = base_date - created
        lifespan_days.append(time_delta.days)

    is_burst_session = rng.choice(
        [True, False], size=total_sessions, p=SIM_CONFIG["burst_session_weights"]
    )

    burst_days = rng.exponential(
        scale=SIM_CONFIG["average_dropoff"], size=total_sessions
    )
    loyalty_days = rng.uniform(low=0, high=lifespan_days, size=total_sessions)

    raw_days = np.where(is_burst_session, burst_days, loyalty_days)

    random_days_array = np.minimum(raw_days, lifespan_days).astype(int)

    peak_hours = rng.choice(SIM_CONFIG["peak_hours"], size=total_sessions)
    normal_dist_hours = rng.normal(loc=peak_hours, scale=1.0)
    random_seconds_array = ((normal_dist_hours % 24) * 3600).astype(int)

    # assigns acquisition channel, NOTE: based on digital_literacy
    literacy = exploded_users["latent_digital_literacy"].to_numpy()
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

    session_start_time = []
    for created_date, days, seconds in zip(
        parent_created_at, random_days_array, random_seconds_array
    ):
        start_date = created_date + timedelta(days=int(days), seconds=int(seconds))
        session_start_time.append(start_date)

    session_date = []
    is_weekend = []
    for start_time in session_start_time:
        date_only = start_time.date()
        session_date.append(date_only)
        weekday_num = start_time.weekday()
        is_weekend_value = weekday_num >= 5
        is_weekend.append(is_weekend_value)

    # payday spike: 15th or 30th | NOTE: i'm not sure if this is a correct implementation for this
    payday_dates = SIM_CONFIG["payday_dates"]
    shift_probability = 0.12

    for session_index, session_start in enumerate(session_start_time):
        day_of_month = session_start.day
        is_payday = day_of_month in payday_dates
        if is_payday:
            continue

        should_shift = rng.random() < shift_probability
        if not should_shift:
            continue

        distance_to_15 = abs(day_of_month - 15)
        distance_to_30 = abs(day_of_month - 30)
        if distance_to_15 <= distance_to_30:
            nearest_payday = 15
        else:
            nearest_payday = 30
        try:
            session_start_time[session_index] = session_start.replace(
                day=nearest_payday
            )
        except ValueError:
            session_start_time[session_index] = session_start.replace(
                day=min(nearest_payday, 28)
            )

    # session duration | NOTE: exponential decay is based on digital_literacy
    latent_digital_literacy = exploded_users["latent_digital_literacy"].to_numpy()
    base_duration = rng.exponential(
        scale=SIM_CONFIG["session_base_max_seconds"], size=total_sessions
    )
    literacy_reduction = (
        latent_digital_literacy * SIM_CONFIG["digital_literacy_reduction"]
    )

    # no session is shorter than 10 seconds
    session_duration_seconds = np.maximum(
        SIM_CONFIG["session_base_min_seconds"], base_duration - literacy_reduction
    ).astype(int)

    # NOTE: generated outliers for duration seconds
    outlier_mask = (
        rng.random(size=total_sessions) < SIM_CONFIG["outlier_rate_session_duration"]
    )
    session_duration_seconds[outlier_mask] = (
        session_duration_seconds[outlier_mask]
        * SIM_CONFIG["outlier_duration_multiplier"]
    ).astype(int)
    session_duration_seconds = session_duration_seconds.tolist()

    # device OS versions | NOTE: conditioned on income bracket
    income = exploded_users["latent_income_score"].to_numpy()
    income_thresholds = SIM_CONFIG["income_os_thresholds"]
    income_tier = np.full(total_sessions, "mid", dtype=object)
    income_tier[income < income_thresholds[0]] = "low"
    income_tier[income >= income_thresholds[1]] = "high"

    income_tier_names = list(SIM_CONFIG["os_by_income"].keys())
    base_os = np.empty(total_sessions, dtype=object)
    for tier in income_tier_names:
        mask = income_tier == tier
        base_os[mask] = rng.choice(
            SIM_CONFIG["os_distribution"],
            size=mask.sum(),
            p=SIM_CONFIG["os_by_income"][tier],
        )

    device_os_version = []
    device_group = []
    for os_type in base_os:
        if os_type == "Android":
            version = rng.choice(
                SIM_CONFIG["android_software_version"],
                p=SIM_CONFIG["android_software_version_weights"],
            )
            device_os_version.append(f"{os_type} {version}")
            device_group.append("Mobile")

        elif os_type == "iOS":
            version = rng.choice(
                SIM_CONFIG["ios_software_version"],
                p=SIM_CONFIG["ios_software_version_weights"],
            )
            device_os_version.append(f"{os_type} {version}")
            device_group.append("Mobile")
        elif os_type == "Windows":
            version = rng.choice(
                SIM_CONFIG["windows_software_version"],
                p=SIM_CONFIG["windows_software_version_weights"],
            )
            device_os_version.append(f"{os_type} {version}")
            device_group.append("Desktop")

        else:
            version = rng.choice(
                SIM_CONFIG["macos_software_version"],
            )
            device_os_version.append(f"{os_type} {version}")
            device_group.append("Desktop")

    # turn into dataframe (pandas)
    df_sessions = pd.DataFrame(
        {
            "session_id": session_id,
            "user_id": user_id_fk,
            "session_number": session_number,
            "acquisition_channel": acq_channel,
            "session_start_time": session_start_time,
            "session_date": session_date,
            "is_weekend": is_weekend,
            "session_duration_seconds": session_duration_seconds,
            "device_os_version": device_os_version,
            "device_group": device_group,
        }
    )

    print("sessions table generated!")
    return df_sessions
