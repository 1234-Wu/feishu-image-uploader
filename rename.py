# -*- coding: utf-8 -*-

import os
import uuid
import sys
import config

def rename_materials():
    base_dir = config.BASE_DIR
    if not os.path.exists(base_dir):
        print(f"[-] 错误: 素材根目录不存在: {base_dir}", file=sys.stderr)
        return False

    print("[+] 开始重命名图片...")

    # Combine cover folder and detail folders to process
    target_folders = [config.COVER_FOLDER_NAME] + config.DETAIL_FOLDER_NAMES

    for folder_name in target_folders:
        folder_path = os.path.join(base_dir, folder_name)
        if not os.path.exists(folder_path):
            print(f"[-] 警告: 找不到文件夹: {folder_path}，跳过此文件夹。")
            continue

        print(f"\n[+] 处理文件夹: {folder_name}")
        rename_count = 0

        files = os.listdir(folder_path)
        for file in files:
            if file.startswith("."): # Skip hidden files like .DS_Store
                continue

            file_path = os.path.join(folder_path, file)
            # Split name and extension
            name, ext = os.path.splitext(file)

            # Check if it has already been renamed to prevent double renaming
            # If the filename starts with the folder name and contains a uuid-like pattern, skip it
            if name.startswith(folder_name + "_") and len(name) > len(folder_name) + 30:
                print(f"    [跳过] 已命名: {file}")
                continue

            new_uuid = str(uuid.uuid4())
            new_name = f"{folder_name}_{new_uuid}{ext}"
            new_file_path = os.path.join(folder_path, new_name)

            try:
                os.rename(file_path, new_file_path)
                print(f"    [重命名] {file} -> {new_name}")
                rename_count += 1
            except Exception as e:
                print(f"    [-] 重命名 {file} 失败: {e}", file=sys.stderr)

        print(f"[+] 文件夹 {folder_name} 完成。共重命名 {rename_count} 个文件。")

    print("\n[+] 重命名操作全部完成。")
    return True

if __name__ == "__main__":
    rename_materials()
