# NOTE: this will change, depending on the configurables based on the funnel optimization analyst
SIM_CONFIG = {
    "random_seed": 42,
    "as_of_date": "2023-12-31",
    "target_users": 1000000,
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
    "os_by_income": {
        "low": [0.55, 0.20, 0.15, 0.10],
        "mid": [0.38, 0.25, 0.20, 0.17],
        "high": [0.25, 0.30, 0.25, 0.20],
    },
    "income_os_thresholds": [-0.44, 0.44],
    "android_software_version": [0.50, 0.30, 0.15, 0.05],
    "android_software_version_weights": [0.5, 0.3, 0.15, 0.05],
    "ios_software_version": ["17.3", "16.5", "15.2"],
    "ios_software_version_weights": [0.6, 0.3, 0.1],
    "windows_software_version": ["11", "10"],
    "windows_software_version_weights": [0.7, 0.3],
    "macos_software_version": ["Sonoma", "Ventura", "Monterey"],
    "digital_literacy_reduction": 150,
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
    "payment_methods": ["COD", "GCash", "Maya", "Credit Card", "Bank Transfer"],
    "payment_method_weights": [0.25, 0.25, 0.25, 0.15, 0.10],
    # data degredation
    # duplicate rate
    "dup_rate_events": 0.005,
    # outlier rates
    "outlier_rate_session_duration": 0.01,
    "outlier_duration_multiplier": 10,
    "outlier_rate_item_price": 0.005,
    "outlier_price_multiplier": 100,
    "channel_weights_by_literacy": {
        "low": [0.50, 0.20, 0.25, 0.05],
        "mid": [0.38, 0.32, 0.18, 0.12],
        "high": [0.25, 0.35, 0.10, 0.30],
    },
    "literacy_thresholds": [0.33, 0.67],
    "payday_dates": [15, 30],
    "payday_boost": 1.3,
    "regions": {
        "NCR": {
            "weight": 0.35,
            "cities": ["Manila", "Quezon City", "Makati", "Taguig"],
            "city_weights": [0.35, 0.30, 0.20, 0.15],
        },
        "Region IV-A": {
            "weight": 0.18,
            "cities": ["Laguna", "Cavite", "Batangas"],
            "city_weights": [0.40, 0.35, 0.25],
        },
        "Region III": {
            "weight": 0.10,
            "cities": ["Bulacan", "Pampanga"],
            "city_weights": [0.55, 0.45],
        },
        "Region VII": {"weight": 0.12, "cities": ["Cebu City"], "city_weights": [1.0]},
        "Region XI": {"weight": 0.08, "cities": ["Davao City"], "city_weights": [1.0]},
        "Region VI": {
            "weight": 0.06,
            "cities": ["Iloilo", "Bacolod"],
            "city_weights": [0.55, 0.45],
        },
        "CAR": {"weight": 0.03, "cities": ["Baguio"], "city_weights": [1.0]},
        "Region X": {
            "weight": 0.05,
            "cities": ["Cagayan de Oro"],
            "city_weights": [1.0],
        },
        "Region IX": {
            "weight": 0.03,
            "cities": ["Zamboanga City"],
            "city_weights": [1.0],
        },
    },
}
