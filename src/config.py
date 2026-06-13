# NOTE: this will change, depending on the configurables based on the funnel optimization analyst
SIM_CONFIG = {
    "random_seed": 42,
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
    # events config
    "event_spacing_scale_seconds": 30,
    "base_transactions": {
        # if user is viewing an item
        "view_item": {"view_item": 0.40, "add_to_cart": 0.30, "drop_off": 0.30},
        # if user added to cart
        "add_to_cart": {"view_item": 0.20, "begin_checkout": 0.50, "drop_off": 0.30},
        # if user begins checkout
        "begin_checkout": {"purchase": 0.40, "drop_off": 0.60},
        # end states (if user purchases or drop off, session is over
        "purchase": {"drop_off": 1.0},
        "drop_off": {"drop_off": 1.0},
    },
    "items_per_order_counts": [1, 2, 3, 4, 5],
    "items_per_order_weights": [0.50, 0.30, 0.10, 0.05, 0.05],
    "item_quantity_counts": [1, 2, 3, 5],
    "item_quantity_weights": [0.85, 0.10, 0.04, 0.01],
    "product_categories": ["Apparel", "Electronics", "Home Goods", "Consumables"],
    "product_category_weights": [0.50, 0.20, 0.15, 0.15],
    "category_base_prices": {
        "Apparel": 35.00,
        "Electronics": 250.00,
        "Home Goods": 85.00,
        "Consumables": 15.00,
    },
    "promo_code_probability": 0.25,
    "promo_discount_tiers": [0.10, 0.15, 0.20, 0.50],
    "promo_discount_weights": [0.50, 0.30, 0.15, 0.05],
}
