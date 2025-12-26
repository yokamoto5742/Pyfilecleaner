import logging
import sys

from service.filecleaner import FileCleaner
from utils.config_manager import load_config
from utils.log_rotation import setup_debug_logging, setup_logging


def main() -> int:
    try:
        config = load_config()

        setup_logging(config)
        setup_debug_logging(config)

        logger = logging.getLogger(__name__)
        logger.info("ファイル削除を開始します")

        cleaner = FileCleaner(config)

        if not cleaner.target_dirs:
            logger.error("対象ディレクトリが設定されていません")
            return 1

        if '*' in cleaner.target_extensions:
            print("対象: すべてのファイル")
        else:
            print(f"対象拡張子: {', '.join(cleaner.target_extensions)}")

        print(f"対象ディレクトリ: {len(cleaner.target_dirs)} 件")
        for i, dir_path in enumerate(cleaner.target_dirs, 1):
            print(f"  {i}. {dir_path}")

        results = cleaner.clean_all()
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
