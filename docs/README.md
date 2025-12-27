# Pyfilecleaner

Windows 向けの自動ファイルクリーナーユーティリティ。指定したディレクトリから、古いファイルを自動的に削除します。

## 主な機能

- **複数ディレクトリ対応**: config.ini で複数のクリーンアップ対象ディレクトリを指定可能
- **柔軟な拡張子フィルタリング**: 特定の拡張子のみを対象、または全ファイルを対象に設定可能
- **ファイル更新日時ベースの削除**: 更新日時に基づいて古いファイルを検出・削除
- **タイムゾーン対応**: Asia/Tokyo タイムゾーンでファイル時刻を管理

## 前提条件

- Python 3.13 以上
- Windows 11

## インストール

1. リポジトリをクローン
```bash
git clone https://github.com/yokamkick/Pyfilecleaner.git
cd Pyfilecleaner
```

2. 仮想環境を作成・有効化
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. 依存ライブラリをインストール
```bash
pip install -r requirements.txt
```

4. 設定ファイルを編集（config.ini）
```ini
[LOGGING]
log_retention_days = 7
log_directory = logs
log_level = INFO
debug_mode = False
project_name = Pyfilecleaner

[Paths]
target_dir1 = C:\Users\example\Downloads
target_dir2 = C:\Users\example\Documents

[Settings]
target_extensions = pdf,txt,jpg
file_cleanup_hour = 24
```

5. 実行
```bash
python main.py
```

## 使用方法

### 基本的な実行

```bash
python main.py
```

コンソール出力例:
```
対象: pdf, txt, jpg
対象ディレクトリ: 2 件
  1. C:\Users\example\Downloads
  2. C:\Users\example\Documents

------------------------------------------------------------
合計:
  削除したファイル: 15
  削除したフォルダ: 3
  スキップしたファイル: 8
  失敗したファイル: 0
  失敗したフォルダ: 0
============================================================
```

### 設定ファイル (config.ini)

#### LOGGING セクション

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|---------|------|
| log_retention_days | int | 7 | ログファイルの保持日数 |
| log_directory | str | logs | ログディレクトリのパス |
| log_level | str | INFO | ログレベル (DEBUG, INFO, WARNING, ERROR) |
| debug_mode | bool | False | 詳細なデバッグログを有効化 |
| project_name | str | Pyfilecleaner | プロジェクト名（ログファイル名の接頭辞） |

#### Paths セクション

対象ディレクトリを `target_dir1`, `target_dir2`, ... の形式で指定します:

```ini
[Paths]
target_dir1 = C:\Users\example\Downloads
target_dir2 = C:\Users\example\Documents
target_dir3 = D:\Temporary
```

#### Settings セクション

| 設定項目 | 型 | デフォルト | 説明 |
|---------|-----|---------|------|
| target_extensions | str | * | 対象拡張子（カンマ区切り、`*` で全ファイル） |
| file_cleanup_hour | int | 24 | 何時間より古いファイルを削除するか |

### 設定例

**ダウンロードフォルダから 1 時間以上前の全ファイルを削除**:
```ini
[Paths]
target_dir1 = C:\Users\example\Downloads

[Settings]
target_extensions = *
file_cleanup_hour = 1
```

**複数ディレクトリから PDF ファイルのみを 7 日以上前のものから削除**:
```ini
[Paths]
target_dir1 = C:\Users\example\Downloads
target_dir2 = C:\Users\example\Documents

[Settings]
target_extensions = pdf
file_cleanup_hour = 168
```

## プロジェクト構造

```
Pyfilecleaner/
├── app/                    # アプリケーション情報
│   └── __init__.py        # バージョン・日付管理
├── service/
│   └── filecleaner.py     # コア削除エンジン
├── utils/
│   ├── config.ini         # 設定ファイル
│   ├── config_manager.py  # 設定読み込み管理
│   └── log_rotation.py    # ログローテーション管理
├── scripts/
│   ├── version_manager.py # バージョン管理
│   └── project_structure.py # プロジェクト構造出力
├── tests/
│   └── test_filecleaner.py # ユニットテスト
├── main.py                # エントリーポイント
├── build.py               # Windows 実行ファイル構築
└── requirements.txt       # 依存ライブラリ
```

### 主要コンポーネント

**FileCleaner (service/filecleaner.py)**

ファイルクリーンアップ処理の中核。設定ファイルから対象ディレクトリ・拡張子・保持期間を読み込み、削除対象ファイルを特定して削除します。

主要メソッド:
- `clean_all()`: 全対象ディレクトリをクリーンアップ
- `clean_directory(directory)`: 指定ディレクトリをクリーンアップ
- `print_summary(results)`: 削除結果サマリを出力

削除モード:
- **ワイルドカードモード** (`target_extensions = *`): サブディレクトリ全体を再帰削除
- **拡張子フィルタリングモード**: 指定拡張子のみ削除、削除後に空ディレクトリも削除

**ConfigManager (utils/config_manager.py)**

config.ini ファイルから設定値を読み込み、型別に変換します。PyInstaller ビルド時の config ファイル参照にも対応。

**LogRotation (utils/log_rotation.py)**

`TimedRotatingFileHandler` でログをローテーション（日次）。設定日数経過後のログを自動削除。debug_mode 有効時は詳細なデバッグログを別ファイルに出力。

## 開発

### テスト実行

```bash
python -m pytest tests/ -v --tb=short --disable-warnings
```

テスト結果は 750+ 以上のテストケースで、FileCleaner の全機能をカバーします。

### 型チェック

```bash
pyright
```

Python 3.13 標準の型チェックモードで実行。

### Windows 実行ファイル構築

```bash
python build.py
```

PyInstaller で `Pyfilecleaner.exe` を生成。config.ini は実行ファイルにバンドルされます。

## トラブルシューティング

### 対象ディレクトリが設定されていないエラー

**原因**: config.ini に `target_dir` 設定がない

**解決方法**: config.ini の `[Paths]` セクションに `target_dir1` を追加してください:
```ini
[Paths]
target_dir1 = C:\Users\example\Downloads
```

### ファイルが削除されない

**原因**: ファイル年齢がまだ基準に達していない、または拡張子が一致していない

**確認方法**:
1. config.ini の `file_cleanup_hour` 値を確認
2. `target_extensions` がファイルの拡張子と一致しているか確認
3. debug_mode を True に設定してログで詳細を確認
   ```ini
   [LOGGING]
   debug_mode = True
   ```

### 削除権限エラー

**原因**: ファイルが別プロセスで使用中、または削除権限がない

**解決方法**:
- ファイルを使用しているアプリケーションを閉じる
- 管理者権限で実行
- ログファイル (logs/Pyfilecleaner.log) でエラー詳細を確認

### ログファイルが作成されない

**原因**: ログディレクトリの作成権限がない

**解決方法**:
1. config.ini の `log_directory` を確認
2. 指定ディレクトリの書き込み権限を確認
3. ディレクトリが存在しない場合は手動作成

## バージョン情報

- **現在のバージョン**: 1.0.1
- **最終更新日**: 2025年12月26日

## ライセンス

このプロジェクトのライセンス情報については、 [LICENSE](./LICENSE) を参照してください。

## 更新履歴

更新履歴は [CHANGELOG.md](./CHANGELOG.md) を参照してください。
