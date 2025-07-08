@echo off
setlocal

:: 仮想環境のディレクトリ名
set VENV_DIR=venv

:: 仮想環境が存在しない場合は作成
if not exist %VENV_DIR% (
    echo 仮想環境を作成しています...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo 仮想環境の作成に失敗しました。Python 3がインストールされていることを確認してください。
        exit /b 1
    )
    echo 仮想環境が作成されました。
)

:: 仮想環境をアクティベート
echo 仮想環境をアクティベートしています...
call %VENV_DIR%\Scripts\activate.bat

:: 依存パッケージをインストール
echo 必要なパッケージをインストールしています...
pip install -r requirements.txt

:: 実行するスクリプトを選択
echo 実行するスクリプトを選択してください:
echo 1) 基本シミュレーション (restaurant_simulation.py)
echo 2) シナリオ比較 (example_scenarios.py)
set /p choice="選択 (1/2): "

:: 選択に基づいてスクリプトを実行
if "%choice%"=="1" (
    echo 基本シミュレーションを実行しています...
    python restaurant_simulation.py
) else if "%choice%"=="2" (
    echo シナリオ比較を実行しています...
    python example_scenarios.py
) else (
    echo 無効な選択です。1または2を入力してください。
    exit /b 1
)

:: 仮想環境を非アクティベート
call deactivate

echo シミュレーションが完了しました。
