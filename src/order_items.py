import fastuuid
import pandas as pd
import numpy as np
from config import SIM_CONFIG


def generate_order_items(
    df_orders: pd.DataFrame, df_users: pd.DataFrame, rng: np.random.Generator
):
    print(f"Generating order items for {len(df_orders)} orders")

    working_df = df_orders.merge(
        df_users[["user_id", "latent_income_score"]], on="user_id", how="left"
    )

    num_orders = len(working_df)

    items_per_order = rng.choice(
        SIM_CONFIG["items_per_order_counts"],
        size=num_orders,
        p=SIM_CONFIG["items_per_order_weights"],
    )
    total_items = items_per_order.sum()

    exploded_orders = working_df.loc[
        working_df.index.repeat(items_per_order)
    ].reset_index(drop=True)

    item_id_list = fastuuid.uuid4_as_strings_bulk(total_items)

    item_order_fk = exploded_orders["order_id"].tolist()

    n_items = int(total_items)

    is_discounted = rng.random(size=total_items) < SIM_CONFIG["promo_code_probability"]
    num_tiers = len(SIM_CONFIG["promo_discount_tiers"])

    tier_indices = rng.choice(
        num_tiers,
        size=n_items,
        p=SIM_CONFIG["promo_discount_weights"],
    )

    percentages = np.array(SIM_CONFIG["promo_discount_tiers"])[tier_indices]
    caps = np.array(SIM_CONFIG["promo_discount_caps"])[tier_indices]

    actual_discount_pct = np.where(is_discounted, percentages, 0.0)
    actual_discount_cap = np.where(is_discounted, caps, 0.0)

    base_quantity = rng.choice(
        SIM_CONFIG["item_quantity_counts"],
        size=total_items,
        p=SIM_CONFIG["item_quantity_weights"],
    )

    promo_volume_uplift = rng.poisson(lam=(actual_discount_pct * 2.5))
    item_quantity = base_quantity + promo_volume_uplift

    item_category = rng.choice(
        SIM_CONFIG["item_categories"],
        size=total_items,
        p=SIM_CONFIG["item_category_weights"],
    )
    base_prices = (
        pd.Series(item_category).map(SIM_CONFIG["category_base_prices"]).to_numpy()
    )
    income_scores = exploded_orders["latent_income_score"].to_numpy()

    mu_base = np.log(base_prices)
    mu_adjusted = mu_base + (income_scores * 0.10)

    raw_prices = rng.lognormal(mean=mu_adjusted, sigma=0.85, size=total_items)
    base_item_price = np.floor(np.maximum(9.99, raw_prices)) + 0.99

    outlier_mask = rng.random(size=total_items) < SIM_CONFIG["outlier_rate_item_price"]
    outlier_multipliers = rng.uniform(3.0, 8.0, size=outlier_mask.sum())

    base_item_price[outlier_mask] = (
        base_item_price[outlier_mask] * outlier_multipliers
    ).round(2)

    raw_discounted_price = base_item_price * actual_discount_pct
    discount_amount = np.minimum(raw_discounted_price, actual_discount_cap)

    discounted_prices = base_item_price - discount_amount
    final_item_price = np.maximum(4.99, discounted_prices).round(2)

    df_order_items = pd.DataFrame(
        {
            "order_item_id": item_id_list,
            "order_id": item_order_fk,
            "item_category": item_category,
            "base_item_price": base_item_price,
            "final_item_price": final_item_price,
            "quantity": item_quantity,
            "promo_tier_percentage": actual_discount_pct,
            "discount_amount": discount_amount,
        }
    )

    df_order_items["item_category"] = df_order_items["item_category"].astype("category")

    print("order items table generated!")
    return df_order_items
