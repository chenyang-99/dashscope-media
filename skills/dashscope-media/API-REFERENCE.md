# DashScope Media — API 参数对照表（官方文档核实版）

> 设计原则：**不设默认，全部由调用者按需显式指定**。
> 影响产出或费用的参数（模型/尺寸/张数/时长/分辨率）一律必填，脚本不替你决定；
> 只有官方本身就可选、不影响产出结构的项（如反向提示词、种子）才是可选项。
>
> 依据：阿里云百炼官方 API 参考 + 2026-08-24 国际版/国内版实测。

---

## 📚 官方 API 文档（可自查）

| 接口 | 官方文档 |
|---|---|
| 万相文生图 V2（wan2.x，multimodal-generation） | https://help.aliyun.com/zh/model-studio/text-to-image-v2-api-reference |
| 万相文生图旧版（wanx2.1，text2image） | https://help.aliyun.com/zh/model-studio/text-to-image-api-reference |
| 万相文生视频（wan2.1~2.6，video-synthesis） | https://help.aliyun.com/zh/model-studio/legacy-wan-text-to-video-api-reference |
| 万相2.7 文生视频 | https://help.aliyun.com/zh/model-studio/text-to-video-api-reference |
| 万相2.7 图生视频 | https://help.aliyun.com/zh/model-studio/image-to-video-general-api-reference |
| 异步任务查询 | `GET {base}/api/v1/tasks/{task_id}` |

---

## 🖼 gen-image（文生图）

**必须由你提供**（缺一项就拒绝生成，不落任何默认）：

| 参数 | 说明 |
|---|---|
| `--prompt` | 正向提示词（官方：中英文，≤2100 字） |
| `--model` | 模型，自己选：`wan2.6-t2i`（实测可用）/ `wan-2.7-image`（国际版未开通）/ `wan2.5-t2i-preview` / `wanx2.1-t2i-turbo` / `wanx2.1-t2i-plus` |
| `--n` | 生成张数（官方 1~4，按张计费）——生成几张由你每次定 |
| 尺寸（二选一） | `--size` 宽\*高（新协议/旧协议模型都用，如 `720x1280`、`960x1696`、`1280*1280`）；或 `--aspect-ratio`（仅 wan-2.7-image，如 `9:16`） |
| `--out-dir` | 保存目录 |
| `--region` | 区域：`intl` 国际版（默认）/ `cn` 国内版 / 完整 URL；也可环境变量 `DASHSCOPE_REGION`、`DASHSCOPE_ENDPOINT` |

**可选（官方本来就可选，不传就用官方默认）**：

| 参数 | 官方行为 |
|---|---|
| `--negative-prompt` | 反向提示词 ≤500 字，不传=无 |
| `--output-resolution` | 仅 wan-2.7-image：1k/2k/4k，不传=1k |

**脚本内置自动处理**（你不用管，也不涉及替你决策）：`720x1280` 自动转官方要求的 `720*1280`；从响应提取 URL；自动下载；文件名带时间戳。

**官方还有但脚本未暴露**（需要可加）：`prompt_extend`（默认 true）、`watermark`（默认 false）、`seed`。

---

## 🎬 gen-video（文生视频）

**必须由你提供**：

| 参数 | 说明 |
|---|---|
| `--prompt` | 正向提示词（wan2.6：≤1500 字） |
| `--model` | 自己选：`wan2.7-t2v` / `wan2.6-t2v` / `wan2.5-t2v` |
| `--duration` | 时长 2~15 秒（整数） |
| `--resolution` | 480P / 720P / 1080P（决定清晰度也决定费用） |
| `--out-dir` | 保存目录 |
| `--region` | 区域：`intl` 国际版（默认）/ `cn` 国内版 / 完整 URL |

**脚本内置自动处理**：异步提交 → 每 3 秒轮询、最长 6 分钟 → 成功后下载。超时打印 task_id 供 `poll` 手动查。

**注意**：一次任务 = 1 条视频，无张数参数；要多条就发多次任务（各自独立扣费）。

**官方可选（脚本未暴露）**：`negative_prompt`（≤500 字）、`audio_url`（配音，仅 wan2.6/2.5）。

---

## 🎞 gen-video-from-image（图生视频 / 首帧）

**必须由你提供**：

| 参数 | 说明 |
|---|---|
| `--prompt` | 运镜/动作描述 |
| `--img-url` | 首帧图片的网络 URL（暂不支持本地直传） |
| `--model` | 自己选：`wan2.7-i2v` / `wan2.6-i2v` / `wan2.6-i2v-flash` |
| `--duration` | 时长 2~15 秒 |
| `--resolution` | 480P / 720P / 1080P |
| `--out-dir` | 保存目录 |
| `--region` | 区域：`intl` 国际版（默认）/ `cn` 国内版 / 完整 URL |

---

## 🔎 poll / 📊 models

- `poll <task_id>`：task_id 必填（来自提交时打印或超时提示）
- `models`：只读，无需参数，不耗额度

---

## ⚠️ 计费提醒（实测教训）

- 官方 `wan2.6-t2i` 的 `n` 默认 **4 张**（按张计费）——脚本已把 `--n` 设为必填，杜绝多扣费
- 官方图片 size 默认 `1280*1280`（1:1）——你按需指定竖版（如 9:16）
- 官方视频默认 1080P——你按需选择 720P/1080P（清晰度=费用）
- 每次真实生成都扣费：**调用前先征求用户同意，并确认张数/时长/分辨率**
