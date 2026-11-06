# -*- coding: utf-8 -*-

import os
import sys
import random
import uuid
import requests
import config

headers = {
    "Authorization": f"Bearer {config.PERSONAL_BASE_TOKEN}"
}

def upload_file(file_path):
    """
    Upload a local file to Feishu Space, with optional compression.
    """
    if not os.path.exists(file_path):
        print(f"[-] 错误: 文件不存在: {file_path}", file=sys.stderr)
        return None

    temp_path = None
    upload_file_path = file_path

    # Check if compression is enabled and it is an image file
    ext = os.path.splitext(file_path)[1].lower()
    is_image = ext in ('.png', '.jpg', '.jpeg', '.bmp', '.webp')

    if config.ENABLE_COMPRESSION and is_image:
        try:
            from PIL import Image
            img = Image.open(file_path)
            w, h = img.size
            if w > config.MAX_IMAGE_WIDTH:
                print(f"    [图片优化] 原尺寸: {w}x{h}, 正在等比缩放到宽度 {config.MAX_IMAGE_WIDTH}...")
                new_w = config.MAX_IMAGE_WIDTH
                new_h = int((new_w / w) * h)

                try:
                    resample_filter = Image.Resampling.LANCZOS
                except AttributeError:
                    resample_filter = Image.ANTIALIAS

                resized_img = img.resize((new_w, new_h), resample_filter)

                # Save to a temporary file in the workspace
                temp_path = os.path.join(os.path.dirname(__file__), f"temp_upload_{uuid.uuid4().hex}{ext}")
                orig_format = img.format if img.format else "PNG"
                resized_img.save(temp_path, orig_format, optimize=True)

                upload_file_path = temp_path
                print(f"    [图片优化] 优化完成。体积: {round(os.path.getsize(file_path)/1024, 2)} KB -> {round(os.path.getsize(temp_path)/1024, 2)} KB")
        except Exception as e:
            print(f"    [!] 图片压缩处理失败 (将直接上传原图): {e}", file=sys.stderr)
            upload_file_path = file_path

    try:
        upload_url = "https://base-api.feishu.cn/open-apis/drive/v1/medias/upload_all"
        file_size = os.path.getsize(upload_file_path)
        file_name = os.path.basename(file_path) # Keep original file name for Bitable attachment view

        data = {
            "file_name": file_name,
            "parent_type": "bitable_file",
            "parent_node": config.APP_TOKEN,
            "size": str(file_size)
        }

        with open(upload_file_path, "rb") as f:
            files = {
                "file": (file_name, f, "application/octet-stream")
            }
            res = requests.post(upload_url, headers=headers, data=data, files=files, timeout=30)
            res.raise_for_status()
            res_data = res.json()

            if res_data.get("code") == 0:
                file_token = res_data.get("data", {}).get("file_token")
                return file_token
            else:
                print(f"[-] 上传 {file_name} 失败: {res_data.get('msg')} (code: {res_data.get('code')})", file=sys.stderr)
                return None
    except Exception as e:
        print(f"[-] 上传 {file_name} 发生网络错误: {e}", file=sys.stderr)
        return None
    finally:
        # Always clean up the temporary file if it was created
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                print(f"    [!] 无法删除临时文件: {e}", file=sys.stderr)


def upload_folder_files(folder_path):
    """
    Upload all files in a folder and return a list of their file_tokens.
    """
    tokens = []
    print(f"\n[+] 开始上传文件夹 {os.path.basename(folder_path)} 中的文件...")
    files = sorted([f for f in os.listdir(folder_path) if not f.startswith(".")])
    for file in files:
        file_path = os.path.join(folder_path, file)
        if os.path.isfile(file_path):
            print(f"    [上传中] {file} ...")
            file_token = upload_file(file_path)
            if file_token:
                print(f"    [已上传] {file} -> token: {file_token}")
                tokens.append(file_token)
            else:
                print(f"    [-] 上传 {file} 失败")
    return tokens

