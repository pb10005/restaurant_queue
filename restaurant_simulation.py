import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib  # 日本語フォントのサポート
import random
from datetime import datetime, timedelta
import collections

# シミュレーションパラメータをインポート
from simulation_parameters import (
    EPSILON, SEATS, OPENING_HOUR, CLOSING_HOUR, KITCHEN_STAFF, HALL_STAFF,
    MENU, INGREDIENTS, CUSTOMER_PARAMS, WEATHER_FACTORS
)

class Ingredient:
    """材料クラス"""
    def __init__(self, name, initial_stock, cost):
        self.name = name
        self.initial_stock = initial_stock
        self.current_stock = initial_stock
        self.cost = cost
        self.used_amount = 0
    
    def use(self, amount):
        """材料を使用"""
        if self.current_stock >= amount:
            self.current_stock -= amount
            self.used_amount += amount
            return True
        return False
    
    def is_available(self, amount):
        """必要量が在庫にあるか確認"""
        return self.current_stock >= amount

class Menu:
    """メニュークラス"""
    def __init__(self, items):
        self.items = items
    
    def get_price(self, item_name):
        """料理の価格を取得"""
        return self.items[item_name]["price"]
    
    def get_cooking_time(self, item_name):
        """料理の調理時間を取得（分布からサンプリング）"""
        mean = self.items[item_name]["cooking_time_mean"]
        std = self.items[item_name]["cooking_time_std"]
        return max(1, np.random.normal(mean, std))
    
    def get_ingredients(self, item_name):
        """料理に必要な材料を取得"""
        return self.items[item_name]["ingredients"]
    
    def get_available_items(self, ingredients):
        """在庫のある料理のリストを取得"""
        available = []
        for item_name in self.items:
            can_make = True
            for ing_name, amount in self.items[item_name]["ingredients"].items():
                if not ingredients[ing_name].is_available(amount):
                    can_make = False
                    break
            if can_make:
                available.append(item_name)
        return available

class Customer:
    """顧客クラス"""
    def __init__(self, env, group_size, patience):
        self.env = env
        self.group_size = group_size
        self.patience = patience  # 待てる最大時間（分）
        self.arrival_time = None
        self.seating_time = None
        self.departure_time = None
        self.orders = []
        self.is_seated = False
        self.walked_out = False
    
    def decide_orders(self, menu, available_items):
        """注文を決定"""
        # 簡易的な実装: 各人がランダムに1品注文
        possible_orders = []
        for _ in range(self.group_size):
            if available_items:
                possible_orders.append(random.choice(available_items))
        return possible_orders

