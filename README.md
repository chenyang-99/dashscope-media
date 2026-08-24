# DashScope Media — 阿里百炼通义万相 图片/视频生成 Skill

一个开源的 **Agent Skill**，封装阿里云百炼（DashScope，**国际版/国内版均可**）通义万相（wanx / wan2.x）模型，支持：
- **图片**：文生图，**原生 9:16 竖版**（短视频封面）、16:9 / 1:1 等任意宽高比
- **视频**：文生视频、图生视频、首尾帧，异步任务自动轮询并下载成片

遵循 **Agent Skills 标准**（`SKILL.md` + YAML frontmatter），**兼容 pi、Codex、Claude Code、Cursor 等所有支持该标准的 agent**——一份 skill，处处可用。

> ⚠️ 调用会**消耗阿里百炼额度（真实扣费）**，请确保账户有余额。本 skill **不包含任何密钥**，key 由各用户本地配置。

---

## ✨ 特性

| 能力 | 说明 |
|---|---|
| 🎨 原生 9:16 竖版图片 | 通义万相原生支持 9:16 等任意比例，**生成即所需尺寸**，不靠事后裁剪 |
| 🎬 视频生成 | 文生视频 / 图生视频 / 首尾帧，2–15 秒，480P~1080P |
| 📦 零依赖 | Python 标准库实现，无需 pip 安装任何包 |
| 🔒 密钥安全 | skill 内不含 key，运行时才从本地读取，分享零泄露 |
| 🔄 自动轮询 | 视频异步任务自动轮询（3 秒/次，最长 6 分钟）并下载成片 |

## 📁 目录结构

```
dashscope-media/
├── README.md                # 本说明
├── LICENSE                  # MIT 开源协议
├── package.json             # pi package 清单（pi install 用）
└── skills/
    └── dashscope-media/     # ★ 真正的 skill（复制/安装此目录）
        ├── SKILL.md         # skill 说明（触发词/快速上手/模型表/实测坑）
        ├── API-REFERENCE.md # 参数对照表 + 官方文档链接
        └── scripts/
            └── dashscope_media.py  # 核心脚本（Python 标准库）
```

---

## 📋 前置条件

1. **Python 3.8+**（仅标准库，无第三方依赖）
2. **阿里百炼 API Key**（开通通义万相模型，国际版/国内版任选其一）：
   - 获取：阿里云百炼控制台 → API-KEY（国际版用国际控制台，国内版用国内控制台）
   - 两种配置方式（任选其一）：
     - 方式 A：写入文件 `~/.config/company/dashscope_key.txt`（仅内容，无换行）
     - 方式 B：设置环境变量 `DASHSCOPE_API_KEY`
   - 脚本读取顺序：环境变量 → key 文件
   - **区域/端点**（默认国际版）：
     - 国际版：`--region intl` → `https://dashscope-intl.aliyuncs.com`
     - 国内版：`--region cn` → `https://dashscope.aliyuncs.com`
     - 也可环境变量 `DASHSCOPE_REGION=cn` / `DASHSCOPE_ENDPOINT=<完整URL>` 切换
     - ⚠️ 用哪个区域的 Key 就配哪个区域端点（两边 Key 不通用）

---

## 🚀 安装

> 本 skill 采用 **Agent Skills 标准格式**，兼容 Claude Code / Codex / Cursor / Gemini / Copilot 等 70+ agent（pi 用户见方式 3）。
> 按你的环境任选一种方式，**推荐方式 1（一行命令）**。

### 方式 1：npx skills add 一行命令（推荐，跨 70+ agent 通用）

需要 Node.js（`npx` 随 npm 自带），适合任何 agent 用户：

```bash
# 安装到指定 agent（codex / claude-code / cursor / gemini ...）
npx skills add chenyang-99/dashscope-media --skill dashscope-media --agent codex

# 装到所有支持的 agent
npx skills add chenyang-99/dashscope-media --skill dashscope-media --all

# 装到用户目录（而非项目目录）
npx skills add chenyang-99/dashscope-media --skill dashscope-media -g
```

装完重启对应 agent 即可生效。

### 方式 2：手动复制（零依赖，任何环境都行）

不需要装任何工具，直接把仓库里的 `skills/dashscope-media/` 整个目录复制到目标位置：

