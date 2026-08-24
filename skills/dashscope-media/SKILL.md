---
name: dashscope-media
displayName: "DashScope Media — 阿里百炼通义万相图片/视频生成"
description: >
  调用阿里云百炼（DashScope 国际版/国内版）通义万相模型生成图片与视频。图片支持
  原生 9:16 / 16:9 / 1:1 等比例；视频支持文生视频、图生视频、首尾帧，
  异步任务自动轮询并下载成片。触发词："百炼"、"阿里百炼"、"通义万相"、
  "wanx"、"wan2"、"dashscope 生图/生视频"、或用图片/视频模型生成。
---

# DashScope Media — 阿里百炼 通义万相 图片/视频生成

调用**阿里云百炼**（DashScope，国际版/国内版均可）的通义万相（wanx / wan2.x）系列模型，
生成图片与视频。图片**原生支持 9:16 竖版**（短视频封面）、视频支持文生视频/图生视频，
任务完成后自动下载到本地。

## ⚠️ 敏感操作提示（必须遵守）

- 调用本 skill 会**消耗阿里百炼额度（真实扣费）**。
- **每次调用前必须先向用户明确说明"将消耗百炼额度生成 xxx"，得到用户同意后才执行**。
- 首次使用前建议先跑 `models` 子命令做一次只读检查（不消耗额度）。

## 前置条件

- **Key 文件**：`~/.config/company/dashscope_key.txt`（阿里百炼 Key，各人自己的家目录）
  - 脚本读取顺序：`DASHSCOPE_API_KEY` 环境变量 → 上述 key 文件
- **区域/端点（国际版、国内版都支持）**：
  - 国际版（默认）：`--region intl` → `https://dashscope-intl.aliyuncs.com/api/v1`
  - 国内版：`--region cn` → `https://dashscope.aliyuncs.com/api/v1`
  - 也可环境变量 `DASHSCOPE_REGION=cn|intl` 或 `DASHSCOPE_ENDPOINT=<完整URL>` 切换
  - ⚠️ 用哪个区域的 Key，就配哪个区域的端点（两边 Key 不通用）
- **依赖**：Python 3.8+，仅标准库（urllib），无需 pip 安装

## 快速上手

```bash
# 列出支持的模型（只读，不耗额度）
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py models

# 生成图片（文生图，9:16 竖版；以下参数全部必填，由你按需指定）
# 默认国际版；用国内版时加 --region cn
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py gen-image \
  --prompt "一只可爱的柴犬坐在海边，夕阳，电影感" \
  --model wan2.6-t2i \
  --size 720x1280 \
  --n 1 \
  --region cn \
  --out-dir D:/Projects/ai_media

# 生成视频（文生视频，异步自动轮询并下载；模型/时长/分辨率全部自己定）
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py gen-video \
  --prompt "一只柴犬在海边奔跑，镜头跟随" \
  --model wan2.6-t2v \
  --duration 5 \
  --resolution 720P \
  --out-dir D:/Projects/ai_media

# 查询已有任务状态
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py poll <task_id>
```

## 支持的模型

### 图片生成（通义万相）

| 模型 id | 说明 | 尺寸支持 |
|---|---|---|
| `wan-2.7-image` | 旗舰，支持 4K，`aspect_ratio` 原生比例 | `1:1,16:9,4:3,21:9,3:4,9:16,8:1,1:8` |
| `wan2.6-t2i` | 推荐，宽高比 [1:4,4:1] 内自由尺寸 | 如 `720x1280`(9:16)、`1280x720`(16:9) |
| `wan2.5-t2i-preview` | 灵活尺寸 | 支持超长竖版 |
| `wanx2.1-t2i-turbo` | 2.1 极速版（旧协议） | `1024*1024` 等固定档位 |

### 视频生成（通义万相，异步任务）

| 模型 id | 说明 |
|---|---|
| `wan2.7-t2v` | 2.7 文生视频（新协议，最长 15s，1080P） |
| `wan2.6-t2v` | 2.6 文生视频（推荐） |
| `wan2.7-i2v` | 2.7 图生视频（首帧/首尾帧/续写） |
| `wan2.6-i2v` / `wan2.6-i2v-flash` | 2.6 图生视频（含极速版） |

视频参数：时长 2–15 秒（整数）；分辨率 480P/720P/1080P；wan2.5 以上支持配音/音效、多镜头叙事。

## API 细节

### 图片 — 新版多模态接口（wan2.6+ / wan-2.7-image）

```
POST {base}/services/aigc/multimodal-generation/generation
```

```json
{
  "model": "wan2.6-t2i",
  "input": { "messages": [
    { "role": "user", "content": [ { "text": "正向提示词" } ] }
  ]},
  "parameters": { "negative_prompt": "...", "size": "720x1280" }
}
```

