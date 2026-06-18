import fastuuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import SIM_CONFIG


def generate_users(total_users: int, rng: np.random.Generator):
    print(f"Generating {total_users} users")

    # user primary keys
    user_id = fastuuid.uuid7_as_strings_bulk(total_users)

    # account created timestamps
    base_date = datetime.strptime(SIM_CONFIG["as_of_date"], "%Y-%m-%d")
    days_ago_array = rng.integers(0, 365, size=total_users)
    seconds_ago_array = rng.integers(0, 86400, size=total_users)

    created_at = []
    for days, seconds in zip(days_ago_array, seconds_ago_array):
        past_date = base_date - timedelta(days=int(days), seconds=int(seconds))
        created_at.append(past_date)

    # engine for latent variables (numpy) | creates a gaussian distribution
    latent_income_score = rng.normal(loc=0, scale=1.0, size=total_users)
    latent_digital_literacy = rng.uniform(low=0, high=1.0, size=total_users)
    latent_trust_in_platform = rng.beta(a=2, b=5, size=total_users)

    region_names = list(SIM_CONFIG["regions"].keys())

    region_weights = []
    for region_name in region_names:
        weight = SIM_CONFIG["regions"][region_name]["weight"]
        region_weights.append(weight)
    region = rng.choice(region_names, size=total_users, p=region_weights)

    # number of days a user has been active since first visit or purchase
    user_tenure_days = days_ago_array

    city = []
    for chosen_region in region:
        region_info = SIM_CONFIG["regions"][chosen_region]
        chosen_city = rng.choice(region_info["cities"], p=region_info["city_weights"])
        city.append(chosen_city)

    # turn into dataframe (pandas)
    df_users = pd.DataFrame(
        {
            "user_id": user_id,
            "account_created_at": created_at,
            "city": city,
            "region": region,
            "user_tenure_days": user_tenure_days,
            "latent_income_score": latent_income_score,
            "latent_digital_literacy": latent_digital_literacy,
            "latent_trust_in_platform": latent_trust_in_platform,
        }
    )

    print("users tables generated!")
    return df_users
