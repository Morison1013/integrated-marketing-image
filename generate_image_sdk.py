#!/usr/bin/env python3
"""火山引擎 Doubao-Seedream 图生图脚本（使用官方SDK）

使用 volcengine-python-sdk 支持图生图功能。
图片可以传入本地路径或URL。

安装依赖：pip install 'volcengine-python-sdk[ark]'

配置来自环境变量或 .env 文件：
- IMG_BASE_URL: API 根地址
- IMG_MODEL: 模型名
- IMG_API_KEY: 火山引擎 API Key
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

try:
    from volcenginesdkarkruntime import Ark
except ImportError:
    print("错误：请先安装SDK: pip install 'volcengine-python-sdk[ark]'")
    sys.exit(1)

ENV_BASE_URL = "IMG_BASE_URL"
ENV_MODEL = "IMG_MODEL"
ENV_API_KEY = "IMG_API_KEY"

# Seedream 支持的尺寸（最低像素要求：3,686,400）
VALID_SIZES = (
    "1920x1920",   # 3,686,400 ✅ 最小方图
    "2048x2048",   # 4,194,304 ✅ 高清方图
    "2048x2732",   # 5,595,136 ✅ 小红书 3:4 竖版
    "1440x2560",   # 3,686,400 ✅ 抖音 9:16 竖版
    "2560x1440",   # 3,686,400 ✅ B站/YouTube 16:9 横版
    "2732x2048",   # 5,595,136 ✅ 横版
    "3840x2160",   # 8,294,400 ✅ 4K 横版
    "1K", "2K", "4K",
)


def fail(message: str, exit_code: int = 1) -> None:
    print(f"错误：{message}", file=sys.stderr)
    raise SystemExit(exit_code)


def strip_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def find_default_env_file() -> Path | None:
    skill_env = Path(__file__).parent.parent / ".env"
    if skill_env.is_file():
        return skill_env
    for directory in (Path.cwd(), *Path.cwd().parents):
        env_file = directory / ".env"
        if env_file.is_file():
            return env_file
    return None


def load_env_file(env_file: Path | None) -> None:
    if env_file is None:
        return
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        fail(f"无法读取 .env 文件：{exc}")
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = strip_env_value(value)


def require_config(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        fail(f"缺少配置 {name}。请在 .env 中设置 IMG_BASE_URL、IMG_MODEL、IMG_API_KEY。")
    return value


def parse_size(size_arg: str) -> str:
    """解析尺寸参数，返回SDK支持的格式"""
    if size_arg.upper() in ("1K", "2K", "4K"):
        return size_arg.upper()
    # 转换像素尺寸
    if "x" in size_arg:
        return size_arg
    return size_arg


def generate_with_sdk(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    image_path: str | None,
    output_dir: Path,
    fmt: str,
) -> list[Path]:
    """使用官方SDK生成图片"""

    client = Ark(base_url=base_url, api_key=api_key)

    # 构建请求参数
    kwargs = {
        "model": model,
        "prompt": prompt,
        "size": parse_size(size),
        "output_format": fmt,
        "response_format": "url",
        "watermark": False,
    }

    # 如果有参考图片
    if image_path:
        # 判断是URL还是本地路径
        if image_path.startswith("http://") or image_path.startswith("https://"):
            kwargs["image"] = image_path
            print(f"使用参考图片URL：{image_path}", file=sys.stderr)
        else:
            # 本地文件需要上传或转为可访问的URL
            # 这里我们尝试使用base64方式（如果SDK支持）
            # 或者提示用户需要先上传图片
            path = Path(image_path)
            if not path.is_file():
                fail(f"本地图片不存在：{image_path}")

            # 读取图片并转为base64 data URL
            data = path.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            suffix = path.suffix.lower().lstrip(".")
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
            data_url = f"data:{mime.get(suffix, 'image/png')};base64,{b64}"

            kwargs["image"] = data_url
            print(f"使用本地图片（base64）：{image_path}", file=sys.stderr)

    print(f"提交生成请求... model={model}, size={size}", file=sys.stderr)

    try:
        response = client.images.generate(**kwargs)
    except Exception as exc:
        fail(f"SDK调用失败：{exc}")

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for idx, item in enumerate(response.data):
        image_url = item.url
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        p = output_dir / f"image-{timestamp}-{idx + 1:02d}.{fmt}"

        print(f"下载图片：{image_url}", file=sys.stderr)
        req = urllib.request.Request(image_url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                p.write_bytes(resp.read())
        except Exception as exc:
            fail(f"无法下载图片：{exc}")

        paths.append(p)

    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="火山引擎 Doubao-Seedream 图生图脚本（SDK版）")

    parser.add_argument("--prompt", required=True, help="图片生成 Prompt")
    parser.add_argument("--image", help="参考图片路径（本地路径或URL）")
    parser.add_argument("--output-dir", default="generated-images", help="图片输出目录")
    parser.add_argument("--env-file", help="指定 .env 配置文件")
    parser.add_argument("--size", default="1920x1920", help="图片尺寸（如 1920x1920, 2K, 4K）")
    parser.add_argument("--format", choices=("png", "jpeg", "webp"), default="png", help="图片格式")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 加载环境配置
    env_file = Path(args.env_file) if args.env_file else find_default_env_file()
    load_env_file(env_file)

    base_url = require_config(ENV_BASE_URL).rstrip("/")
    model = require_config(ENV_MODEL)
    api_key = require_config(ENV_API_KEY)

    print(f"火山引擎 Seedream SDK | model={model}", file=sys.stderr)

    paths = generate_with_sdk(
        base_url=base_url,
        api_key=api_key,
        model=model,
        prompt=args.prompt,
        size=args.size,
        image_path=args.image,
        output_dir=Path(args.output_dir),
        fmt=args.format,
    )

    print("生成完成：")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()