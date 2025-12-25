import logging
import sys

from service.filecleaner import FileCleaner
from utils.config_manager import load_config
from utils.log_rotation import setup_debug_logging, setup_logging


def main() -> int:
    """メイン処理"""
    try:
        # 設定ファイルの読み込み
        config = load_config()

        # ログシステムの初期化
        setup_logging(config)
        setup_debug_logging(config)

        logger = logging.getLogger(__name__)
        logger.info("ファイルクリーナーを開始します")

        # ファイルクリーナーの実行
        cleaner = FileCleaner(config)

        # 対象ディレクトリが設定されているか確認
        if not cleaner.target_dirs:
            logger.error("対象ディレクトリが設定されていません")
            print("エラー: 対象ディレクトリが設定されていません")
            print("config.ini の [Paths] セクションに target_dir を設定してください")
            return 1

        # 対象拡張子の表示
        if '*' in cleaner.target_extensions:
            print("対象: すべてのファイル")
        else:
            print(f"対象拡張子: {', '.join(cleaner.target_extensions)}")

        print(f"対象ディレクトリ: {len(cleaner.target_dirs)} 件")
        for i, dir_path in enumerate(cleaner.target_dirs, 1):
            print(f"  {i}. {dir_path}")

        # クリーンアップの実行
        results = cleaner.clean_all()

        # 結果の表示
        cleaner.print_summary(results)

        logger.info("ファイルクリーナーが正常に完了しました")
        return 0

    except FileNotFoundError as e:
        print(f"エラー: {e}")
        return 1
    except PermissionError as e:
        print(f"権限エラー: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n処理が中断されました")
        return 130
    except Exception as e:
        logging.exception(f"予期しないエラーが発生しました: {e}")
        print(f"予期しないエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
