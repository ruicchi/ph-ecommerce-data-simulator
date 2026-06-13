import uuid
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import SIM_CONFIG


def generate_users(total_users: int, rng: np.random.Generator):
    print(f"Generating {total_users} users")

    # user primary keys
    user_ids = []
    for _ in range(total_users):
        new_id = str(uuid.uuid4())
        user_ids.append(new_id)

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
            "latent_income_score": latent_income_score,
            "latent_tech_savviness": latent_tech_savviness,
        }
    )

    print("users tables generated!")
    return df_users
