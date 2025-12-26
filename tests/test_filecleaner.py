import configparser
import logging
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from service.filecleaner import FileCleaner


@pytest.fixture
def mock_config():
    """テスト用のConfigParserオブジェクトを作成"""
    config = configparser.ConfigParser()
    config.add_section('Paths')
    config.set('Paths', 'target_dir1', 'C:\\Users\\test\\Downloads')
    config.set('Paths', 'target_dir2', 'C:\\Users\\test\\Documents')
    config.add_section('Settings')
    config.set('Settings', 'target_extensions', 'pdf,txt,jpg')
    config.set('Settings', 'file_cleanup_hour', '24')
    return config


@pytest.fixture
def file_cleaner(mock_config):
    """FileCleaner インスタンスを作成"""
    return FileCleaner(config=mock_config)


@pytest.fixture
def mock_logger():
    """モックロガーを作成"""
    return MagicMock(spec=logging.Logger)


class TestFileCleanerInit:
    """FileCleaner の初期化に関するテスト"""

    def test_init_with_config(self, mock_config):
        """設定ファイルを渡して初期化できることを確認"""
        cleaner = FileCleaner(config=mock_config)
        assert cleaner.config == mock_config
        assert isinstance(cleaner.app_start_time, datetime)
        assert cleaner.app_start_time.tzinfo == ZoneInfo("Asia/Tokyo")

    @patch('service.filecleaner.load_config')
    def test_init_without_config(self, mock_load_config):
        """設定ファイルを渡さない場合、load_configが呼ばれることを確認"""
        mock_config = configparser.ConfigParser()
        mock_config.add_section('Paths')
        mock_config.add_section('Settings')
        mock_load_config.return_value = mock_config

        cleaner = FileCleaner()
        mock_load_config.assert_called_once()
        assert cleaner.config == mock_config

    def test_init_loads_target_directories(self, file_cleaner):
        """初期化時に対象ディレクトリが読み込まれることを確認"""
        assert len(file_cleaner.target_dirs) == 2
        assert 'C:\\Users\\test\\Downloads' in file_cleaner.target_dirs
        assert 'C:\\Users\\test\\Documents' in file_cleaner.target_dirs

    def test_init_loads_target_extensions(self, file_cleaner):
        """初期化時に対象拡張子が読み込まれることを確認"""
        assert file_cleaner.target_extensions == ['pdf', 'txt', 'jpg']

    def test_init_loads_cleanup_hour(self, file_cleaner):
        """初期化時にクリーンアップ時間が読み込まれることを確認"""
        assert file_cleaner.file_cleanup_hour == 24


class TestLoadSettings:
    """設定ファイルの読み込みに関するテスト"""

    def test_load_settings_wildcard_extension(self):
        """ワイルドカード拡張子の設定が正しく読み込まれることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', '*')
        config.set('Settings', 'file_cleanup_hour', '1')

        cleaner = FileCleaner(config=config)
        assert cleaner.target_extensions == ['*']

    def test_load_settings_multiple_extensions(self):
        """複数の拡張子が正しく読み込まれることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', 'PDF, .TXT, jpg, ')
        config.set('Settings', 'file_cleanup_hour', '24')

        cleaner = FileCleaner(config=config)
        assert cleaner.target_extensions == ['pdf', 'txt', 'jpg']

    def test_load_settings_invalid_cleanup_hour(self):
        """不正なクリーンアップ時間の場合、デフォルト値が使用されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', 'pdf')
        config.set('Settings', 'file_cleanup_hour', 'invalid')

        cleaner = FileCleaner(config=config)
        assert cleaner.file_cleanup_hour == 24

    def test_load_settings_empty_extensions(self):
        """空の拡張子設定の場合、空のリストになることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', '')
        config.set('Settings', 'file_cleanup_hour', '24')

        cleaner = FileCleaner(config=config)
        assert cleaner.target_extensions == []


