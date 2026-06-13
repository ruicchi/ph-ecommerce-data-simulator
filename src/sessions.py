import uuid
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

    # assigns acquisition channel
    acq_channel = rng.choice(
        SIM_CONFIG["channels"], size=len(session_id), p=SIM_CONFIG["channel_weights"]
    )

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
            "acquisition_channel": acq_channel,
            "session_start_time": session_start_time,
            "session_duration_seconds": session_duration_seconds,
            "device_os_version": device_os_version,
        }
    )

    print("sessions table generated!")
    return df_sessions
