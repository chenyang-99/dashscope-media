#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dashscope_media.py — 阿里百炼（DashScope 国际版）通义万相 图片/视频生成封装

子命令：
  models                       列出支持的模型（只读，不耗额度）
  gen-image                    文生图（支持 9:16 等比例，同步返回）
  gen-video                    文生视频（异步任务，自动轮询并下载）
  gen-video-from-image         图生视频（首帧，异步轮询并下载）
  poll <task_id>               查询异步任务状态

依赖：仅 Python 3.8+ 标准库（urllib），无需 pip 安装。
Key 读取：环境变量 DASHSCOPE_API_KEY → ~/.config/company/dashscope_key.txt
端点（双区域都支持）：
  --region intl（默认）→ 国际版 https://dashscope-intl.aliyuncs.com/api/v1
  --region cn         → 国内版 https://dashscope.aliyuncs.com/api/v1
  --region <完整URL>  → 自定义端点
  或环境变量 DASHSCOPE_ENDPOINT / DASHSCOPE_REGION（intl|cn|URL）
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REGIONS = {
    "intl": "https://dashscope-intl.aliyuncs.com/api/v1",  # 国际版
    "cn": "https://dashscope.aliyuncs.com/api/v1",         # 国内版
}
BASE_URL = REGIONS["intl"]  # 默认国际版；main() 里按 --region / 环境变量调整
KEY_FILE = os.path.expanduser("~/.config/company/dashscope_key.txt")


def resolve_base_url(region):
    """解析端点：--region 参数 > 环境变量 DASHSCOPE_ENDPOINT/DASHSCOPE_REGION > 默认 intl。
    支持 intl / cn / 完整 URL 三种写法。"""
    val = region
    if not val:
        val = os.environ.get("DASHSCOPE_ENDPOINT", "") or os.environ.get("DASHSCOPE_REGION", "intl")
    val = str(val).strip()
    if val.lower() in REGIONS:
        return REGIONS[val.lower()]
    if val.lower().startswith(("http://", "https://")):
        return val.rstrip("/")
    sys.exit(f"[错误] 未知区域: {val}（可选 intl / cn，或直接传完整端点 URL）")

# 图片模型（国际版；最终可用性以调用为准）
IMAGE_MODELS = {
    "wan-2.7-image": "旗舰 4K，用 aspect-ratio（1:1,16:9,4:3,21:9,3:4,9:16,8:1,1:8）",
    "wan2.6-t2i": "推荐，宽高比 [1:4,4:1] 内自由尺寸，如 720x1280",
    "wan2.5-t2i-preview": "灵活尺寸，支持超长竖版",
    "wanx2.1-t2i-turbo": "2.1 极速版（旧协议，固定档位）",
    "wanx2.1-t2i-plus": "2.1 专业版（旧协议）",
}
# 视频模型（文生视频 t2v / 图生视频 i2v）
VIDEO_MODELS = {
    "wan2.7-t2v": "2.7 文生视频（新协议，2-15s，1080P）",
    "wan2.6-t2v": "2.6 文生视频（推荐）",
    "wan2.5-t2v": "2.5 文生视频",
    "wan2.7-i2v": "2.7 图生视频（首帧/首尾帧/续写）",
    "wan2.6-i2v": "2.6 图生视频",
    "wan2.6-i2v-flash": "2.6 图生视频极速版",
}

# 旧协议图片模型（走 text2image/image-synthesis）
LEGACY_IMAGE_MODELS = {"wanx2.1-t2i-turbo", "wanx2.1-t2i-plus", "wanx2.0-t2i-turbo"}
# 新协议图片模型（走 multimodal-generation/generation）
NEW_IMAGE_MODELS = {"wan-2.7-image", "wan2.6-t2i", "wan2.5-t2i-preview"}


def normalize_size(s):
    """把 720x1280 / 720×1280 / 720*1280 统一为 width*height 格式（国际版要求）。"""
    if not s:
        return s
    import re
    return re.sub(r"[xX×*]", "*", s.strip())


def load_api_key():
    key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if key:
        return key
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            key = f.read().strip()
    except OSError as e:
        sys.exit(f"[错误] 读取 Key 文件失败: {e}\n请设置环境变量 DASHSCOPE_API_KEY 或检查 {KEY_FILE}")
    if not key:
        sys.exit("[错误] Key 文件为空")
    return key


def http_json(method, path, api_key, body=None, headers=None, timeout=60):
    url = BASE_URL + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            err = json.loads(raw)
            msg = json.dumps(err, ensure_ascii=False)
        except Exception:
            msg = raw
        sys.exit(f"[错误] HTTP {e.code} {msg}")
    except urllib.error.URLError as e:
        sys.exit(f"[错误] 网络请求失败: {e}")