class SimulationMetrics:
    """シミュレーション指標クラス"""
    def __init__(self):
        self.total_revenue = 0
        self.total_cost = 0
        self.customer_data = []
        self.queue_length_over_time = []
        self.seated_customers_over_time = []
        self.stockouts = collections.Counter()
        self.walkouts = 0
        self.total_customers = 0
        self.max_queue_length = 0
        self.ingredient_usage = {}
        self.hourly_metrics = {
            "revenue": collections.defaultdict(float),
            "customers": collections.defaultdict(int),
            "walkouts": collections.defaultdict(int)
        }
    
    def record_arrival(self, customer, time, queue_length):
        """顧客到着を記録"""
        self.total_customers += 1
        self.max_queue_length = max(self.max_queue_length, queue_length)
        self.queue_length_over_time.append((time, queue_length))
        hour = int(time / 60)
        self.hourly_metrics["customers"][hour] += 1
    
    def record_seating(self, customer, time, seated_count):
        """着席を記録"""
        self.seated_customers_over_time.append((time, seated_count))
    
    def record_revenue(self, amount, time):
        """売上を記録"""
        self.total_revenue += amount
        hour = int(time / 60)
        self.hourly_metrics["revenue"][hour] += amount
    
    def record_cost(self, amount):
        """コストを記録"""
        self.total_cost += amount
    
    def record_departure(self, customer, time):
        """退店を記録"""
        waiting_time = customer.seating_time - customer.arrival_time if customer.seating_time else 0
        dining_time = customer.departure_time - customer.seating_time if customer.seating_time else 0
        
        self.customer_data.append({
            "group_size": customer.group_size,
            "arrival_time": customer.arrival_time,
            "seating_time": customer.seating_time,
            "departure_time": customer.departure_time,
            "waiting_time": waiting_time,
            "dining_time": dining_time,
            "orders": customer.orders,
            "walked_out": customer.walked_out
        })
    
    def record_walkout(self, customer, time):
        """待ちきれずに帰った顧客を記録"""
        self.walkouts += 1
        customer.walked_out = True
        hour = int(time / 60)
        self.hourly_metrics["walkouts"][hour] += 1
        self.record_departure(customer, time)
    
    def record_stockout(self, item_name):
        """品切れを記録"""
        self.stockouts[item_name] += 1
    
    def record_ingredient_usage(self, ingredients):
        """材料使用量を記録"""
        self.ingredient_usage = {
            ing.name: {
                "initial": ing.initial_stock,
                "remaining": ing.current_stock,
                "used": ing.used_amount,
                "usage_rate": ing.used_amount / ing.initial_stock if ing.initial_stock > EPSILON else 0,
                "cost": ing.cost * ing.used_amount
            }
            for ing in ingredients.values()
        }
    
    def calculate_metrics(self):
        """各種指標を計算"""
        # 顧客データをDataFrameに変換
        if self.customer_data:
            df = pd.DataFrame(self.customer_data)
            
            # 待ち時間関連
            seated_customers = df[~df["walked_out"]]
            if not seated_customers.empty:
                self.avg_waiting_time = seated_customers["waiting_time"].mean()
                self.avg_dining_time = seated_customers["dining_time"].mean()
            else:
                self.avg_waiting_time = 0
                self.avg_dining_time = 0
            
            # 経済指標
            self.total_profit = self.total_revenue - self.total_cost
            
            # 顧客体験
            self.walkout_rate = self.walkouts / self.total_customers if self.total_customers > EPSILON else 0
            
            # 在庫管理
            self.stockout_rate = sum(self.stockouts.values()) / len(self.stockouts) if self.stockouts else 0
            
            # 材料廃棄率
            wastage = sum(
                (ing["initial"] - ing["used"]) * ing["cost"] / (ing["initial"] * ing["cost"]) 
                for ing in self.ingredient_usage.values() 
                if ing["initial"] > EPSILON and ing["cost"] > EPSILON
            ) / len(self.ingredient_usage) if self.ingredient_usage else 0
            self.ingredient_wastage = wastage
        else:
            # データがない場合のデフォルト値
            self.avg_waiting_time = 0
            self.avg_dining_time = 0
            self.total_profit = -self.total_cost
            self.walkout_rate = 0
            self.stockout_rate = 0
            self.ingredient_wastage = 0

