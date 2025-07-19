Portfolio Analyzer
トレーディングビュー（TradingView）のバックテスト Excel ファイル（.xlsx）を読み込んで、
複数銘柄（戦略）のパフォーマンスを一括評価できる PyQt6 ベースのデスクトップアプリです。

ダークテーマ & 黒背景＋赤ラインのエクイティカーブ（タイトルは常に Equity Curve）

複数ファイルをドラッグ＆ドロップで追加、個別 ON/OFF・削除・一括管理

許容最大ドローダウン / Monte Carlo 試行回数をスライダー & 数値入力で即時調整

日本語 / 英語 UI ワンクリック切替（辞書ベース即時反映）

🚀 特徴
複数バックテストファイルを同時分析（TradingView エクスポート対応）

ドラッグ＆ドロップ対応（空領域に .xlsx を直接投入可能）

エクイティカーブ可視化（高コントラスト黒背景＋赤ライン）

主要トレード指標を自動算出 & 3ブロック表示

許容最大DD（破産閾値）を動的変更 → Risk of Ruin を再計算

Monte Carlo 試行回数をスライダー or 入力ボックスで調整（1,000〜100,000+ 任意）

ゴミ箱ボタンで個別削除 / All ON / All OFF / まとめてリセット

期待値・Payoff・ストリークなど運用評価に必須の補助指標も搭載

日本語 / 英語 UI 即時切替（Equity Curve タイトルのみ英語固定）

📝 使い方
Excelファイルを開く ボタン、または空のファイルリスト領域へ .xlsx をドラッグ＆ドロップ

エクイティカーブ & 各種指標が自動表示

許容最大ドローダウン（％）スライダー or 数値入力で変更 → Risk of Ruin 自動更新

Monte Carlo 試行回数 を変更（スライダー / 数値入力）→ 分解能 (RoR Step) も更新

ファイル管理領域で ON/OFF（チェック）、ゴミ箱削除、All ON / All OFF、全リセット

再計算 ボタンで「チェックされているファイルのみ」で再集計（負荷軽減したいときに使用）

左上の 🌐 ボタンで UI 言語（JP / EN）を切り替え

📊 実装されている主要指標
CAGR (%) … 年率複利リターン

Max Drawdown (%) … 最大ドローダウン

Sharpe Ratio … シャープレシオ（年率化・無リスクレート 0 想定）

Sortino Ratio … Sortino レシオ（下方偏差使用）

Profit Factor … 総利益 ÷ 総損失（絶対値）

Expectancy … 1トレードあたり期待値

Payoff Ratio … 平均利益 ÷ 平均損失（絶対値）

Win Rate (%) … 勝率

Avg Win / Avg Loss … 平均利益／平均損失

Max Win Streak / Max Lose Streak … 最大連勝／最大連敗

Trade Count … 総トレード数

Risk of Ruin (%) … 破産確率（Monte Carlo ブートストラップ）

RoR Step (%) … Monte Carlo 試行数に依存する理論最小刻み（= 100 / 試行数）

🧪 Risk of Ruin (Monte Carlo)
トレード損益系列を復元抽出でランダム並び生成

ピーク→谷の下落率が「許容最大DD（％）」に達したらその試行は “破産” 判定

試行回数を増やすと精度向上（計算時間↑）

分解能（RoR Step）は 100 / 試行回数 で表示

再現性（乱数シード固定）は将来実装予定

🖥️ スクリーンショット


🌐 多言語
右上（または上部）の 🌐 ボタンで 日本語 / 英語 切替

翻訳辞書は views/main_window.py 内 TRANSLATIONS に定義

Equity Curve タイトルは英語固定（可読性優先）

⚡ Windows デスクトップからの起動
start_app.bat をダブルクリックでアプリ起動

バッチへのショートカットをデスクトップに配置すると便利

🛠️ 開発・コントリビュート
指標追加 / UI 改善 / 高速化案など Pull Request・Issue 歓迎

計算ロジック: pyqt_portfolio_analyzer/models/metrics.py

データ読み込み: pyqt_portfolio_analyzer/models/data_loader.py

GUI / 多言語 / D&D: pyqt_portfolio_analyzer/views/main_window.py

コントローラ: pyqt_portfolio_analyzer/controller.py

📦 対応 Excel 形式（基本前提）
シート名: トレード一覧

必須列例: 日時, 損益列（例：損益 / Profit など。異なる場合は loader でマッピング要）

日次集計は 日時 → 日付へ変換後、日次損益合計 → 累積和でエクイティカーブ生成

初期資金（例: 100,000）は metrics.py 内で定義（要変更可）

❓ よくある質問
Q. RoR の値が揺れる
A. 乱数による Monte Carlo のため。将来 Seed オプション追加予定。

Q. 指標が NaN になる
A. トレード数が極端に少ない / 分母が 0（標準偏差ゼロなど）のケース。

Q. タイトルを日本語にしたい
A. 翻訳辞書に追加し、フォント（Meiryo など）設定を行えば可能（現在は英語固定方針）。

Q. 結果がファイル順で微妙に変わる
A. 同一日時トレードの並び順差。data_loader で明示ソートを強化可能。

🛠️ 開発用（環境セットアップ例）
sh
コピーする
編集する
# 環境作成（初回）
conda create -n pa-env python=3.12 -y
conda activate pa-env

# 依存インストール
pip install -r requirements.txt
# （requirements.txt がまだ無ければ）
pip install pyqt6 pandas numpy matplotlib openpyxl

# 起動
python -m pyqt_portfolio_analyzer
# または
start_app.bat
🔄 Git ワークフロー例
sh
コピーする
編集する
git status
git add .
git commit -m "feat: add JP/EN toggle & Monte Carlo adjustable"
git pull --rebase origin main
git push origin main
🔮 今後追加予定（アイデア）
設定永続化（言語 / 許容DD / 試行回数 / 最終ファイル）

Calmar / MAR / Ulcer / CVaR / Recovery Factor / Skew / Kurtosis

銘柄別寄与・相関マトリクス・ドローダウン曲線・月次損益ヒートマップ

Monte Carlo：ブロックブートストラップ / パラメトリック法 / Seed 固定

指標・エクイティの CSV / PNG エクスポート

EXE 配布（PyInstaller / Nuitka）

単体テスト（pytest）& CI

ポートフォリオ最適化（Sharpe 最大 / VaR / CVaR 最小化）

📚 参考文献・仕様元
『システムトレード 基本と原則』ブレント・ペンフォールド著

『伝説のトレーダー集団 タートル流投資の魔術』カーティス・フェイス著

TradingView 公式ドキュメント

📝 ライセンス
MIT License
（著作権表記を残せば商用利用・改変再配布自由）

🙋 コントリビュート方法
Issue / 機能要望を登録

Fork → ブランチ作成 → 変更 → テスト

コミットメッセージは feat: / fix: / refactor: / docs: などプリフィクス推奨

Pull Request 作成

🗒 再開クイックメモ
sh
コピーする
編集する
conda activate pa-env
python -m pyqt_portfolio_analyzer
# 例: 設定永続化(QSettings)の実装に着手