def extract_image_urls(resp):
    """从多种响应结构中提取图片 URL 列表（新版/旧版兼容，去重保序）。"""
    urls = []
    output = resp.get("output") or {}
    results = output.get("results")
    if isinstance(results, list):
        for r in results:
            u = r.get("url")
            if u:
                urls.append(u)
    choices = output.get("choices")
    if isinstance(choices, list):
        for ch in choices:
            content = (ch.get("message") or {}).get("content") or []
            for item in content:
                u = item.get("image_url") or item.get("image") or item.get("url")
                if u:
                    urls.append(u)
    seen, out = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def download(url, dest_dir, suffix, index=None):
    os.makedirs(dest_dir, exist_ok=True)
    if url.endswith((".png", ".jpg", ".jpeg", ".webp")):
        ext = os.path.splitext(url)[1] or ".png"
    elif url.endswith(".mp4"):
        ext = ".mp4"
    else:
        ext = suffix
    seq = f"_{index + 1}" if index is not None else ""
    name = f"dashscope_{time.strftime('%Y%m%d_%H%M%S')}{seq}{ext}"
    path = os.path.join(dest_dir, name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dashscope-media/1.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
            f.write(r.read())
    except Exception as e:
        sys.exit(f"[错误] 下载失败: {e} | URL: {url}")
    print(f"[完成] 已保存: {path}")
    return path


# ────────────────────────── 图片 ──────────────────────────

def gen_image(args):
    api_key = load_api_key()
    if args.model == "wan-2.7-image" and not args.aspect_ratio:
        sys.exit("[错误] wan-2.7-image 必须用 --aspect-ratio（如 9:16）")
    if args.model != "wan-2.7-image" and not args.size:
        sys.exit("[错误] 必须用 --size 指定尺寸（如 720x1280 / 960x1696）")
    if args.model in LEGACY_IMAGE_MODELS:
        # 旧协议 text2image
        params = {"size": args.size, "n": args.n}
        if args.negative_prompt:
            params["negative_prompt"] = args.negative_prompt
        body = {
            "model": args.model,
            "input": {"prompt": args.prompt},
            "parameters": params,
        }
        resp = http_json("POST", "/services/aigc/text2image/image-synthesis", api_key, body)
    else:
        # 新协议 multimodal-generation
        parameters = {}
        if args.negative_prompt:
            parameters["negative_prompt"] = args.negative_prompt
        if args.model == "wan-2.7-image":
            parameters["aspect_ratio"] = args.aspect_ratio
            if args.output_resolution:
                parameters["output_resolution"] = args.output_resolution
            parameters["output_count"] = args.n
        else:
            parameters["size"] = normalize_size(args.size)
            # 数量由调用者显式指定（--n 必填），脚本不设默认
            parameters["n"] = args.n
        body = {
            "model": args.model,
            "input": {
                "messages": [
                    {"role": "user", "content": [{"text": args.prompt}]}
                ]
            },
            "parameters": parameters,
        }
        resp = http_json("POST", "/services/aigc/multimodal-generation/generation", api_key, body)

    urls = extract_image_urls(resp)
    if not urls:
        print("[提示] 未提取到图片 URL，原始响应：")
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:2000])
        return
    print(f"[生成] 共 {len(urls)} 张图片")
    for i, url in enumerate(urls):
        print(f"  [{i + 1}] URL: {url}")
        download(url, args.out_dir, ".png", index=i)


# ────────────────────────── 视频 ──────────────────────────

def submit_video(api_key, body):
    resp = http_json(
        "POST", "/services/aigc/video-generation/video-synthesis", api_key, body,
        headers={"X-DashScope-Async": "enable"},
    )
    output = resp.get("output") or {}
    task_id = output.get("task_id")
    if not task_id:
        print("[提示] 未拿到 task_id，原始响应：")
        print(json.dumps(resp, ensure_ascii=False, indent=2)[:2000])
        sys.exit(1)
    return task_id


def poll_task(api_key, task_id, max_wait=420, interval=3):
    print(f"[轮询] 任务 {task_id} 处理中（最长 {max_wait // 60} 分钟）...")
    waited = 0
    while waited < max_wait:
        resp = http_json("GET", f"/tasks/{task_id}", api_key)
        output = resp.get("output") or {}
        status = output.get("task_status", "")
        print(f"  [{waited // 60}分{waited % 60:02d}秒] 状态: {status}")
        if status in ("SUCCEEDED", "SUCCESS"):
            return output
        if status in ("FAILED", "CANCELED", "UNKNOWN", "CANCELLED"):
            print("[错误] 任务失败:",
                  output.get("code"), output.get("message") or json.dumps(output, ensure_ascii=False)[:500])
            sys.exit(1)
        time.sleep(interval)
        waited += interval
    print(f"[提示] 超时。任务仍在后台，可用以下命令查询:\n  python3 {os.path.abspath(__file__)} poll {task_id}")
    sys.exit(1)


def gen_video(args):
    api_key = load_api_key()
    params = {"duration": args.duration, "resolution": args.resolution}
    body = {
        "model": args.model,
        "input": {"prompt": args.prompt},
        "parameters": params,
    }
    task_id = submit_video(api_key, body)
    print(f"[已提交] task_id: {task_id}")
    output = poll_task(api_key, task_id)
    video_url = output.get("video_url") or output.get("url")
    if not video_url:
        print("[提示] 未拿到视频 URL：")
        print(json.dumps(output, ensure_ascii=False, indent=2)[:1500])
        return
    print(f"[生成] 视频 URL: {video_url}")
    download(video_url, args.out_dir, ".mp4")