class Restaurant:
    """レストランクラス"""
    def __init__(self, env, seats, menu_items, ingredients_data, opening_hour, closing_hour, kitchen_staff, hall_staff):
        self.env = env
        self.seats = seats
        self.available_seats = seats
        self.waiting_line = []
        self.seated_customers = []
        
        # 営業時間（分単位）
        self.opening_time = opening_hour * 60
        self.closing_time = closing_hour * 60
        
        # スタッフ
        self.kitchen_staff = simpy.Resource(env, capacity=kitchen_staff)
        self.hall_staff = simpy.Resource(env, capacity=hall_staff)
        
        # メニューと材料
        self.ingredients = {
            name: Ingredient(name, data["initial_stock"], data["cost"])
            for name, data in ingredients_data.items()
        }
        self.menu = Menu(menu_items)
        
        # 指標
        self.metrics = SimulationMetrics()
    
    def is_open(self, time):
        """営業中かどうか確認"""
        return self.opening_time <= time < self.closing_time
    
    def can_prepare(self, item_name):
        """料理が作れるか確認（材料の在庫チェック）"""
        for ing_name, amount in self.menu.get_ingredients(item_name).items():
            if not self.ingredients[ing_name].is_available(amount):
                return False
        return True
    
    def reserve_ingredients(self, item_name):
        """材料を予約（使用）"""
        for ing_name, amount in self.menu.get_ingredients(item_name).items():
            self.ingredients[ing_name].use(amount)
    
    def seat_customer(self, customer):
        """顧客を席に案内"""
        if self.available_seats >= customer.group_size:
            self.available_seats -= customer.group_size
            customer.is_seated = True
            customer.seating_time = self.env.now
            self.seated_customers.append(customer)
            self.waiting_line.remove(customer)
            self.metrics.record_seating(customer, self.env.now, len(self.seated_customers))
            return True
        return False
    
    def release_seating(self, customer):
        """席を解放"""
        self.available_seats += customer.group_size
        self.seated_customers.remove(customer)
        self.metrics.record_seating(None, self.env.now, len(self.seated_customers))
    
    def cook(self, item_name):
        """料理を調理するプロセス"""
        cooking_time = self.menu.get_cooking_time(item_name)
        return cooking_time

def customer_behavior(env, customer, restaurant):
    """顧客の行動プロセス"""
    # 到着
    customer.arrival_time = env.now
    restaurant.waiting_line.append(customer)
    restaurant.metrics.record_arrival(customer, env.now, len(restaurant.waiting_line))
    
    # 席が空くか、忍耐が尽きるまで待機
    patience_end = env.now + customer.patience
    
    while env.now < patience_end and not customer.is_seated:
        # 席が空いているか確認
        if restaurant.seat_customer(customer):
            break
        
        # 1分待機
        yield env.timeout(1)
        
        # 忍耐が尽きた場合
        if env.now >= patience_end and not customer.is_seated:
            restaurant.metrics.record_walkout(customer, env.now)
            return
    
    # 着席できなかった場合
    if not customer.is_seated:
        return
    
    # 注文
    yield env.timeout(random.uniform(2, 5))  # メニュー検討時間
    
    # 注文可能なメニューを確認
    available_items = restaurant.menu.get_available_items(restaurant.ingredients)
    customer.orders = customer.decide_orders(restaurant.menu, available_items)
    
    # 注文がない場合（全て品切れなど）
    if not customer.orders:
        customer.departure_time = env.now
        restaurant.metrics.record_departure(customer, env.now)
        restaurant.release_seating(customer)
        return
    
    # 注文した料理の材料を使用
    for item in customer.orders:
        restaurant.reserve_ingredients(item)
    
    # 調理（キッチンスタッフを確保）
    with restaurant.kitchen_staff.request() as req:
        yield req
        
        # 各料理の調理時間を計算
        cooking_times = []
        for item in customer.orders:
            cooking_time = restaurant.cook(item)
            cooking_times.append(cooking_time)
        
        # 最も時間のかかる料理ができるまで待機
        if cooking_times:
            yield env.timeout(max(cooking_times))
    
    # 食事
    eating_time = random.uniform(15, 30)  # 食事時間（15〜30分）
    yield env.timeout(eating_time)
    
    # 会計と退店
    with restaurant.hall_staff.request() as req:
        yield req
        yield env.timeout(random.uniform(3, 5))  # 会計処理時間
    
    # 売上記録
    bill = sum(restaurant.menu.get_price(item) for item in customer.orders)
    restaurant.metrics.record_revenue(bill, env.now)
    
    # 退店
    customer.departure_time = env.now
    restaurant.metrics.record_departure(customer, env.now)
    restaurant.release_seating(customer)

