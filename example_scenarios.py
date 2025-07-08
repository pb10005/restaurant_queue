"""
飲食店待ち行列シミュレーションの異なるシナリオ例
"""

import copy
from restaurant_simulation import (
    SEATS, OPENING_HOUR, CLOSING_HOUR, KITCHEN_STAFF, HALL_STAFF,
    MENU, INGREDIENTS, CUSTOMER_PARAMS, WEATHER_FACTORS,
    Restaurant, customer_generator, analyze_results
)
import simpy

def run_scenario(name, seats=None, kitchen_staff=None, hall_staff=None, 
                 ingredients_multiplier=None, weather=None):
    """異なるパラメータでシミュレーションを実行"""
    print(f"\n\n{'='*50}")
    print(f"シナリオ: {name}")
    print(f"{'='*50}")
    
    # パラメータの設定
    actual_seats = seats if seats is not None else SEATS
    actual_kitchen_staff = kitchen_staff if kitchen_staff is not None else KITCHEN_STAFF
    actual_hall_staff = hall_staff if hall_staff is not None else HALL_STAFF
    
    # 材料の在庫を調整
    actual_ingredients = copy.deepcopy(INGREDIENTS)
    if ingredients_multiplier is not None:
        for ing_name in actual_ingredients:
            actual_ingredients[ing_name]["initial_stock"] = int(
                actual_ingredients[ing_name]["initial_stock"] * ingredients_multiplier
            )
    
    # 天候スケジュール
    weather_schedule = {0: weather} if weather else {0: "sunny"}
    
    # シミュレーション環境の設定
    env = simpy.Environment()
    
    # レストランの初期化
    restaurant = Restaurant(
        env=env,
        seats=actual_seats,
        menu_items=MENU,
        ingredients_data=actual_ingredients,
        opening_hour=OPENING_HOUR,
        closing_hour=CLOSING_HOUR,
        kitchen_staff=actual_kitchen_staff,
        hall_staff=actual_hall_staff
    )
    
    # 顧客生成プロセスの開始
    env.process(customer_generator(env, restaurant, CUSTOMER_PARAMS, weather_schedule))
    
    # シミュレーション実行（1日分）
    env.run(until=24*60)  # 24時間（分単位）
    
    # 材料使用状況を記録
    restaurant.metrics.record_ingredient_usage(restaurant.ingredients)
    
    # 材料コストを計算
    for ing in restaurant.ingredients.values():
        restaurant.metrics.record_cost(ing.used_amount * ing.cost)
    
    # 結果の分析
    analyze_results(restaurant.metrics)
    
    return restaurant.metrics

def main():
    """異なるシナリオを実行"""
    # 基本シナリオ
    base_metrics = run_scenario("基本シナリオ")
    
    # 席数を増やしたシナリオ
    more_seats_metrics = run_scenario("席数増加シナリオ", seats=30)
    
    # スタッフを増やしたシナリオ
    more_staff_metrics = run_scenario("スタッフ増加シナリオ", kitchen_staff=3, hall_staff=4)
    
    # 材料在庫を減らしたシナリオ
    less_ingredients_metrics = run_scenario("材料在庫減少シナリオ", ingredients_multiplier=0.5)
    
    # 雨の日シナリオ
    rainy_day_metrics = run_scenario("雨の日シナリオ", weather="rainy")
    
    # 結果の比較
    print("\n\n" + "="*50)
    print("シナリオ比較")
    print("="*50)
    
    scenarios = [
        ("基本シナリオ", base_metrics),
        ("席数増加シナリオ", more_seats_metrics),
        ("スタッフ増加シナリオ", more_staff_metrics),
        ("材料在庫減少シナリオ", less_ingredients_metrics),
        ("雨の日シナリオ", rainy_day_metrics)
    ]
    
    print("\n【総売上比較】")
    for name, metrics in scenarios:
        print(f"{name}: {metrics.total_revenue:.0f}円")
    
    print("\n【純利益比較】")
    for name, metrics in scenarios:
        print(f"{name}: {metrics.total_profit:.0f}円")
    
    print("\n【最大待ち行列長比較】")
    for name, metrics in scenarios:
        print(f"{name}: {metrics.max_queue_length}組")
    
    print("\n【キャンセル率比較】")
    for name, metrics in scenarios:
        print(f"{name}: {metrics.walkout_rate * 100:.1f}%")
    
    print("\n【材料廃棄率比較】")
    for name, metrics in scenarios:
        print(f"{name}: {metrics.ingredient_wastage * 100:.1f}%")

if __name__ == "__main__":
    main()
