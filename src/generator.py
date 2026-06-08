import pandas as pd
import numpy as np
import uuid
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
    # add more specs here, according to the document
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
    # calculates total sessions | NOTE: 1 to 5 sessions per user, might change
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
    user_id = exploded_users["user_id"].tolist()

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
            "user_id": user_id,
            "session_start_time": session_start_time,
            "session_duration_seconds": session_duration_seconds,
            "device_os_version": device_os_version,
        }
    )

    print("session table generated!")
    return df_sessions


# TEST: FOR TESTING ONLY
if __name__ == "__main__":
    test_users_df = generate_users(20)
    test_sessions_df = generate_sessions(test_users_df)

    print("\nTEST: GENERATED USERS")
    print(test_users_df)

    print("\nTEST: GENERATED SESSIONS")
    print(test_sessions_df)

    print("\nTEST: DATA TYPES")
    print(test_users_df.dtypes)
