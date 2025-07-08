#!/bin/bash

# 仮想環境のディレクトリ名
VENV_DIR="venv"

# 仮想環境が存在しない場合は作成
if [ ! -d "$VENV_DIR" ]; then
    echo "仮想環境を作成しています..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "仮想環境の作成に失敗しました。Python 3がインストールされていることを確認してください。"
        exit 1
    fi
    echo "仮想環境が作成されました。"
fi

# 仮想環境をアクティベート
echo "仮想環境をアクティベートしています..."
source $VENV_DIR/bin/activate

# 依存パッケージをインストール
echo "必要なパッケージをインストールしています..."
pip install -r requirements.txt

# 実行するスクリプトを選択
echo "実行するスクリプトを選択してください:"
echo "1) 基本シミュレーション (restaurant_simulation.py)"
echo "2) シナリオ比較 (example_scenarios.py)"
read -p "選択 (1/2): " choice

# 選択に基づいてスクリプトを実行
if [ "$choice" = "1" ]; then
    echo "基本シミュレーションを実行しています..."
    python restaurant_simulation.py
elif [ "$choice" = "2" ]; then
    echo "シナリオ比較を実行しています..."
    python example_scenarios.py
else
    echo "無効な選択です。1または2を入力してください。"
    exit 1
fi

# 仮想環境を非アクティベート
deactivate

echo "シミュレーションが完了しました。"
