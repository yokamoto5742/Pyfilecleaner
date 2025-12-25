# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## House Rules:
- 文章ではなくパッチの差分を返す。
- コードの変更範囲は最小限に抑える。
- コードの修正は直接適用する。
- Pythonのコーディング規約はPEP8に従います。
- KISSの原則に従い、できるだけシンプルなコードにします。
- 可読性を優先します。一度読んだだけで理解できるコードが最高のコードです。
- Pythonのコードのimport文は以下の適切な順序に並べ替えてください。
標準ライブラリ
サードパーティライブラリ
カスタムモジュール 
それぞれアルファベット順に並べます。importが先でfromは後です。

## CHANGELOG
このプロジェクトにおけるすべての重要な変更は日本語でdcos/CHANGELOG.mdに記録します。
フォーマットは[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づきます。

## Automatic Notifications (Hooks)
自動通知は`.claude/settings.local.json` で設定済：
- **Stop Hook**: ユーザーがClaude Codeを停止した時に「作業が完了しました」と通知
- **SessionEnd Hook**: セッション終了時に「Claude Code セッションが終了しました」と通知

## クリーンコードガイドライン
- 関数のサイズ：関数は50行以下に抑えることを目標にしてください。関数の処理が多すぎる場合は、より小さなヘルパー関数に分割してください。
- 単一責任：各関数とモジュールには明確な目的が1つあるようにします。無関係なロジックをまとめないでください。
- 命名：説明的な名前を使用してください。`tmp` 、`data`、`handleStuff`のような一般的な名前は避けてください。例えば、`doCalc`よりも`calculateInvoiceTotal` の方が適しています。
- DRY原則：コードを重複させないでください。類似のロジックが2箇所に存在する場合は、共有関数にリファクタリングしてください。それぞれに独自の実装が必要な場合はその理由を明確にしてください。
- コメント:分かりにくいロジックについては説明を加えます。説明不要のコードには過剰なコメントはつけないでください。
- コメントとdocstringは必要最小限に日本語で記述します。文末に"。"や"."をつけないでください。

## Project Overview

Pyfilecleaner is a Windows-based Python utility that automatically cleans up files from specified directories based on file age and extension criteria. It's designed to run periodically and clean up download folders or other target directories.

## Development Commands

### Testing
```bash
python -m pytest tests/ -v --tb=short --disable-warnings
```

Run all tests with verbose output and short traceback format.

### Type Checking
```bash
pyright
```

Type checking is configured in `pyrightconfig.json` for Python 3.13 with standard type checking mode.

### Building Executable
```bash
python build.py
```

Builds a Windows executable using PyInstaller. The build script automatically updates the version and packages the config.ini file.

### Running the Application
```bash
python main.py
```

Runs the file cleaner with the settings defined in `utils/config.ini`.

## Architecture

### Core Components

**FileCleaner (`service/filecleaner.py`)**
- Main service class that orchestrates file cleanup operations
- Loads configuration from config.ini to determine target directories, extensions, and retention period
- Uses file creation time (`st_ctime`) with Asia/Tokyo timezone to determine file age
- Supports two cleanup modes:
  - Wildcard mode (`*`): Recursively deletes entire directory trees
  - Extension mode: Selectively deletes files matching specified extensions, removes empty directories after cleanup

**Configuration Management (`utils/config_manager.py`)**
- Loads config.ini from the utils directory
- For PyInstaller builds, uses `sys._MEIPASS` to locate the bundled config file
- Provides type-aware config value retrieval (bool, int, float, string)

**Logging System (`utils/log_rotation.py`)**
- Uses `TimedRotatingFileHandler` with midnight rotation
- Maintains logs based on `log_retention_days` setting
- Supports optional debug logging when `debug_mode = True`
- Automatically cleans up old rotated log files

### Configuration File Structure

The `utils/config.ini` file controls all operational parameters:

```ini
[LOGGING]
log_retention_days = 7
log_directory = logs
log_level = INFO
debug_mode = False
project_name = Pyfilecleaner

[Paths]
target_dir1 = C:\Users\yokam\Downloads
# Add target_dir2, target_dir3, etc. as needed

[Settings]
target_extensions = *  # or csv list like: pdf,txt,jpg
file_cleanup_hour = 1  # Files older than this many hours are deleted
```

### Key Implementation Details

- File age calculation uses `app_start_time` (when FileCleaner is instantiated) as the reference point, not current time during each file check
- All timestamps use `ZoneInfo("Asia/Tokyo")` for timezone-aware datetime operations
- The cleanup process skips files/directories it doesn't have permissions to delete, logging errors but continuing execution
- When `target_extensions = *`, subdirectories are deleted entirely; otherwise, they are recursively searched for matching extensions
