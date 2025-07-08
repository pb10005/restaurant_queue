"""
飲食店待ち行列シミュレーションのパラメータ定義
"""

# 0除算防止用の極小値定数
EPSILON = 1e-10  # 非常に小さい値

# シミュレーションパラメータ
SEATS = 20  # 席数
OPENING_HOUR = 11  # 開店時間（時）
CLOSING_HOUR = 22  # 閉店時間（時）
KITCHEN_STAFF = 2  # 調理スタッフ数
HALL_STAFF = 3  # ホールスタッフ数

# メニュー設定
MENU = {
    "ラーメン": {
        "price": 800,
        "cooking_time_mean": 10,  # 分
        "cooking_time_std": 2,    # 分
        "ingredients": {
            "麺": 1,
            "スープ": 1,
            "チャーシュー": 2,
            "ネギ": 0.1
        }
    },
    "餃子": {
        "price": 500,
        "cooking_time_mean": 8,
        "cooking_time_std": 1,
        "ingredients": {
            "餃子の皮": 6,
            "餃子の具": 0.2,
            "ニンニク": 0.05
        }
    },
    "チャーハン": {
        "price": 700,
        "cooking_time_mean": 7,
        "cooking_time_std": 1,
        "ingredients": {
            "米": 1,
            "卵": 1,
            "チャーシュー": 1,
            "ネギ": 0.05
        }
    },
    "唐揚げ": {
        "price": 600,
        "cooking_time_mean": 12,
        "cooking_time_std": 2,
        "ingredients": {
            "鶏肉": 0.3,
            "ニンニク": 0.02,
            "油": 0.1
        }
    },
    "ビール": {
        "price": 500,
        "cooking_time_mean": 1,
        "cooking_time_std": 0.5,
        "ingredients": {
            "ビール": 1
        }
    }
}

# 材料設定
INGREDIENTS = {
    "麺": {"initial_stock": 100, "cost": 100},
    "スープ": {"initial_stock": 80, "cost": 150},
    "チャーシュー": {"initial_stock": 50, "cost": 300},
    "ネギ": {"initial_stock": 20, "cost": 100},
    "餃子の皮": {"initial_stock": 300, "cost": 50},
    "餃子の具": {"initial_stock": 30, "cost": 200},
    "ニンニク": {"initial_stock": 10, "cost": 100},
    "米": {"initial_stock": 100, "cost": 80},
    "卵": {"initial_stock": 50, "cost": 20},
    "鶏肉": {"initial_stock": 30, "cost": 400},
    "油": {"initial_stock": 20, "cost": 200},
    "ビール": {"initial_stock": 100, "cost": 200}
}

# 顧客生成パラメータ
CUSTOMER_PARAMS = {
    "weekday": {
        "lunch": {"mean_interval": 2, "group_size_probs": [0.4, 0.4, 0.15, 0.05]},
        "dinner": {"mean_interval": 4, "group_size_probs": [0.3, 0.4, 0.2, 0.1]}
    },
    "weekend": {
        "lunch": {"mean_interval": 2, "group_size_probs": [0.3, 0.35, 0.25, 0.1]},
        "dinner": {"mean_interval": 1, "group_size_probs": [0.2, 0.3, 0.3, 0.2]}
    }
}

# 天候影響係数
WEATHER_FACTORS = {
    "sunny": 1.0,
    "cloudy": 0.9,
    "rainy": 0.7,
    "snowy": 0.5
}