class TestGetTargetDirectories:
    """対象ディレクトリ取得に関するテスト"""

    def test_get_target_directories_multiple(self):
        """複数のディレクトリが正しく取得されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.set('Paths', 'target_dir1', 'C:\\dir1')
        config.set('Paths', 'target_dir2', 'C:\\dir2')
        config.set('Paths', 'target_dir3', 'C:\\dir3')
        config.add_section('Settings')

        cleaner = FileCleaner(config=config)
        assert len(cleaner.target_dirs) == 3
        assert 'C:\\dir1' in cleaner.target_dirs
        assert 'C:\\dir2' in cleaner.target_dirs
        assert 'C:\\dir3' in cleaner.target_dirs

    def test_get_target_directories_no_paths_section(self):
        """Pathsセクションがない場合、空のリストが返されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Settings')

        cleaner = FileCleaner(config=config)
        assert cleaner.target_dirs == []

    def test_get_target_directories_empty_values(self):
        """空の値は無視されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.set('Paths', 'target_dir1', 'C:\\valid_dir')
        config.set('Paths', 'target_dir2', '')
        config.set('Paths', 'target_dir3', '   ')
        config.add_section('Settings')

        cleaner = FileCleaner(config=config)
        assert len(cleaner.target_dirs) == 1
        assert 'C:\\valid_dir' in cleaner.target_dirs

    def test_get_target_directories_ignores_non_target_dir_keys(self):
        """target_dirで始まらないキーは無視されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.set('Paths', 'target_dir1', 'C:\\dir1')
        config.set('Paths', 'other_key', 'C:\\other')
        config.add_section('Settings')

        cleaner = FileCleaner(config=config)
        assert len(cleaner.target_dirs) == 1
        assert 'C:\\dir1' in cleaner.target_dirs


class TestIsFileOldEnough:
    """ファイル年齢判定に関するテスト"""

    def test_is_file_old_enough_old_file(self, file_cleaner, tmp_path):
        """古いファイルがTrueを返すことを確認"""
        test_file = tmp_path / "old_file.txt"
        test_file.write_text("test")

        # ファイルの更新時刻を25時間前に設定
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        test_file.touch()
        import os
        os.utime(test_file, (old_time, old_time))

        assert file_cleaner._is_file_old_enough(test_file) is True

    def test_is_file_old_enough_recent_file(self, file_cleaner, tmp_path):
        """新しいファイルがFalseを返すことを確認"""
        test_file = tmp_path / "recent_file.txt"
        test_file.write_text("test")

        # ファイルの更新時刻を1時間前に設定
        recent_time = (file_cleaner.app_start_time - timedelta(hours=1)).timestamp()
        import os
        os.utime(test_file, (recent_time, recent_time))

        assert file_cleaner._is_file_old_enough(test_file) is False

    def test_is_file_old_enough_exact_cutoff_time(self, file_cleaner, tmp_path):
        """カットオフ時刻ちょうどのファイルがFalseを返すことを確認"""
        test_file = tmp_path / "exact_file.txt"
        test_file.write_text("test")

        # ファイルの更新時刻をちょうど24時間前に設定
        cutoff_time = (file_cleaner.app_start_time - timedelta(hours=24)).timestamp()
        import os
        os.utime(test_file, (cutoff_time, cutoff_time))

        assert file_cleaner._is_file_old_enough(test_file) is False

    def test_is_file_old_enough_oserror(self, file_cleaner):
        """OSErrorが発生した場合、Falseを返すことを確認"""
        nonexistent_file = Path("C:\\nonexistent\\file.txt")
        assert file_cleaner._is_file_old_enough(nonexistent_file) is False


