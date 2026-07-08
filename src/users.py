import fastuuid
import pandas as pd
import numpy as np
from config import SIM_CONFIG


def generate_users(total_users: int, rng: np.random.Generator):
    print(f"Generating {total_users} users")

    user_id = fastuuid.uuid4_as_strings_bulk(total_users)

    base_date = pd.to_datetime(SIM_CONFIG["as_of_date"])
    raw_tenure = rng.lognormal(mean=5.19, sigma=1.2, size=total_users)
    user_tenure_days = np.clip(np.floor(raw_tenure), 1, 2000).astype(int)
    seconds_ago_array = rng.integers(0, 86400, size=total_users)

    user_first_touch_timestamp = (
        base_date
        - pd.to_timedelta(user_tenure_days, unit="D")
        - pd.to_timedelta(seconds_ago_array, unit="s")
    )

    latent_income_score = rng.lognormal(mean=0, sigma=1.0, size=total_users)
    latent_digital_literacy = rng.uniform(low=0, high=1.0, size=total_users)
    latent_trust_in_platform = rng.beta(a=2, b=5, size=total_users)

    region_names = list(SIM_CONFIG["regions"].keys())

    region_weights = []
    for region_name in region_names:
        weight = SIM_CONFIG["regions"][region_name]["weight"]
        region_weights.append(weight)
    region = rng.choice(region_names, size=total_users, p=region_weights)

    city = []
    for chosen_region in region:
        region_info = SIM_CONFIG["regions"][chosen_region]
        chosen_city = rng.choice(region_info["cities"], p=region_info["city_weights"])
        city.append(chosen_city)

    df_users = pd.DataFrame(
        {
            "user_id": user_id,
            "account_created_at": user_first_touch_timestamp,
            "city": city,
            "region": region,
            "user_tenure_days": user_tenure_days,
            "latent_income_score": latent_income_score,
            "latent_digital_literacy": latent_digital_literacy,
            "latent_trust_in_platform": latent_trust_in_platform,
        }
    )

    print("users table generated!")
    return df_users
