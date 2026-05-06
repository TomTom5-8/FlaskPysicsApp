# 物理シミュレーション Web App (ばね減衰振動)

Flaskを用いた、ばねの減衰振動を計算・可視化するWebアプリケーションです。

## 主な機能
- **シミュレーション計算**: パラメータ（k, m, gamma, x0）に基づいた振動計算
- **ユーザー管理**: 新規ID登録、ログイン、ログアウト機能[cite: 2]
- **履歴保存**: ユーザーごとのシミュレーション実行履歴の保存と表示[cite: 2]

## 使用技術
- **Backend**: Python 3.x, Flask
- **Database**: SQLite (SQLAlchemy)[cite: 2]
- **Frontend**: HTML, Chart.js (グラフ表示用)[cite: 1]
- **Library**: NumPy (計算用)[cite: 2]

## セットアップ方法
1. リポジトリをクローンまたはダウンロード
2. 必要なライブラリのインストール
   ```bash
   pip install flask flask-sqlalchemy flask-login numpy werkzeug