| Agent | 安装位置 |
|---|---|
| pi | `~/.pi/agent/skills/` |
| Codex | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` |
| 项目级（任何 agent） | 仓库内 `.agents/skills/` 或 `.pi/skills/` |

复制完成后**重启 agent** 即可生效。

### 方式 3：pi 用户（仅 pi 环境）

```bash
pi install git:github.com/chenyang-99/dashscope-media
```

（npm 发布后也可 `pi install npm:dashscope-media`）

---

## 🎯 使用说明

### 触发词

说以下任一关键词，agent 会自动加载本 skill：
> **百炼** · **阿里百炼** · **通义万相** · **wanx** · **wan2** · **dashscope 生图/生视频** · 或用图片/视频模型生成

### 命令行快速上手

```bash
# 列出支持的模型（只读，不耗额度）
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py models

# 生成图片（文生图，9:16 竖版；以下参数全部必填，由你按需指定）
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py gen-image \
  --prompt "一只可爱的柴犬坐在海边，夕阳，电影感" \
  --model wan2.6-t2i \
  --size 720x1280 \
  --n 1 \
  --out-dir D:/Projects/ai_media

# 生成视频（文生视频，异步自动轮询并下载）
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py gen-video \
  --prompt "一只柴犬在海边奔跑，镜头跟随" \
  --model wan2.6-t2v \
  --duration 5 \
  --resolution 720P \
  --out-dir D:/Projects/ai_media

# 查询已有任务状态
python3 ~/.pi/agent/skills/dashscope-media/scripts/dashscope_media.py poll <task_id>
```

> **设计原则：不设任何默认值。** 模型、尺寸、张数、时长、分辨率等所有影响产出/费用的参数均由调用者显式指定，脚本缺参直接报错，避免意外多扣费。

### 支持的模型

**图片生成（通义万相）：**

| 模型 id | 说明 | 尺寸支持 |
|---|---|---|
| `wan-2.7-image` | 旗舰，支持 4K，`aspect_ratio` 原生比例 | `1:1,16:9,4:3,21:9,3:4,9:16,8:1,1:8` |
| `wan2.6-t2i` | 推荐，宽高比 [1:4,4:1] 内自由尺寸 | 如 `720x1280`(9:16)、`1280x720`(16:9) |
| `wan2.5-t2i-preview` | 灵活尺寸 | 支持超长竖版 |
| `wanx2.1-t2i-turbo` | 2.1 极速版（旧协议） | `1024*1024` 等固定档位 |

**视频生成（通义万相，异步任务）：**

| 模型 id | 说明 |
|---|---|
| `wan2.7-t2v` | 2.7 文生视频（新协议，最长 15s，1080P） |
| `wan2.6-t2v` | 2.6 文生视频（推荐） |
| `wan2.7-i2v` | 2.7 图生视频（首帧/首尾帧/续写） |
| `wan2.6-i2v` / `wan2.6-i2v-flash` | 2.6 图生视频（含极速版） |

> ⚠️ 实测：国际版部分旗舰模型（如 `wan-2.7-image`）可能报 `Model not exist`（未开通）；国内版模型通常更全，可加 `--region cn` 尝试。

---

## ⚠️ 常见坑（实测经验）

1. **尺寸格式**：国际版 `wan2.6-t2i` 的 size 要求 `width*height`（`*` 不是 `x`）。脚本已自动把 `720x1280` 规范化成 `720*1280`，直接传 `--size 720x1280` 即可。
2. **默认多张**：官方 `wan2.6-t2i` 不带数量参数时默认生成 **4 张**（按 4 张扣费）。脚本已把 `--n` 设为必填，**无默认**，避免多扣费。
3. **响应结构**：新版接口图片 URL 在 `output.choices[].message.content[].image` 字段，脚本已兼容全部结构并自动下载。
4. **国际版模型不全**：国际版部分模型未开通，报 `Model not exist` 时可加 `--region cn` 试国内版（模型更全）或换列表内模型。
5. **文字渲染**：通义万相对中文标题渲染一般，封面含大量文字时建议用 gpt-image-2 / Seedream。

**错误排查：**
- `InvalidApiKey` / 401 → Key 无效或端点用错（检查是否用了 intl 端点）
- `InvalidParameter` / 400 → 参数格式不对（如 size 格式），看 message 提示
- `Throttling` / 429 → 限流，稍后重试
- `Arrearage` → 百炼账户欠费/余额不足

---

## 🔒 安全说明

- Key 从本地文件/环境变量读取，**不会写入任何日志或输出到对话**
- 脚本不做网络请求之外的对外传输；生成的图片/视频下载到用户指定目录
- 本 skill 不硬编码任何密钥，可安全开源分享

## 📜 协议

MIT License © 2026

---

## 💡 二次开发

- 参数细节、官方 API 文档链接见 [API-REFERENCE.md](skills/dashscope-media/API-REFERENCE.md)
- 欢迎提交 issue / PR 完善模型支持与功能
