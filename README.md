# 飲食店待ち行列シミュレーション

このプロジェクトは、飲食店における待ち行列のシミュレーションを行うPythonスクリプトです。顧客の到着、席の割り当て、注文、調理、食事、退店までの一連のプロセスをシミュレートし、様々な指標を分析します。

## 仮想環境での実行方法

このプロジェクトは、Python仮想環境（venv）内で実行するためのスクリプトが用意されています。

### Unix系システム（macOS/Linux）の場合:

1. スクリプトを実行可能にします:
   ```bash
   chmod +x run_simulation.sh
   ```

2. スクリプトを実行します:
   ```bash
   ./run_simulation.sh
   ```

### Windowsの場合:

1. コマンドプロンプトまたはPowerShellで以下を実行します:
   ```
   run_simulation.bat
   ```

これらのスクリプトは、自動的に仮想環境を作成し、必要なパッケージをインストールした後、シミュレーションを実行します。

## 特徴

- 離散イベントシミュレーション（SimPy）を使用
- 顧客の到着、待ち行列、席の割り当て、注文、調理、食事、退店までの一連のプロセスをモデル化
- 材料の在庫管理（営業時間中の追加調達なし）
- 天候、時間帯、曜日による来客頻度の変動
- 待ち行列の長さによる来店意欲の変化
- 顧客の忍耐度（待てる最大時間）の考慮
- 詳細な分析結果とグラフの生成
- ゼロ除算防止のための安全な計算処理
- 日本語フォントに対応したグラフ表示
- シミュレーションパラメータを別ファイルに分離し、設定変更を容易に

## 必要なライブラリ

```
simpy
numpy
pandas
matplotlib
japanize-matplotlib
```

インストール方法:

```bash
pip install -r requirements.txt
```

または個別にインストール:

```bash
pip install simpy numpy pandas matplotlib japanize-matplotlib
```

## 使い方

1. スクリプトを実行するだけで、デフォルト設定でシミュレーションが実行されます:

```bash
python restaurant_simulation.py
```

2. シミュレーション結果は、コンソールに表示されるとともに、以下のグラフファイルが生成されます:
   - `hourly_metrics.png`: 時間帯別の売上、来客数、キャンセル率
   - `queue_length.png`: 待ち行列の長さの時間変化
   - `ingredient_usage.png`: 材料の使用率

## カスタマイズ

シミュレーションパラメータは `simulation_parameters.py` ファイルに分離されており、このファイルを編集することで様々な条件でのシミュレーションが可能です。メインのシミュレーションロジックを変更せずにパラメータだけを調整できるため、異なるシナリオを簡単にテストできます。

### ファイル構成

- `simulation_parameters.py`: シミュレーションの全パラメータを定義
- `restaurant_simulation.py`: シミュレーションのメインロジックを実装
- `example_scenarios.py`: 異なるシナリオでのシミュレーション実行例

以下のパラメータを変更することで、様々な条件でのシミュレーションが可能です:

### レストラン設定

```python
SEATS = 20  # 席数
OPENING_HOUR = 11  # 開店時間（時）
CLOSING_HOUR = 22  # 閉店時間（時）
KITCHEN_STAFF = 2  # 調理スタッフ数
HALL_STAFF = 3  # ホールスタッフ数
```

### メニュー設定

```python
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
    # 他のメニュー項目...
}
```

### 材料設定

```python
INGREDIENTS = {
    "麺": {"initial_stock": 100, "cost": 100},
    "スープ": {"initial_stock": 80, "cost": 150},
    # 他の材料...
}
```

### 顧客生成パラメータ

```python
CUSTOMER_PARAMS = {
    "weekday": {
        "lunch": {"mean_interval": 10, "group_size_probs": [0.4, 0.4, 0.15, 0.05]},
        "dinner": {"mean_interval": 8, "group_size_probs": [0.3, 0.4, 0.2, 0.1]}
    },
    "weekend": {
        "lunch": {"mean_interval": 7, "group_size_probs": [0.3, 0.35, 0.25, 0.1]},
        "dinner": {"mean_interval": 5, "group_size_probs": [0.2, 0.3, 0.3, 0.2]}
    }
}
```

`mean_interval`はポアソン分布のパラメータで、顧客の平均到着間隔（分）を表します。この値は天候や待ち行列の長さによって動的に調整されます。実際の到着間隔は以下のように指数分布を用いて生成されます：

```python
# 次の顧客の到着間隔を計算
weather_queue_product = max(EPSILON, weather_factor * queue_factor)
mean_interval = params["mean_interval"] / weather_queue_product
interval = random.expovariate(1.0 / mean_interval)
```

これは、ポアソン過程における到着間隔が指数分布に従うという性質を利用しています。

### 天候影響係数

```python
WEATHER_FACTORS = {
    "sunny": 1.0,
    "cloudy": 0.9,
    "rainy": 0.7,
    "snowy": 0.5
}
```

## 分析できる指標

### 経済指標
- 総売上
- 総コスト
- 純利益

### 運営効率
- 最大待ち行列長

### 顧客体験
- 総来客数
- 着席できた顧客数
- 待ちきれずに帰った顧客数と割合
- 平均待ち時間
- 平均食事時間

### 在庫管理
- 品切れ回数と品切れメニュー
- 材料廃棄率
- 材料ごとの使用状況（初期在庫、使用量、使用率、残量）

## 拡張可能性

このシミュレーションは以下のように拡張できます:

1. 複数日シミュレーション
2. 予約システムの導入
3. スタッフシフトの最適化
4. メニュー構成の最適化
5. 価格戦略の分析
6. 席のレイアウト最適化

## 仮定

- 営業時間中に材料の追加調達はできない
- 席が空いたら直ちに待ち行列の先頭の客が着席する
- 来客頻度はポアソン分布に従い、そのパラメータは天候や待ち行列の長さによって変動する
- 顧客は一定時間以上待つと帰る
- 各顧客グループのサイズは確率分布に従う

## 技術的な改良点

### ゼロ除算防止

シミュレーション内の計算処理において、ゼロ除算エラーを防ぐために極小値定数（EPSILON = 1e-10）を導入しています。これにより、分母が0になる可能性のある全ての除算操作が安全に実行されます。

```python
# 0除算防止用の極小値定数
EPSILON = 1e-10  # 非常に小さい値

# 使用例
value = numerator / denominator if denominator > EPSILON else 0
```

### 日本語フォントサポート

グラフのタイトル、ラベル、凡例などの日本語テキストを正しく表示するために、japanize-matplotlibライブラリを使用しています。

```python
import matplotlib.pyplot as plt
import japanize_matplotlib  # 日本語フォントのサポート
```

### 材料コスト計算

材料コストは、使用した材料だけでなく、購入した全材料（初期在庫）のコストを考慮して計算されます。これにより、廃棄された材料のコストも適切に反映され、より現実的な収益計算が可能になります。

```python
# 材料コストを計算 - 初期在庫（購入した全材料）のコストを記録
for ing in restaurant.ingredients.values():
    restaurant.metrics.record_cost(ing.initial_stock * ing.cost)
```

### 材料使用処理の改善

顧客が注文した料理の材料が適切に消費されるように、注文処理時に材料使用のロジックを追加しました。これにより、材料の使用量と在庫が正確に追跡されます。

```python
# 注文した料理の材料を使用
for item in customer.orders:
    restaurant.reserve_ingredients(item)
```