def get_all_record_ids():
    """
    Fetch all record IDs in the table, ordered by view if VIEW_ID is set.
    """
    record_ids = []
    url = f"https://base-api.feishu.cn/open-apis/bitable/v1/apps/{config.APP_TOKEN}/tables/{config.TABLE_ID}/records"
    page_token = None

    while True:
        params = {"page_size": 500}
        if config.VIEW_ID:
            params["view_id"] = config.VIEW_ID
        if page_token:
            params["page_token"] = page_token

        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            res.raise_for_status()
            res_data = res.json()
            if res_data.get("code") == 0:
                data = res_data.get("data", {})
                items = data.get("items", [])
                for item in items:
                    record_ids.append(item.get("record_id"))

                if data.get("has_more"):
                    page_token = data.get("page_token")
                else:
                    break
            else:
                print(f"[-] 获取记录列表失败: {res_data.get('msg')}", file=sys.stderr)
                break
        except Exception as e:
            print(f"[-] 获取记录列表发生网络错误: {e}", file=sys.stderr)
            break

    return record_ids

def add_bitable_record(attachment_tokens):
    """
    Insert a record (row) into Bitable.
    """
    url = f"https://base-api.feishu.cn/open-apis/bitable/v1/apps/{config.APP_TOKEN}/tables/{config.TABLE_ID}/records"
    payload = {
        "fields": {
            config.ATTACHMENT_FIELD_NAME: [{"file_token": t} for t in attachment_tokens]
        }
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        res_data = res.json()
        if res_data.get("code") == 0:
            record_id = res_data.get("data", {}).get("record", {}).get("record_id")
            return record_id
        else:
            print(f"[-] 新增行失败: {res_data.get('msg')} (code: {res_data.get('code')})", file=sys.stderr)
            return None
    except Exception as e:
        print(f"[-] 新增行发生网络错误: {e}", file=sys.stderr)
        return None

def update_bitable_record(record_id, attachment_tokens):
    """
    Update an existing record (row) in Bitable.
    """
    url = f"https://base-api.feishu.cn/open-apis/bitable/v1/apps/{config.APP_TOKEN}/tables/{config.TABLE_ID}/records/{record_id}"
    payload = {
        "fields": {
            config.ATTACHMENT_FIELD_NAME: [{"file_token": t} for t in attachment_tokens]
        }
    }

    try:
        res = requests.put(url, headers=headers, json=payload, timeout=10)
        res.raise_for_status()
        res_data = res.json()
        if res_data.get("code") == 0:
            return record_id
        else:
            print(f"[-] 更新行失败: {res_data.get('msg')} (code: {res_data.get('code')})", file=sys.stderr)
            return None
    except Exception as e:
        print(f"[-] 更新行发生网络错误: {e}", file=sys.stderr)
        return None

def main():
    print("=" * 60)
    print(" 飞书多维表格批量图片匹配上传程序 ")
    print("=" * 60)

    # 确定覆盖模式与起始行数
    start_row_num = 1
    overwrite_mode = config.OVERWRITE_EXISTING_ROWS

    if len(sys.argv) > 1:
        # 优先使用命令行参数，例如: python3 uploader.py 5 或 python3 uploader.py add
        arg = sys.argv[1].lower()
        if arg in ('add', 'a', 'append', 'false'):
            overwrite_mode = False
            print("[+] 已从命令行参数指定为【追加创建】模式，将在表格末尾追加记录。")
        else:
            try:
                start_row_num = int(sys.argv[1])
                if start_row_num < 1:
                    raise ValueError
                overwrite_mode = True
                print(f"[+] 已从命令行参数指定为【覆盖修改】模式，自第 {start_row_num} 行开始覆盖。")
            except ValueError:
                print(f"[-] 参数错误: '{sys.argv[1]}' 不是有效的行号。行号必须是大于等于 1 的正整数，或输入 'add' 开启追加模式。", file=sys.stderr)
                sys.exit(1)
    else:
        # 如果没有命令行参数，进行交互式输入
        try:
            print("[模式选择]")
            print("  - 直接回车 (默认): 不覆盖任何数据，直接在表格最末尾追加创建新行")
            print("  - 输入正整数 (如 1 或 5): 从指定行号开始覆盖修改已有数据")
            print("-" * 60)
            user_input = input("请输入起始行号 (直接回车默认追加新行): ").strip().lower()
            if not user_input:
                overwrite_mode = False
                print("[+] 已选择【追加创建】模式。")
            else:
                start_row_num = int(user_input)
                if start_row_num < 1:
                    raise ValueError
                overwrite_mode = True
                print(f"[+] 已选择【覆盖修改】模式，自第 {start_row_num} 行开始覆盖。")
        except ValueError:
            print("[-] 输入错误: 行号必须是正整数（>=1），直接回车表示追加！", file=sys.stderr)
            sys.exit(1)
        except (KeyboardInterrupt, EOFError):
            print("\n[+] 用户取消操作。")
            sys.exit(0)


    # 将解析出的运行模式和行数写回 config 中
    config.OVERWRITE_EXISTING_ROWS = overwrite_mode
    config.START_ROW_NUMBER = start_row_num

    if not (config.APP_TOKEN and config.TABLE_ID and config.PERSONAL_BASE_TOKEN):
        print("[-] 请从 config.example.json 创建 config.local.json 并填写飞书凭证。", file=sys.stderr)
        sys.exit(1)

    # 1. 自动执行图片重命名
    import rename
    if not rename.rename_materials():
        print("[-] 自动重命名失败，已终止上传！", file=sys.stderr)
        sys.exit(1)

    base_dir = config.BASE_DIR
    cover_dir = os.path.join(base_dir, config.COVER_FOLDER_NAME)

    # Check directory structure
    for d in [cover_dir]:
        if not os.path.exists(d):
            print(f"[-] 错误: 找不到封面目录: {d}", file=sys.stderr)
            sys.exit(1)

    # 2. Upload all detail images from folders
    detail_tokens_by_folder = []
    for detail_name in config.DETAIL_FOLDER_NAMES:
        detail_path = os.path.join(base_dir, detail_name)
        if not os.path.exists(detail_path):
            print(f"[-] 错误: 找不到详情页目录: {detail_path}", file=sys.stderr)
            sys.exit(1)

        tokens = upload_folder_files(detail_path)
        if not tokens:
            print(f"    [提示] 详情页文件夹 {detail_name} 中没有图片，该列配图将被忽略。")
        else:
            detail_tokens_by_folder.append(tokens)


    print(f"\n[+] 详情页图片上传完毕。已准备好 {len(detail_tokens_by_folder)} 个详情页分类。")

    # 3. Get existing records if overwrite mode is enabled
    existing_record_ids = []
    if config.OVERWRITE_EXISTING_ROWS:
        print(f"\n[+] 正在获取多维表格中的已有行列表...")
        existing_record_ids = get_all_record_ids()
        print(f"    当前表格中共有 {len(existing_record_ids)} 条已有行。")

    # 4. Get list of all cover images
    covers = sorted([f for f in os.listdir(cover_dir) if not f.startswith(".")])
    print(f"\n[+] 找到 {len(covers)} 张封面图，准备进行处理...")

    success_count = 0

    for i, cover_file in enumerate(covers):
        cover_path = os.path.join(cover_dir, cover_file)
        target_row_num = config.START_ROW_NUMBER + i
        target_idx = target_row_num - 1

        print(f"\n[{i+1}/{len(covers)}] 处理封面图: {cover_file} ...")

        # Upload cover image
        cover_token = upload_file(cover_path)
        if not cover_token:
            print(f"    [-] 封面图 {cover_file} 上传失败，跳过该行。")
            continue

        # Select one detail image randomly from each detail folder token list
        row_tokens = [cover_token]
        for tokens_list in detail_tokens_by_folder:
            row_tokens.append(random.choice(tokens_list))

        # Determine whether to update or insert
        if config.OVERWRITE_EXISTING_ROWS and target_idx < len(existing_record_ids):
            record_id = existing_record_ids[target_idx]
            print(f"    [覆盖修改] 目标为表格第 {target_row_num} 行 (Record ID: {record_id}) ...")
            res_id = update_bitable_record(record_id, row_tokens)
            if res_id:
                print(f"    [成功] 修改第 {target_row_num} 行成功! Record ID: {res_id}")
                success_count += 1
            else:
                print(f"    [-] 修改第 {target_row_num} 行失败！")
        else:
            print(f"    [追加创建] 目标为新增第 {target_row_num} 行 ...")
            res_id = add_bitable_record(row_tokens)
            if res_id:
                print(f"    [成功] 新增行成功! Record ID: {res_id}")
                success_count += 1
            else:
                print(f"    [-] 新增行失败！")

    print("\n" + "=" * 60)
    print(f" 批量上传执行完毕。成功处理行数: {success_count}/{len(covers)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