def gen_video_from_image(args):
    api_key = load_api_key()
    params = {"duration": args.duration, "resolution": args.resolution}
    inp = {"prompt": args.prompt}
    if args.img_url:
        inp["img_url"] = args.img_url
    else:
        sys.exit("[错误] 图生视频需要 --img-url（网络图片 URL）。本地图片暂未支持，请先上传为 URL。")
    body = {"model": args.model, "input": inp, "parameters": params}
    task_id = submit_video(api_key, body)
    print(f"[已提交] task_id: {task_id}")
    output = poll_task(api_key, task_id)
    video_url = output.get("video_url") or output.get("url")
    if not video_url:
        print("[提示] 未拿到视频 URL：")
        print(json.dumps(output, ensure_ascii=False, indent=2)[:1500])
        return
    print(f"[生成] 视频 URL: {video_url}")
    download(video_url, args.out_dir, ".mp4")


def cmd_poll(args):
    api_key = load_api_key()
    output = poll_task(api_key, args.task_id, max_wait=args.max_wait or 420)
    print(json.dumps(output, ensure_ascii=False, indent=2)[:2000])


def cmd_models(_args):
    print("== 图片模型 ==")
    for m, d in IMAGE_MODELS.items():
        print(f"  {m:<24} {d}")
    print("\n== 视频模型 ==")
    for m, d in VIDEO_MODELS.items():
        print(f"  {m:<24} {d}")
    print("\n[只读] 列表来自本地配置；国际版/国内版实际可用模型以调用为准。")


def build_parser():
    p = argparse.ArgumentParser(description="阿里百炼 通义万相 图片/视频生成")
    sub = p.add_subparsers(dest="cmd")

    mp = sub.add_parser("models", help="列出支持的模型（只读）")
    mp.add_argument("--region", default=None, help="intl 国际版(默认) / cn 国内版 / 完整URL")
    mp.set_defaults(func=cmd_models)

    g = sub.add_parser("gen-image", help="文生图")
    g.add_argument("--prompt", required=True)
    g.add_argument("--model", required=True, choices=sorted(IMAGE_MODELS), help="模型（必填，自己选）")
    sizeg = g.add_mutually_exclusive_group()
    sizeg.add_argument("--size", default=None, help="尺寸 宽*高（必填其一，如 720x1280 9:16 / 960x1696 / 1280*1280）")
    sizeg.add_argument("--aspect-ratio", default=None, help="仅 wan-2.7-image 用（必填其一，如 9:16）")
    g.add_argument("--output-resolution", default=None, help="仅 wan-2.7-image: 1k/2k/4k")
    g.add_argument("--negative-prompt", default=None)
    g.add_argument("--n", type=int, required=True, help="生成数量（必填，由你决定，如 1/2/4；不设默认）")
    g.add_argument("--out-dir", required=True)
    g.add_argument("--region", default=None, help="intl 国际版(默认) / cn 国内版 / 完整URL")
    g.set_defaults(func=gen_image)

    v = sub.add_parser("gen-video", help="文生视频")
    v.add_argument("--prompt", required=True)
    v.add_argument("--model", required=True, choices=sorted(VIDEO_MODELS), help="模型（必填，自己选）")
    v.add_argument("--duration", type=int, required=True, help="时长 2-15 秒（必填）")
    v.add_argument("--resolution", required=True, help="480P/720P/1080P（必填）")
    v.add_argument("--out-dir", required=True)
    v.add_argument("--region", default=None, help="intl 国际版(默认) / cn 国内版 / 完整URL")
    v.set_defaults(func=gen_video)

    iv = sub.add_parser("gen-video-from-image", help="图生视频（首帧）")
    iv.add_argument("--prompt", required=True)
    iv.add_argument("--img-url", required=True, help="首帧图片的网络 URL")
    iv.add_argument("--model", required=True, choices=sorted(VIDEO_MODELS), help="模型（必填，自己选）")
    iv.add_argument("--duration", type=int, required=True, help="时长 2-15 秒（必填）")
    iv.add_argument("--resolution", required=True, help="480P/720P/1080P（必填）")
    iv.add_argument("--out-dir", required=True)
    iv.add_argument("--region", default=None, help="intl 国际版(默认) / cn 国内版 / 完整URL")
    iv.set_defaults(func=gen_video_from_image)

    pl = sub.add_parser("poll", help="查询异步任务")
    pl.add_argument("task_id")
    pl.add_argument("--max-wait", type=int, default=None)
    pl.add_argument("--region", default=None, help="intl 国际版(默认) / cn 国内版 / 完整URL")
    pl.set_defaults(func=cmd_poll)
    return p


def main():
    p = build_parser()
    args = p.parse_args()
    if not getattr(args, "cmd", None):
        p.print_help()
        return
    global BASE_URL
    BASE_URL = resolve_base_url(getattr(args, "region", None))
    args.func(args)


if __name__ == "__main__":
    main()
