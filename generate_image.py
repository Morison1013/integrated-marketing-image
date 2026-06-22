#!/usr/bin/env python3
"""火山引擎 Doubao-Seedream 图像生成脚本

适配火山引擎 ARK API 的 Seedream 视觉生成模型。
支持文生图和图生图（传入参考图提升产品一致性）。

配置来自环境变量或 .env 文件：
- IMG_BASE_URL: API 根地址（默认：https://ark.cn-beijing.volces.com/api/v3）
- IMG_MODEL: 模型名（默认：doubao-seedream-3-0-t2i-250415）
- IMG_API_KEY: 火山引擎 API Key

官方文档：
- https://www.volcengine.com/docs/82379/1544825
- https://www.volcengine.com/docs/82379/1544826
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ENV_BASE_URL = "IMG_BASE_URL"
ENV_MODEL = "IMG_MODEL"
ENV_API_KEY = "IMG_API_KEY"
ENV_ALIASES = {
    ENV_BASE_URL: ("ARK_BASE_URL", "VOLCENGINE_BASE_URL"),
    ENV_MODEL: ("ARK_MODEL", "SEEDREAM_MODEL"),
    ENV_API_KEY: ("ARK_API_KEY", "VOLCENGINE_API_KEY"),
}

# 火山引擎 Seedream 支持的尺寸（最低像素要求：3,686,400 = 1920×1920）
VALID_SIZES = (
    "1920x1920",   # 3,686,400 ✅ 最小方图
    "2048x2048",   # 4,194,304 ✅ 高清方图
    "2048x2732",   # 5,595,136 ✅ 小红书 3:4 竖版
    "1440x2560",   # 3,686,400 ✅ 抖音 9:16 竖版
    "2560x1440",   # 3,686,400 ✅ B站/YouTube 16:9 横版
    "2732x2048",   # 5,595,136 ✅ 横版
    "3840x2160",   # 8,294,400 ✅ 4K 横版
)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def fail(message: str, exit_code: int = 1) -> None:
    print(f"错误：{message}", file=sys.stderr)
    raise SystemExit(exit_code)


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt:
        prompt = args.prompt.strip()
    else:
        try:
            prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
        except OSError as exc:
            fail(f"无法读取 prompt 文件：{exc}")
    if not prompt:
        fail("prompt 不能为空。")
    return prompt


def strip_env_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def find_default_env_file() -> Path | None:
    # 优先查找skill目录的.env
    skill_env = Path(__file__).parent.parent / ".env"
    if skill_env.is_file():
        return skill_env
    # 再向上查找
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
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        if key not in os.environ:
            os.environ[key] = strip_env_value(value)


def require_config(name: str) -> str:
    candidates = (name, *ENV_ALIASES.get(name, ()))
    for candidate in candidates:
        value = os.environ.get(candidate, "").strip()
        if value:
            return value
    accepted = "、".join(candidates)
    fail(
        f"缺少配置 {name}。请在 .env 中设置 IMG_BASE_URL、IMG_MODEL、IMG_API_KEY；"
        f"也兼容：{accepted}。"
    )


def encode_image_base64(image_path: str) -> str:
    """将图片编码为base64"""
    path = Path(image_path)
    if not path.is_file():
        fail(f"参考图片不存在：{image_path}")

    suffix = path.suffix.lower().lstrip(".")
    mime_map = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
    }

    try:
        data = path.read_bytes()
    except OSError as exc:
        fail(f"无法读取参考图片：{exc}")

    return base64.b64encode(data).decode("ascii")


def http_post(url: str, api_key: str, payload: dict[str, Any], timeout: int = 120) -> dict[str, Any]:
    """发送POST请求"""
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": UA,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        fail(f"接口返回 HTTP {exc.code}：{detail}")
    except urllib.error.URLError as exc:
        fail(f"无法连接接口：{exc.reason}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        fail(f"接口返回的不是有效 JSON：{raw[:500]}")

    if not isinstance(parsed, dict):
        fail("接口返回格式不正确")

    return parsed


def generate_image(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    n: int,
    image_reference: str | None,
    output_dir: Path,
    fmt: str,
) -> list[Path]:
    """调用火山引擎 Seedream API 生成图片"""

    endpoint = f"{base_url}/images/generations"

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "n": n,
    }

    # 如果有参考图片，添加到payload
    # 火山引擎 Seedream 图生图接受：public URL 或 data URI
    if image_reference:
        if image_reference.startswith(("http://", "https://")):
            payload["image"] = image_reference
            print(f"使用参考图URL：{image_reference}", file=sys.stderr)
        else:
            path = Path(image_reference)
            if not path.is_file():
                fail(f"参考图片不存在：{image_reference}")
            suffix = path.suffix.lower().lstrip(".")
            mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
            mime = mime_map.get(suffix, "image/png")
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            data_uri = f"data:{mime};base64,{b64}"
            payload["image"] = data_uri
            print(f"使用参考图（data URI）：{image_reference}", file=sys.stderr)

    print(f"提交生成请求到 {endpoint}...", file=sys.stderr)
    result = http_post(endpoint, api_key, payload, timeout=120)

    # 解析返回结果
    data = result.get("data")
    if not isinstance(data, list) or not data:
        fail(f"接口返回中没有 data 图片数组：{json.dumps(result)[:300]}")

    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            fail("接口返回格式不正确：data 中包含非对象项目")

        # 处理返回的图片
        if item.get("b64_json"):
            encoded = item["b64_json"]
            try:
                image_bytes = base64.b64decode(encoded)
            except Exception as exc:
                fail(f"无法解码 b64_json 图片：{exc}")

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            p = output_dir / f"image-{timestamp}-{index + 1:02d}.{fmt}"
            p.write_bytes(image_bytes)
            paths.append(p)

        elif item.get("url"):
            image_url = item["url"]
            suffix = fmt
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            p = output_dir / f"image-{timestamp}-{index + 1:02d}.{suffix}"

            print(f"下载图片：{image_url}", file=sys.stderr)
            dl_req = urllib.request.Request(image_url, headers={"User-Agent": UA})

            try:
                with urllib.request.urlopen(dl_req, timeout=120) as resp:
                    p.write_bytes(resp.read())
            except urllib.error.URLError as exc:
                fail(f"无法下载图片：{exc.reason}")

            paths.append(p)
        else:
            fail("图片结果既没有 b64_json，也没有 url")

    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="火山引擎 Doubao-Seedream 图像生成脚本"
    )

    prompt_group = parser.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="直接传入图片生成 Prompt")
    prompt_group.add_argument("--prompt-file", help="从文本文件读取 Prompt")

    parser.add_argument("--output-dir", default="generated-images", help="图片输出目录")
    parser.add_argument("--env-file", help="指定 .env 配置文件")
    parser.add_argument("--size", default="1920x1920", choices=VALID_SIZES, help="图片尺寸（默认1920x1920）")
    parser.add_argument("--n", type=int, default=1, help="生成图片数量，默认1")
    parser.add_argument("--image", help="参考产品图片路径（用于图生图）")
    parser.add_argument("--format", choices=("png", "jpeg", "webp"), default="png", help="图片格式")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # 加载环境配置
    env_file = Path(args.env_file) if args.env_file else find_default_env_file()
    load_env_file(env_file)

    prompt = read_prompt(args)
    base_url = require_config(ENV_BASE_URL).rstrip("/")
    model = require_config(ENV_MODEL)
    api_key = require_config(ENV_API_KEY)

    print(f"火山引擎 Seedream | model={model} | size={args.size}", file=sys.stderr)

    paths = generate_image(
        base_url=base_url,
        api_key=api_key,
        model=model,
        prompt=prompt,
        size=args.size,
        n=args.n,
        image_reference=args.image,
        output_dir=Path(args.output_dir),
        fmt=args.format,
    )

    print("生成完成：")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()