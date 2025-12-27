# 変更ログ

このプロジェクトのすべての変更は、このファイルに記録されます。

形式は[Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)に基づいており、バージョニングは[セマンティック バージョニング](https://semver.org/lang/ja/)に従います。

## [1.0.1] - 2025-12-26

### 追加
- ファイルクリーンアップ機能のテストスイートを追加（tests/test_filecleaner.py）
- プロジェクト構造ドキュメント（scripts/project_structure.txt）を追加

### 変更
- ファイルのタイムスタンプ判定の基準を更新日時に変更（service/filecleaner.py）
- file_cleanup_hourのデフォルト値を24時間に設定（service/filecleaner.py）
- ファイルクリーナーのロジックを改善し、処理を簡潔に整理（service/filecleaner.py）
- file_cleanup_hourのデフォルト値処理を改善（service/filecleaner.py）
- OSErrorの例外処理を簡略化（service/filecleaner.py）
- results辞書のイテレーション処理を改善（service/filecleaner.py）

### 修正
- Windowsでのファイル作成時刻の取得方法を改善し、st_ctimeを正しく使用（service/filecleaner.py）
