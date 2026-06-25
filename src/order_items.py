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

    item_id_list = fastuuid.uuid7_as_strings_bulk(total_items)

    item_order_fk = exploded_orders["order_id"].tolist()

    item_quantity = rng.choice(
        SIM_CONFIG["item_quantity_counts"],
        size=total_items,
        p=SIM_CONFIG["item_quantity_weights"],
    )

    item_category = rng.choice(
        SIM_CONFIG["product_categories"],
        size=total_items,
        p=SIM_CONFIG["product_category_weights"],
    )
    base_prices = (
        pd.Series(item_category).map(SIM_CONFIG["category_base_prices"]).to_numpy()
    )
    is_discounted = rng.random(size=total_items) < SIM_CONFIG["promo_code_probability"]
    discount_tiers = rng.choice(
        SIM_CONFIG["promo_discount_tiers"],
        size=total_items,
        p=SIM_CONFIG["promo_discount_weights"],
    )
    actual_discount = np.where(is_discounted, discount_tiers, 0.0)

    income_scores = exploded_orders["latent_income_score"].to_numpy()
    noise = rng.normal(0, 10, size=total_items)
    raw_prices = base_prices + (income_scores * 20) + noise
    base_item_price = np.floor(np.maximum(9.99, raw_prices)) + 0.99
    discounted_prices = base_item_price * (1.0 - actual_discount)
    final_item_price = np.maximum(4.99, discounted_prices).round(2)

    outlier_mask = rng.random(size=total_items) < SIM_CONFIG["outlier_rate_item_price"]
    final_item_price[outlier_mask] = (
        final_item_price[outlier_mask] * SIM_CONFIG["outlier_price_multiplier"]
    ).round(2)

    df_order_items = pd.DataFrame(
        {
            "order_item_id": item_id_list,
            "order_id": item_order_fk,
            "product_category": item_category,
            "base_item_price": base_item_price,
            "final_item_price": final_item_price,
            "quantity": item_quantity,
            "discount_percentage": actual_discount,
        }
    )

    df_order_items["product_category"] = df_order_items["product_category"].astype(
        "category"
    )

    print("order items table generated!")
    return df_order_items