def customer_generator(env, restaurant, customer_params, weather_schedule):
    """顧客を生成するプロセス"""
    while True:
        # 営業時間外なら顧客生成を停止
        if not restaurant.is_open(env.now):
            if env.now >= restaurant.closing_time:
                break
            else:
                yield env.timeout(1)
                continue
        
        # 現在の時間帯を判定
        current_hour = int(env.now / 60)
        time_of_day = "lunch" if 11 <= current_hour < 15 else "dinner"
        
        # 曜日を判定（簡易的に平日/週末）
        day_type = "weekend" if current_hour // 24 % 7 >= 5 else "weekday"
        
        # 天候の影響を取得
        current_weather = get_weather(env.now, weather_schedule)
        weather_factor = WEATHER_FACTORS.get(current_weather, 1.0)
        
        # 待ち行列の長さによる影響
        queue_length = len(restaurant.waiting_line)
        queue_factor = max(0.1, 1 - queue_length * 0.05)  # 待ち行列が長いほど来客が減少
        
        # 次の顧客の到着間隔を計算
        params = customer_params[day_type][time_of_day]
        # 0除算を防止
        weather_queue_product = max(EPSILON, weather_factor * queue_factor)
        mean_interval = params["mean_interval"] / weather_queue_product
        # 0除算を防止
        mean_interval = max(EPSILON, mean_interval)
        interval = random.expovariate(1.0 / mean_interval)
        
        yield env.timeout(interval)
        
        # グループサイズを決定
        group_size = np.random.choice(
            [1, 2, 3, 4], 
            p=params["group_size_probs"]
        )
        
        # 忍耐度を決定（10〜30分）
        patience = random.uniform(10, 30)
        
        # 顧客を生成
        customer = Customer(env, group_size, patience)
        
        # 顧客の行動プロセスを開始
        env.process(customer_behavior(env, customer, restaurant))

def get_weather(time, weather_schedule):
    """時間に応じた天候を取得"""
    hour = int(time / 60)
    day = hour // 24
    if day in weather_schedule:
        return weather_schedule[day]
    return "sunny"  # デフォルト

def analyze_results(metrics):
    """シミュレーション結果を分析"""
    metrics.calculate_metrics()
    
    print("\n===== 飲食店待ち行列シミュレーション結果 =====")
    
    # 経済指標
    print("\n【経済指標】")
    print(f"総売上: {metrics.total_revenue:.0f}円")
    print(f"総コスト: {metrics.total_cost:.0f}円")
    print(f"純利益: {metrics.total_profit:.0f}円")
    
    # 運営効率
    print("\n【運営効率】")
    print(f"最大待ち行列長: {metrics.max_queue_length}組")
    
    # 顧客体験
    print("\n【顧客体験】")
    print(f"総来客数: {metrics.total_customers}組")
    print(f"着席できた顧客: {metrics.total_customers - metrics.walkouts}組")
    print(f"待ちきれずに帰った顧客: {metrics.walkouts}組 ({metrics.walkout_rate * 100:.1f}%)")
    print(f"平均待ち時間: {metrics.avg_waiting_time:.1f}分")
    print(f"平均食事時間: {metrics.avg_dining_time:.1f}分")
    
    # 在庫管理
    print("\n【在庫管理】")
    print(f"品切れ回数: {sum(metrics.stockouts.values())}回")
    if metrics.stockouts:
        print("品切れメニュー:")
        for item, count in metrics.stockouts.most_common():
            print(f"  {item}: {count}回")
    
    print(f"材料廃棄率: {metrics.ingredient_wastage * 100:.1f}%")
    
    # 材料使用状況
    print("\n【材料使用状況】")
    for name, data in metrics.ingredient_usage.items():
        print(f"  {name}: 初期在庫 {data['initial']}, 使用量 {data['used']:.1f} ({data['usage_rate'] * 100:.1f}%), 残量 {data['remaining']:.1f}")
    
    # グラフ作成
    plot_hourly_metrics(metrics)
    plot_queue_length_over_time(metrics)
    plot_ingredient_usage(metrics)

