import configparser
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from utils.config_manager import get_config_value, load_config


class FileCleaner:
    """指定されたディレクトリ内のファイルとサブフォルダを削除するクラス"""

    def __init__(self, config: configparser.ConfigParser | None = None):
        self.config = config if config is not None else load_config()
        self.logger = logging.getLogger(__name__)
        self.target_dirs: list[str] = []
        self.target_extensions: list[str] = []
        self.file_cleanup_hour: int = 1
        self.app_start_time = datetime.now(ZoneInfo("Asia/Tokyo"))
        self._load_settings()

    def _load_settings(self) -> None:
        """設定ファイルから対象ディレクトリと拡張子を読み込む"""
        self.target_dirs = self._get_target_directories()

        extensions_str = get_config_value(
            self.config, 'Settings', 'target_extensions', '*'
        )
        if extensions_str:
            extensions_str = str(extensions_str).strip()
            if extensions_str == '*':
                self.target_extensions = ['*']
            else:
                self.target_extensions = [
                    ext.strip().lower().lstrip('.')
                    for ext in extensions_str.split(',')
                    if ext.strip()
                ]

        cleanup_hour_str = get_config_value(
            self.config, 'Settings', 'file_cleanup_hour', '24'
        )
        try:
            self.file_cleanup_hour = int(cleanup_hour_str or '24')
        except (ValueError, TypeError):
            self.logger.warning(
                f"file_cleanup_hour の値が不正です: {cleanup_hour_str}。デフォルト値を使用します"
            )
            self.file_cleanup_hour = 24

        self.logger.info(f"対象ディレクトリ: {self.target_dirs}")
        self.logger.info(f"対象拡張子: {self.target_extensions}")

    def _get_target_directories(self) -> list[str]:
        """Pathsセクションからtarget_dirで始まるすべてのディレクトリを取得"""
        directories: list[str] = []

        if not self.config.has_section('Paths'):
            self.logger.warning("設定ファイルにPathsセクションがありません")
            return directories

        for key in self.config.options('Paths'):
            if key.startswith('target_dir'):
                value = self.config.get('Paths', key)
                if value and value.strip():
                    directories.append(value.strip())

        return directories

    def _is_file_old_enough(self, file_path: Path) -> bool:
        """ファイルが削除対象の期間より古いかを判定"""
        try:
            stat_info = file_path.stat()
            file_modification_time = datetime.fromtimestamp(
                stat_info.st_mtime, ZoneInfo("Asia/Tokyo")
            )
            cutoff_time = self.app_start_time - timedelta(hours=self.file_cleanup_hour)

            is_old = file_modification_time < cutoff_time

            if is_old:
                self.logger.debug(
                    f"ファイルは削除対象です: {file_path} "
                    f"(更新日時: {file_modification_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"基準時刻: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')})"
                )
            else:
                self.logger.debug(
                    f"ファイルは削除対象外です: {file_path} "
                    f"(更新日時: {file_modification_time.strftime('%Y-%m-%d %H:%M:%S')}, "
                    f"基準時刻: {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')})"
                )

            return is_old
        except (OSError, ValueError) as e:
            self.logger.warning(f"ファイル更新時刻の取得に失敗しました: {file_path} - {e}")
            return False

    def _should_delete_file(self, file_path: Path) -> bool:
        """ファイルが削除対象かどうかを判定"""
        extension_match = False

        if '*' in self.target_extensions:
            extension_match = True
        else:
            extension = file_path.suffix.lower().lstrip('.')
            extension_match = extension in self.target_extensions

        if not extension_match:
            return False

        return self._is_file_old_enough(file_path)

    def _delete_file(self, file_path: Path) -> bool:
        """ファイルを削除"""
        try:
            file_path.unlink()
            self.logger.info(f"ファイルを削除しました: {file_path}")
            return True
        except PermissionError:
            self.logger.error(f"ファイルの削除権限がありません: {file_path}")
            return False
        except OSError as e:
            self.logger.error(f"ファイル削除中にエラーが発生しました: {file_path} - {e}")
            return False

    def _delete_directory(self, dir_path: Path) -> bool:
        """ディレクトリを再帰的に削除"""
        try:
            shutil.rmtree(dir_path)
            self.logger.info(f"ディレクトリを削除しました: {dir_path}")
            return True
        except PermissionError:
            self.logger.error(f"ディレクトリの削除権限がありません: {dir_path}")
            return False
        except OSError as e:
            self.logger.error(f"ディレクトリ削除中にエラーが発生しました: {dir_path} - {e}")
            return False

    def clean_directory(self, directory: str) -> dict[str, int]:
        """
        指定されたディレクトリ内のファイルとサブフォルダを削除

        Args:
            directory: クリーンアップ対象のディレクトリパス

        Returns:
            削除結果の統計情報
        """
        result = {
            'deleted_files': 0,
            'deleted_dirs': 0,
            'failed_files': 0,
            'failed_dirs': 0,
            'skipped_files': 0
        }

        target_path = Path(directory)

        if not target_path.exists():
            self.logger.warning(f"ディレクトリが存在しません: {directory}")
            return result

        if not target_path.is_dir():
            self.logger.warning(f"指定されたパスはディレクトリではありません: {directory}")
            return result

        self.logger.info(f"クリーンアップを開始します: {directory}")

        items = list(target_path.iterdir())

        for item in items:
            if item.is_file():
                if self._should_delete_file(item):
                    if self._delete_file(item):
                        result['deleted_files'] += 1
                    else:
                        result['failed_files'] += 1
                else:
                    result['skipped_files'] += 1
                    self.logger.debug(f"削除対象外ファイルをスキップしました: {item}")

            elif item.is_dir():
                if '*' in self.target_extensions:
                    if self._delete_directory(item):
                        result['deleted_dirs'] += 1
                    else:
                        result['failed_dirs'] += 1
                else:
                    # 特定の拡張子のみ対象の場合はサブディレクトリも再帰的に処理
                    sub_result = self._clean_directory_recursive(item)
                    result['deleted_files'] += sub_result['deleted_files']
                    result['failed_files'] += sub_result['failed_files']
                    result['skipped_files'] += sub_result['skipped_files']
                    result['deleted_dirs'] += sub_result['deleted_dirs']
                    result['failed_dirs'] += sub_result['failed_dirs']

        return result

    def _clean_directory_recursive(self, directory: Path) -> dict[str, int]:
        """
        ディレクトリを再帰的にクリーンアップ

        Args:
            directory: クリーンアップ対象のディレクトリ

        Returns:
            削除結果の統計情報
        """
        result = {
            'deleted_files': 0,
            'deleted_dirs': 0,
            'failed_files': 0,
            'failed_dirs': 0,
            'skipped_files': 0
        }

        for item in directory.iterdir():
            if item.is_file():
                if self._should_delete_file(item):
                    if self._delete_file(item):
                        result['deleted_files'] += 1
                    else:
                        result['failed_files'] += 1
                else:
                    result['skipped_files'] += 1

            elif item.is_dir():
                sub_result = self._clean_directory_recursive(item)
                result['deleted_files'] += sub_result['deleted_files']
                result['failed_files'] += sub_result['failed_files']
                result['skipped_files'] += sub_result['skipped_files']
                result['deleted_dirs'] += sub_result['deleted_dirs']
                result['failed_dirs'] += sub_result['failed_dirs']

        try:
            if not any(directory.iterdir()):
                directory.rmdir()
                self.logger.info(f"空のディレクトリを削除しました: {directory}")
                result['deleted_dirs'] += 1
        except OSError:
            self.logger.debug(f"ディレクトリは空ではないため削除しませんでした: {directory}")

        return result

    def clean_all(self) -> dict[str, dict[str, int]]:
        """
        設定ファイルで指定されたすべてのディレクトリをクリーンアップ

        Returns:
            各ディレクトリの削除結果
        """
        results: dict[str, dict[str, int]] = {}

        if not self.target_dirs:
            self.logger.warning("対象ディレクトリが設定されていません")
            return results

        for directory in self.target_dirs:
            self.logger.info(f"処理中: {directory}")
            results[directory] = self.clean_directory(directory)

        return results

    def print_summary(self, results: dict[str, dict[str, int]]) -> None:
        """クリーンアップ結果のサマリを出力"""
        total_deleted_files = 0
        total_deleted_dirs = 0
        total_failed_files = 0
        total_failed_dirs = 0
        total_skipped_files = 0

        for _, result in results.items():
            total_deleted_files += result['deleted_files']
            total_deleted_dirs += result['deleted_dirs']
            total_failed_files += result['failed_files']
            total_failed_dirs += result['failed_dirs']
            total_skipped_files += result['skipped_files']

        print("\n" + "-" * 60)
        print("合計:")
        print(f"  削除したファイル: {total_deleted_files}")
        print(f"  削除したフォルダ: {total_deleted_dirs}")
        print(f"  スキップしたファイル: {total_skipped_files}")
        print(f"  失敗したファイル: {total_failed_files}")
        print(f"  失敗したフォルダ: {total_failed_dirs}")
        print("=" * 60)
