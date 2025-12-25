"""ファイルの作成日時と更新日時を確認するデバッグスクリプト"""
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def check_file_times(directory: str) -> None:
    """指定ディレクトリ内のファイルの日時情報を表示"""
    target_path = Path(directory)
    tz = ZoneInfo("Asia/Tokyo")

    if not target_path.exists():
        print(f"ディレクトリが存在しません: {directory}")
        return

    print(f"ディレクトリ: {directory}")
    print("=" * 80)
    print(f"{'ファイル名':<40} {'作成日時':<20} {'更新日時':<20}")
    print("-" * 80)

    for item in target_path.iterdir():
        if item.is_file():
            stat_info = item.stat()

            # Windowsではst_ctimeが作成日時
            creation_time = datetime.fromtimestamp(stat_info.st_ctime, tz)
            # st_mtimeが更新日時
            modification_time = datetime.fromtimestamp(stat_info.st_mtime, tz)

            print(
                f"{item.name:<40} "
                f"{creation_time.strftime('%Y/%m/%d %H:%M:%S'):<20} "
                f"{modification_time.strftime('%Y/%m/%d %H:%M:%S'):<20}"
            )

    print("=" * 80)


if __name__ == "__main__":
    # 確認したいディレクトリを指定
    check_file_times(r"C:\Users\yokam\Downloads")
