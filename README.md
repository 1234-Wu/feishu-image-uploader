# 飞书多维表格图片批量上传工具

批量重命名和上传本地图片。每条多维表格记录包含一张封面图，并从每个详情图分类随机选取一张配图。

## 快速开始

在项目目录运行以下命令。

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp config.example.json config.local.json
```

在 `config.local.json` 填写多维表格的 `APP_TOKEN`、`TABLE_ID`、`PERSONAL_BASE_TOKEN` 和附件字段名 `ATTACHMENT_FIELD_NAME`。默认将封面放在 `data/cover/`，详情图按分类放在 `data/detail-1/`、`data/detail-2/` 和 `data/detail-3/`。目录名可在配置中修改。

```bash
python uploader.py        # 交互选择，直接回车进入追加模式
python uploader.py add    # 追加记录
python uploader.py 5      # 从现有第 5 行开始更新，超出已有行数时追加
```

上传会先重命名素材目录中的文件。只需重命名时可运行 `python rename.py`。本地配置和默认素材目录已加入 Git 忽略规则。

更多配置见 [使用指南](USAGE.md)。

## 许可证

本项目采用 [MIT 许可证](LICENSE)。
