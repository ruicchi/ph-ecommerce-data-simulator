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
    "android_share": 0.65,
    "ios_share": 0.35,
    "session_base_max_seconds": 300,
    "savviness_time_reduction": 150,
    "android_error_rate": 0.05,
    "android_error_string": "ERR_VERSION_NOT_FOUND",
    # add markov chain probs here later...
}


def generate_users(num_users):
    print(f"Generating {num_users} users")

    # user primary keys
    user_ids = []
    for _ in range(num_users):
        new_id = str(uuid.uuid4())
        user_ids.append(new_id)

    # assigns hardware whether android or ios
    hardware = rng.choice(
        ["Android", "iOS"],
        size=num_users,
        p=[SIM_CONFIG["android_share"], SIM_CONFIG["ios_share"]],
    )

    # account created timestamps
    base_date = datetime.strptime(SIM_CONFIG["as_of_date"], "%Y-%m-%d")
    days_ago_array = rng.integers(0, 365, size=num_users)

    created_at = []
    for days in days_ago_array:
        past_date = base_date - timedelta(days=int(days))
        created_at.append(past_date)

    # engine for latent variables (numpy) | creates a gaussian distribution
    latent_income_score = rng.normal(loc=0, scale=1.0, size=num_users)
    latent_tech_savviness = rng.uniform(low=0, high=1.0, size=num_users)

    # turn into dataframe (pandas)
    df_users = pd.DataFrame(
        {
            "user_id": user_ids,
            "signup_hardware": hardware,
            "account_created_at": created_at,
            "latent_income_score": latent_income_score,
            "latent_tech_savviness": latent_tech_savviness,
        }
    )

    print("users tables generated!")
    return df_users


# TEST: FOR TESTING ONLY
if __name__ == "__main__":
    test_df = generate_users(10)

    print("\n TEST: GENERATED USERS")
    print(test_df)

    print("\n TEST: DATA TYPES")
    print(test_df.dtypes)