- `wan-2.7-image` 用 `"aspect_ratio": "9:16"`（不用 size），可选 `"output_resolution": "1k|2k|4k"`
- 默认**同步返回**；加请求头 `X-DashScope-Async: enable` 可转异步（同视频任务轮询）
- 返回 `output.results[].url`，直接下载即可

### 图片 — 旧版文生图接口（wanx2.1 等）

```
POST {base}/services/aigc/text2image/image-synthesis
```

```json
{
  "model": "wanx2.1-t2i-turbo",
  "input": { "prompt": "..." },
  "parameters": { "size": "1024*1024", "n": 1 }
}
```

### 视频 — 异步任务接口

```
POST {base}/services/aigc/video-generation/video-synthesis
```

请求头必须带 `X-DashScope-Async: enable`，返回 `{ "output": { "task_id": "..." } }`。
然后轮询（task_id 有效期 24 小时，勿重复创建）：

```
GET {base}/tasks/{task_id}
```

- `GET` 需带 `Authorization: Bearer <key>`
- 状态：`PENDING → RUNNING → SUCCEEDED`（或 `FAILED`）
- 成功返回 `output.video_url`（下载即可）；失败时 `output.code` / `output.message` 为错误原因

文生视频请求体：

```json
{
  "model": "wan2.6-t2v",
  "input": { "prompt": "..." },
  "parameters": { "duration": 5, "resolution": "720P" }
}
```

图生视频请求体（`wan2.6-i2v` / `wan2.7-i2v`）：

```json
{
  "model": "wan2.6-i2v",
  "input": {
    "prompt": "镜头缓缓上移...",
    "img_url": "https://.../first_frame.png"
  },
  "parameters": { "duration": 5 }
}
```

## 使用要点（实测经验）

- **9:16 竖版封面**：`wan2.6-t2i --size 720x1280` 或 `wan-2.7-image --aspect-ratio 9:16`，**原生比例，不要事后裁剪**（已实测：wan2.6-t2i 出图就是 720×1280）
- **图片同步返回**，一般 10–30 秒；**视频 1–5 分钟**，脚本会自动轮询（每 3 秒，最长 6 分钟），超时会打印 task_id 供手动 `poll`
- **⚠️ 实测坑 1（尺寸格式）**：国际版 `wan2.6-t2i` 的 size 要求 `width*height`（用 `*` 不是 `x`）。脚本已自动把 `720x1280` 规范化成 `720*1280`，直接传 `--size 720x1280` 即可
- **⚠️ 实测坑 2（默认多张）**：官方 `wan2.6-t2i` 不带数量参数时默认生成 **4 张**（按 4 张扣费）。脚本已把 `--n` 以及模型/尺寸/时长/分辨率**全部设为必填**——不设任何默认，每次由你显式指定，避免多扣费
- **⚠️ 实测坑 3（响应结构）**：新版接口图片 URL 在 `output.choices[].message.content[].image` 字段（不是 `url`），脚本已兼容全部结构并自动下载
- **⚠️ 实测坑 4（国际版模型不全）**：`wan-2.7-image` 在国际版报 `Model not exist`，未开通；国际版实际可用的是 **wan2.6-t2i** 等。**国内版模型通常更全**，报 `Model not exist` 时可加 `--region cn` 尝试
- **文字排版**：通义万相对中文标题渲染一般，封面含大量文字时优先考虑 gpt-image-2（RunComfy）或 Seedream
- **错误排查**：
  - `InvalidApiKey` / 401 → Key 无效或区域/端点不匹配（用哪个区域的 Key 就配哪个区域端点）
  - `InvalidParameter` / 400 → 参数格式不对（如 size 格式），看 message 提示
  - `Throttling` / 429 → 限流，稍后重试
  - `Arrearage` → 百炼账户欠费/余额不足
  - 模型不存在 → 该模型在所选区域未开通，换列表内模型或加 `--region cn`（国内版模型更全）

## 目录结构

```
dashscope-media/
├── SKILL.md                # 本说明（快速上手/模型表/实测经验）
├── API-REFERENCE.md        # ★ 参数对照表：用户必填 vs 脚本默认 + 官方文档链接
└── scripts/
    └── dashscope_media.py  # 封装脚本（标准库，无第三方依赖）
```

> **每次调用前先看 `API-REFERENCE.md`**：所有影响产出/费用的参数均为必填（无默认），由你按需指定。

## 安全说明

- Key 从本地文件读取，**不会写入任何日志或输出到对话**；脚本不做网络请求之外的对外传输
- 生成的图片/视频下载到用户指定目录，文件名带时间戳
- 本 skill 不硬编码任何密钥