def plot_hourly_metrics(metrics):
    """時間帯別の指標をプロット"""
    plt.figure(figsize=(12, 8))
    
    # 時間帯別売上
    plt.subplot(3, 1, 1)
    hours = sorted(metrics.hourly_metrics["revenue"].keys())
    revenue = [metrics.hourly_metrics["revenue"][h] for h in hours]
    plt.bar(hours, revenue)
    plt.title("時間帯別売上")
    plt.xlabel("時間")
    plt.ylabel("売上（円）")
    
    # 時間帯別来客数
    plt.subplot(3, 1, 2)
    customers = [metrics.hourly_metrics["customers"][h] for h in hours]
    walkouts = [metrics.hourly_metrics["walkouts"][h] for h in hours]
    plt.bar(hours, customers, label="総来客数")
    plt.bar(hours, walkouts, label="キャンセル数")
    plt.title("時間帯別来客数")
    plt.xlabel("時間")
    plt.ylabel("組数")
    plt.legend()
    
    # 時間帯別キャンセル率
    plt.subplot(3, 1, 3)
    cancel_rates = [
        walkouts[i] / customers[i] * 100 if customers[i] > EPSILON else 0 
        for i in range(len(hours))
    ]
    plt.bar(hours, cancel_rates)
    plt.title("時間帯別キャンセル率")
    plt.xlabel("時間")
    plt.ylabel("キャンセル率（%）")
    
    plt.tight_layout()
    plt.savefig("hourly_metrics.png")
    plt.close()

def plot_queue_length_over_time(metrics):
    """待ち行列の長さの時間変化をプロット"""
    plt.figure(figsize=(12, 6))
    
    times, queue_lengths = zip(*metrics.queue_length_over_time) if metrics.queue_length_over_time else ([], [])
    plt.plot(times, queue_lengths)
    plt.title("待ち行列の長さの時間変化")
    plt.xlabel("時間（分）")
    plt.ylabel("待ち行列の長さ（組）")
    plt.grid(True)
    
    plt.savefig("queue_length.png")
    plt.close()

def plot_ingredient_usage(metrics):
    """材料の使用状況をプロット"""
    plt.figure(figsize=(12, 6))
    
    names = list(metrics.ingredient_usage.keys())
    usage_rates = [metrics.ingredient_usage[name]["usage_rate"] * 100 for name in names]
    
    # 使用率でソート
    sorted_indices = np.argsort(usage_rates)
    sorted_names = [names[i] for i in sorted_indices]
    sorted_rates = [usage_rates[i] for i in sorted_indices]
    
    plt.barh(sorted_names, sorted_rates)
    plt.title("材料の使用率")
    plt.xlabel("使用率（%）")
    plt.ylabel("材料")
    plt.grid(True)
    plt.tight_layout()
    
    plt.savefig("ingredient_usage.png")
    plt.close()


def main():
    """メイン関数"""
    # 天候スケジュール（日ごと）
    weather_schedule = {
        0: "sunny",  # 1日目
    }
    
    # シミュレーション環境の設定
    env = simpy.Environment()
    
    # レストランの初期化
    restaurant = Restaurant(
        env=env,
        seats=SEATS,
        menu_items=MENU,
        ingredients_data=INGREDIENTS,
        opening_hour=OPENING_HOUR,
        closing_hour=CLOSING_HOUR,
        kitchen_staff=KITCHEN_STAFF,
        hall_staff=HALL_STAFF
    )
    
    # 顧客生成プロセスの開始
    env.process(customer_generator(env, restaurant, CUSTOMER_PARAMS, weather_schedule))
    
    # シミュレーション実行（1日分）
    env.run(until=24*60)  # 24時間（分単位）
    
    # 材料使用状況を記録
    restaurant.metrics.record_ingredient_usage(restaurant.ingredients)
    
    # 材料コストを計算 - 初期在庫（購入した全材料）のコストを記録
    for ing in restaurant.ingredients.values():
        restaurant.metrics.record_cost(ing.initial_stock * ing.cost)
    
    # 結果の分析
    analyze_results(restaurant.metrics)
    
    print("\nシミュレーション完了！グラフは以下のファイルに保存されました：")
    print("- hourly_metrics.png")
    print("- queue_length.png")
    print("- ingredient_usage.png")

if __name__ == "__main__":
    main()