class TestShouldDeleteFile:
    """ファイル削除判定に関するテスト"""

    def test_should_delete_file_wildcard_match_old(self, tmp_path):
        """ワイルドカード設定で古いファイルがTrueを返すことを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', '*')
        config.set('Settings', 'file_cleanup_hour', '24')
        cleaner = FileCleaner(config=config)

        test_file = tmp_path / "any_file.xyz"
        test_file.write_text("test")
        old_time = (cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        assert cleaner._should_delete_file(test_file) is True

    def test_should_delete_file_extension_match_old(self, file_cleaner, tmp_path):
        """拡張子が一致し、古いファイルがTrueを返すことを確認"""
        test_file = tmp_path / "old_document.pdf"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        assert file_cleaner._should_delete_file(test_file) is True

    def test_should_delete_file_extension_match_recent(self, file_cleaner, tmp_path):
        """拡張子が一致しても、新しいファイルはFalseを返すことを確認"""
        test_file = tmp_path / "recent_document.pdf"
        test_file.write_text("test")
        recent_time = (file_cleaner.app_start_time - timedelta(hours=1)).timestamp()
        import os
        os.utime(test_file, (recent_time, recent_time))

        assert file_cleaner._should_delete_file(test_file) is False

    def test_should_delete_file_extension_not_match(self, file_cleaner, tmp_path):
        """拡張子が一致しないファイルはFalseを返すことを確認"""
        test_file = tmp_path / "document.docx"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        assert file_cleaner._should_delete_file(test_file) is False

    def test_should_delete_file_case_insensitive(self, file_cleaner, tmp_path):
        """拡張子の大文字小文字を区別しないことを確認"""
        test_file = tmp_path / "document.PDF"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        assert file_cleaner._should_delete_file(test_file) is True


class TestDeleteFile:
    """ファイル削除に関するテスト"""

    def test_delete_file_success(self, file_cleaner, tmp_path):
        """ファイルの削除が成功することを確認"""
        test_file = tmp_path / "delete_me.txt"
        test_file.write_text("test")

        assert test_file.exists()
        assert file_cleaner._delete_file(test_file) is True
        assert not test_file.exists()

    def test_delete_file_nonexistent(self, file_cleaner, tmp_path):
        """存在しないファイルの削除がFalseを返すことを確認"""
        test_file = tmp_path / "nonexistent.txt"

        assert file_cleaner._delete_file(test_file) is False

    @patch('pathlib.Path.unlink')
    def test_delete_file_permission_error(self, mock_unlink, file_cleaner, tmp_path):
        """PermissionErrorが発生した場合、Falseを返すことを確認"""
        mock_unlink.side_effect = PermissionError("Access denied")
        test_file = tmp_path / "protected.txt"

        assert file_cleaner._delete_file(test_file) is False

    @patch('pathlib.Path.unlink')
    def test_delete_file_os_error(self, mock_unlink, file_cleaner, tmp_path):
        """OSErrorが発生した場合、Falseを返すことを確認"""
        mock_unlink.side_effect = OSError("Disk error")
        test_file = tmp_path / "error.txt"

        assert file_cleaner._delete_file(test_file) is False


class TestDeleteDirectory:
    """ディレクトリ削除に関するテスト"""

    def test_delete_directory_success(self, file_cleaner, tmp_path):
        """ディレクトリの削除が成功することを確認"""
        test_dir = tmp_path / "delete_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        assert test_dir.exists()
        assert file_cleaner._delete_directory(test_dir) is True
        assert not test_dir.exists()

    @patch('shutil.rmtree')
    def test_delete_directory_permission_error(self, mock_rmtree, file_cleaner, tmp_path):
        """PermissionErrorが発生した場合、Falseを返すことを確認"""
        mock_rmtree.side_effect = PermissionError("Access denied")
        test_dir = tmp_path / "protected_dir"

        assert file_cleaner._delete_directory(test_dir) is False

    @patch('shutil.rmtree')
    def test_delete_directory_os_error(self, mock_rmtree, file_cleaner, tmp_path):
        """OSErrorが発生した場合、Falseを返すことを確認"""
        mock_rmtree.side_effect = OSError("Disk error")
        test_dir = tmp_path / "error_dir"

        assert file_cleaner._delete_directory(test_dir) is False


class TestCleanDirectory:
    """ディレクトリクリーンアップに関するテスト"""

    def test_clean_directory_nonexistent(self, file_cleaner):
        """存在しないディレクトリの処理結果を確認"""
        result = file_cleaner.clean_directory("C:\\nonexistent_dir")
        assert result['deleted_files'] == 0
        assert result['deleted_dirs'] == 0
        assert result['failed_files'] == 0
        assert result['failed_dirs'] == 0
        assert result['skipped_files'] == 0

    def test_clean_directory_not_a_directory(self, file_cleaner, tmp_path):
        """ディレクトリでないパスの処理結果を確認"""
        test_file = tmp_path / "not_a_dir.txt"
        test_file.write_text("test")

        result = file_cleaner.clean_directory(str(test_file))
        assert result['deleted_files'] == 0
        assert result['deleted_dirs'] == 0

    def test_clean_directory_wildcard_deletes_subdirs(self, tmp_path):
        """ワイルドカード設定でサブディレクトリが削除されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', '*')
        config.set('Settings', 'file_cleanup_hour', '24')
        cleaner = FileCleaner(config=config)

        # テストディレクトリ構造を作成
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("test")

        result = cleaner.clean_directory(str(test_dir))
        assert result['deleted_dirs'] == 1
        assert not subdir.exists()

    def test_clean_directory_deletes_old_files(self, file_cleaner, tmp_path):
        """古いファイルが削除されることを確認"""
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()

        old_file = test_dir / "old.pdf"
        old_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(old_file, (old_time, old_time))

        recent_file = test_dir / "recent.pdf"
        recent_file.write_text("test")
        recent_time = (file_cleaner.app_start_time - timedelta(hours=1)).timestamp()
        os.utime(recent_file, (recent_time, recent_time))

        result = file_cleaner.clean_directory(str(test_dir))
        assert result['deleted_files'] == 1
        assert result['skipped_files'] == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_clean_directory_skips_wrong_extension(self, file_cleaner, tmp_path):
        """拡張子が一致しないファイルがスキップされることを確認"""
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()

        wrong_ext_file = test_dir / "file.docx"
        wrong_ext_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(wrong_ext_file, (old_time, old_time))

        result = file_cleaner.clean_directory(str(test_dir))
        assert result['deleted_files'] == 0
        assert result['skipped_files'] == 1
        assert wrong_ext_file.exists()

    def test_clean_directory_recursive_with_extensions(self, file_cleaner, tmp_path):
        """特定拡張子設定でサブディレクトリが再帰的に処理されることを確認"""
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()
        subdir = test_dir / "subdir"
        subdir.mkdir()

        # サブディレクトリ内の古いファイル
        old_file = subdir / "old.pdf"
        old_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(old_file, (old_time, old_time))

        result = file_cleaner.clean_directory(str(test_dir))
        assert result['deleted_files'] == 1
        assert result['deleted_dirs'] == 1  # 空になったサブディレクトリも削除
        assert not old_file.exists()
        assert not subdir.exists()

    def test_clean_directory_file_deletion_failure(self, file_cleaner, tmp_path):
        """ファイル削除失敗時のカウント増加を確認"""
        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()

        old_file = test_dir / "old.pdf"
        old_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(old_file, (old_time, old_time))

        # ファイル削除をモックして失敗させる
        with patch.object(file_cleaner, '_delete_file', return_value=False):
            result = file_cleaner.clean_directory(str(test_dir))
            assert result['failed_files'] == 1
            assert result['deleted_files'] == 0

    def test_clean_directory_wildcard_dir_deletion_failure(self, tmp_path):
        """ワイルドカードモードでディレクトリ削除失敗時のカウント増加を確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', '*')
        config.set('Settings', 'file_cleanup_hour', '24')
        cleaner = FileCleaner(config=config)

        test_dir = tmp_path / "test_cleanup"
        test_dir.mkdir()
        subdir = test_dir / "subdir"
        subdir.mkdir()

        # ディレクトリ削除をモックして失敗させる
        with patch.object(cleaner, '_delete_directory', return_value=False):
            result = cleaner.clean_directory(str(test_dir))
            assert result['failed_dirs'] == 1
            assert result['deleted_dirs'] == 0


class TestCleanDirectoryRecursive:
    """再帰的ディレクトリクリーンアップに関するテスト"""

    def test_clean_directory_recursive_nested_structure(self, file_cleaner, tmp_path):
        """ネストしたディレクトリ構造が正しく処理されることを確認"""
        test_dir = tmp_path / "root"
        test_dir.mkdir()
        level1 = test_dir / "level1"
        level1.mkdir()
        level2 = level1 / "level2"
        level2.mkdir()

        # 各レベルにファイルを配置
        file1 = level2 / "deep.pdf"
        file1.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(file1, (old_time, old_time))

        result = file_cleaner._clean_directory_recursive(test_dir)
        assert result['deleted_files'] == 1
        assert result['deleted_dirs'] == 3  # test_dir, level1, level2 が削除される
        assert not level2.exists()
        assert not level1.exists()
        assert not test_dir.exists()

    def test_clean_directory_recursive_keeps_non_empty_dirs(self, file_cleaner, tmp_path):
        """空でないディレクトリは残されることを確認"""
        test_dir = tmp_path / "root"
        test_dir.mkdir()
        subdir = test_dir / "subdir"
        subdir.mkdir()

        # 新しいファイル（削除されない）
        recent_file = subdir / "recent.pdf"
        recent_file.write_text("test")
        recent_time = (file_cleaner.app_start_time - timedelta(hours=1)).timestamp()
        import os
        os.utime(recent_file, (recent_time, recent_time))

        result = file_cleaner._clean_directory_recursive(test_dir)
        assert result['deleted_files'] == 0
        assert result['deleted_dirs'] == 0
        assert subdir.exists()
        assert recent_file.exists()

    def test_clean_directory_recursive_mixed_files(self, file_cleaner, tmp_path):
        """削除対象と非対象のファイルが混在する場合の処理を確認"""
        test_dir = tmp_path / "root"
        test_dir.mkdir()

        # 古いPDFファイル（削除される）
        old_pdf = test_dir / "old.pdf"
        old_pdf.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(old_pdf, (old_time, old_time))

        # 新しいPDFファイル（スキップされる）
        recent_pdf = test_dir / "recent.pdf"
        recent_pdf.write_text("test")
        recent_time = (file_cleaner.app_start_time - timedelta(hours=1)).timestamp()
        os.utime(recent_pdf, (recent_time, recent_time))

        # 古いが拡張子が違うファイル（スキップされる）
        old_docx = test_dir / "old.docx"
        old_docx.write_text("test")
        os.utime(old_docx, (old_time, old_time))

        result = file_cleaner._clean_directory_recursive(test_dir)
        assert result['deleted_files'] == 1
        assert result['skipped_files'] == 2
        assert not old_pdf.exists()
        assert recent_pdf.exists()
        assert old_docx.exists()

    def test_clean_directory_recursive_file_deletion_failure(self, file_cleaner, tmp_path):
        """再帰処理中のファイル削除失敗時のカウント増加を確認"""
        test_dir = tmp_path / "root"
        test_dir.mkdir()

        old_file = test_dir / "old.pdf"
        old_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(old_file, (old_time, old_time))

        # ファイル削除をモックして失敗させる
        with patch.object(file_cleaner, '_delete_file', return_value=False):
            result = file_cleaner._clean_directory_recursive(test_dir)
            assert result['failed_files'] == 1
            assert result['deleted_files'] == 0

    def test_clean_directory_recursive_non_empty_dir_not_deleted(self, file_cleaner, tmp_path):
        """ディレクトリが空でない場合、削除されないことを確認"""
        test_dir = tmp_path / "root"
        test_dir.mkdir()

        # 新しいファイルを配置（削除されない）
        recent_file = test_dir / "recent.pdf"
        recent_file.write_text("test")
        recent_time = (file_cleaner.app_start_time - timedelta(hours=1)).timestamp()
        import os
        os.utime(recent_file, (recent_time, recent_time))

        result = file_cleaner._clean_directory_recursive(test_dir)
        # ディレクトリは空でないため削除されない
        assert result['deleted_dirs'] == 0
        assert test_dir.exists()
        assert recent_file.exists()


class TestCleanAll:
    """全ディレクトリクリーンアップに関するテスト"""

    def test_clean_all_no_target_dirs(self):
        """対象ディレクトリがない場合、空の結果が返されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        config.add_section('Settings')
        cleaner = FileCleaner(config=config)

        results = cleaner.clean_all()
        assert results == {}

    def test_clean_all_multiple_directories(self, tmp_path):
        """複数のディレクトリが処理されることを確認"""
        config = configparser.ConfigParser()
        config.add_section('Paths')
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        config.set('Paths', 'target_dir1', str(dir1))
        config.set('Paths', 'target_dir2', str(dir2))
        config.add_section('Settings')
        config.set('Settings', 'target_extensions', 'pdf')
        config.set('Settings', 'file_cleanup_hour', '24')
        cleaner = FileCleaner(config=config)

        # 各ディレクトリにファイルを配置
        file1 = dir1 / "file1.pdf"
        file1.write_text("test")
        file2 = dir2 / "file2.pdf"
        file2.write_text("test")

        old_time = (cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(file1, (old_time, old_time))
        os.utime(file2, (old_time, old_time))

        results = cleaner.clean_all()
        assert len(results) == 2
        assert str(dir1) in results
        assert str(dir2) in results
        assert results[str(dir1)]['deleted_files'] == 1
        assert results[str(dir2)]['deleted_files'] == 1


class TestPrintSummary:
    """サマリ出力に関するテスト"""

    def test_print_summary_empty_results(self, file_cleaner, capsys):
        """空の結果でサマリが出力されることを確認"""
        results = {}
        file_cleaner.print_summary(results)
        captured = capsys.readouterr()
        assert "合計:" in captured.out
        assert "削除したファイル: 0" in captured.out
        assert "削除したフォルダ: 0" in captured.out

    def test_print_summary_with_results(self, file_cleaner, capsys):
        """結果がある場合、正しいサマリが出力されることを確認"""
        results = {
            'C:\\dir1': {
                'deleted_files': 5,
                'deleted_dirs': 2,
                'failed_files': 1,
                'failed_dirs': 0,
                'skipped_files': 3
            },
            'C:\\dir2': {
                'deleted_files': 3,
                'deleted_dirs': 1,
                'failed_files': 0,
                'failed_dirs': 1,
                'skipped_files': 2
            }
        }
        file_cleaner.print_summary(results)
        captured = capsys.readouterr()
        assert "削除したファイル: 8" in captured.out
        assert "削除したフォルダ: 3" in captured.out
        assert "スキップしたファイル: 5" in captured.out
        assert "失敗したファイル: 1" in captured.out
        assert "失敗したフォルダ: 1" in captured.out


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_file_with_no_extension(self, file_cleaner, tmp_path):
        """拡張子のないファイルの処理を確認"""
        test_file = tmp_path / "noextension"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        # 拡張子が空文字列として扱われる
        assert file_cleaner._should_delete_file(test_file) is False

    def test_file_with_multiple_dots(self, file_cleaner, tmp_path):
        """複数のドットを持つファイル名の処理を確認"""
        test_file = tmp_path / "file.backup.pdf"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        # 最後の拡張子が使用される
        assert file_cleaner._should_delete_file(test_file) is True

    def test_unicode_file_names(self, file_cleaner, tmp_path):
        """Unicode文字を含むファイル名の処理を確認"""
        test_file = tmp_path / "日本語ファイル.pdf"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        assert file_cleaner._should_delete_file(test_file) is True
        assert file_cleaner._delete_file(test_file) is True
        assert not test_file.exists()

    def test_very_long_path(self, file_cleaner, tmp_path):
        """長いパスの処理を確認"""
        # Windowsの制限内で長いパスを作成
        long_name = "a" * 100
        test_file = tmp_path / f"{long_name}.pdf"
        test_file.write_text("test")
        old_time = (file_cleaner.app_start_time - timedelta(hours=25)).timestamp()
        import os
        os.utime(test_file, (old_time, old_time))

        assert file_cleaner._should_delete_file(test_file) is True

    def test_concurrent_file_modification(self, file_cleaner, tmp_path):
        """ファイルが処理中に変更された場合のエラーハンドリングを確認"""
        test_file = tmp_path / "modified.pdf"
        test_file.write_text("test")

        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.side_effect = OSError("File is being modified")
            assert file_cleaner._is_file_old_enough(test_file) is False
