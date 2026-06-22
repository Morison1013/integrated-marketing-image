---
name: integrated-marketing-image
description: 广告AI生图Skill - 上传产品图，指定图类型，自动批量生成**中文营销图片**。支持小红书种草、抖音封面、B站封面、品牌KV、促销海报等。自动完成产品特征提取、prompt扩写、风格锁定、批量生成全流程。**所有生成的图片必须包含中文文案、中文标语，符合中国本土营销场景。**
---

# 广告AI生图 Skill (OpenClaw 适配版)

> **核心工作流**：上传产品图 → 指定图类型 → 自动提取特征 → 自动扩写Prompt → 批量生成
> **用户只需输入**：产品图 + 图类型列表（+ 可选参考风格图）
> **Skill自动完成**：产品分析、风格匹配、prompt构建、调用API批量生成

---

## OpenClaw 工具链

本 Skill 使用 OpenClaw 以下工具完成全流程：

| 步骤 | 工具 | 作用 |
|------|------|------|
| 1. 产品特征提取 | `image` tool | 视觉分析产品图，识别类型/颜色/材质/风格 |
| 2. 参考图风格分析 | `image` tool（可选） | 分析参考图提取构图/光线/调性 |
| 3. Prompt 构建 | Agent 自身逻辑 | 模板 + 产品特征 + Style Lock → 完整 Prompt |
| 4. 图片生成 | `exec` 调用 `generate_image.py` | 调用火山引擎 Doubao-Seedream API |
| 5. 结果展示 | `image` tool 预览 | 展示生成的图片 |

---

## 核心工作流

### Step 1: 接收用户输入

```
用户上传产品图（必填）
用户指定图类型（必填）
用户上传参考风格图（可选）

示例：
"上传：飞鹤奶粉罐.jpg
指定：小红书种草图（3张）- 松弛生活、晨间仪式、自我关怀"
```

### Step 2: 产品特征提取

使用 `image` tool 分析产品图：

```
调用: image(path="用户产品图路径", prompt="分析这张产品图片，提取：1.产品类型 2.颜色/色系 3.材质 4.形状 5.品牌风格 6.关键特征 7.适合的营销调性。用JSON格式返回。")
```

### Step 3: 参考图风格分析（可选）

如果用户上传了参考图，逐张分析：

```
调用: image(path="参考图路径", prompt="分析这张小红书/抖音营销参考图的风格：1.构图方式 2.光线特点 3.色彩搭配 4.场景元素 5.情绪调性 6.文字位置。用JSON格式返回。")
```

### Step 4: Campaign Style Lock 生成

多图任务自动生成视觉一致性锁定：

```
Campaign Style Lock:
- 视觉方向：{从产品风格提取}
- 固定色板：{从产品颜色提取hex码}
- 冷暖调：{从产品氛围判断}
- 字体系统：{从品牌调性匹配}
- 背景系统：{从产品类型匹配}
- 光线系统：{从图类型匹配}
```

### Step 5: Prompt 自动扩写

根据图类型匹配对应模板，结合产品特征和 Style Lock 构建完整 Prompt。

### Step 6: 调用 API 批量生成

使用 `exec` 调用生成脚本：

```bash
cd ~/.openclaw/workspace/skills/integrated-marketing-image
python3 scripts/generate_image.py \
  --prompt "{完整Prompt}" \
  --image "{产品图路径}" \
  --size "{尺寸}" \
  --output-dir outputs/{campaign名}/ \
  --format png
```

### Step 7: 展示结果

使用 `image` tool 预览生成的图片：
```
image(path="生成的图片路径", prompt="描述这张图片的内容和风格")
```

然后用 `MEDIA:` 指令展示：
```
MEDIA:outputs/campaign/xhs_01.png
```

---

## 图类型触发词

| 图类型 | 触发词 | 模板文件 | 推荐尺寸 | 产品占比 | 留白 |
|--------|--------|---------|---------|---------|------|
| 小红书种草 | 小红书、种草、KOL | `01-xhs-seeding.json` | 2048x2732 (3:4) | 28% | ≥50% |
| 抖音封面 | 抖音、短视频封面 | `02-douyin-short-video.json` | 1440x2560 (9:16) | 40% | ≥40% |
| B站封面 | B站、哔哩哔哩 | `03-bilibili-content.json` | 2560x1440 (16:9) | 30% | ≥45% |
| 品牌KV | 品牌KV、主视觉 | `04-brand-kv.json` | 2048x2048 | 35% | ≥40% |
| 促销海报 | 促销、海报、Banner | `08-promo-banner.json` | 2560x1440 | 30% | ≥35% |
| 季节Campaign | 季节、春夏秋冬 | `09-seasonal-campaign.json` | 2048x2732 | 30% | ≥45% |
| TVC视频 | TVC、品牌广告 | `33-tvc-brand-commercial.json` | 2048x2048 | 40% | ≥30% |

---

## 尺寸规范

火山引擎 Seedream 最低像素要求：**3,686,400 px**

| 用途 | 尺寸 | 像素 | 比例 |
|------|------|------|------|
| 方图 | 1920x1920 | 3,686,400 | 1:1 |
| 高清方图 | 2048x2048 | 4,194,304 | 1:1 |
| 小红书竖版 | 2048x2732 | 5,595,136 | 3:4 |
| 抖音竖版 | 1440x2560 | 3,686,400 | 9:16 |
| B站横版 | 2560x1440 | 3,686,400 | 16:9 |
| 横版 | 2732x2048 | 5,595,136 | 4:3 |
| 4K横版 | 3840x2160 | 8,294,400 | 16:9 |

---

## GPT-Image-2 / Seedream 铁律

### 1. 颜色 hex 码
- 从产品图提取颜色 → 自动转换为 hex 码
- 小红书红 → `#FF2442` | 抖音黑 → `#000000` | B站蓝 → `#00A1D6`

### 2. 产品占比
- 小红书 → `产品占画面28%`
- 抖音 → `产品占画面40%`
- B站 → `产品占画面30%`

### 3. 留白声明
- 小红书 → `留白至少50%`
- 抖音 → `留白至少40%`
- B站 → `留白至少45%`

### 4. 否定清单（每条Prompt自动追加）
`不要添加道具、手、水印、假logo、额外文字、渐变背景`

### 5. Anti-AI 技巧（小红书种草专用）
- `iPhone 14 Pro 原相机`
- `轻微噪点、毛孔可见、不完美构图`
- `真实家居环境、略微凌乱`
- `NOT professional photography, NOT AI-generated look`

---

## Prompt 构建模板

### 小红书种草

```
小红书种草风格图片。{product_description}在{lifestyle_scene}中。
iPhone 14 Pro原相机质感，{lighting}光线，{vibe}氛围。
产品占画面28%，留白至少50%。
中文标题「{headline}」位于{text_position}。
Campaign Style Lock: {style_lock}
否定约束：不要添加道具、手、水印、假logo、额外文字、渐变背景
```

### 抖音封面

```
抖音短视频封面。{product_description}。
高视觉冲击力，{color_contrast}，{motion_elements}。
产品占画面40%，留白至少40%。
中文标题「{headline}」醒目设计。
Campaign Style Lock: {style_lock}
否定约束：不要添加复杂背景、多余元素
```

### B站封面

```
B站内容封面。{product_description}用于{content_type}视频。
{professional_style}，{style_elements}。
产品占画面30%，留白至少45%。
中文标题「{headline}」设计感强。
Campaign Style Lock: {style_lock}
否定约束：不要杂乱背景、模糊元素
```

### 品牌KV

```
品牌Campaign主视觉。{product_description}作为视觉中心。
{brand_emotion}调性，{lighting}光线，{composition}构图。
产品占画面35%，留白至少40%。
中文标语「{slogan}」位于{text_position}。
Campaign Style Lock: {style_lock}
```

---

## 执行流程示例

### 用户输入
```
上传产品图：芝华仕沙发.jpg
指定：
- 小红书种草图（3张）：松弛生活方式、真实家居、晨间仪式
- 品牌KV（1张）：高端品质
```

### Agent 自动执行

**1. 分析产品图**
```
image(path="芝华仕沙发.jpg", prompt="分析这张产品图片...")
→ 类型：头等舱沙发
→ 颜色：酒红色系 (#8B1A1A)
→ 材质：头层牛皮
→ 风格：现代简约、高端
```

**2. 生成 Style Lock**
```
Campaign Style Lock:
- 固定色板：#8B1A1A（主色）+ #F5F1E8（背景）+ #2D2D2D（文字）
- 冷暖调：warm
- 字体系统：modern sans-serif
- 光线系统：柔和漫射、自然窗光
```

**3. 构建 Prompt 并调用 API**
```bash
# 小红书-松弛生活方式
python3 scripts/generate_image.py \
  --prompt "小红书种草风格图片。头等舱真皮沙发在温馨客厅中，..." \
  --image "芝华仕沙发.jpg" \
  --size 2048x2732 \
  --output-dir outputs/sofa-campaign/

# 品牌KV
python3 scripts/generate_image.py \
  --prompt "品牌Campaign主视觉。头等舱真皮沙发作为视觉中心..." \
  --image "芝华仕沙发.jpg" \
  --size 2048x2048 \
  --output-dir outputs/sofa-campaign/
```

**4. 展示结果**
```
MEDIA:outputs/sofa-campaign/image-xxx-01.png
MEDIA:outputs/sofa-campaign/image-xxx-02.png
...
```

---

## API 配置

配置文件位置：`~/.openclaw/workspace/skills/integrated-marketing-image/.env`

```dotenv
IMG_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
IMG_MODEL=doubao-seedream-5-0-260128
IMG_API_KEY=your-api-key
```

**获取 API Key**：[火山引擎方舟控制台](https://console.volcengine.com/ark)

**模型文档**：[Seedream API](https://www.volcengine.com/docs/82379/1544825)

---

## 脚本说明

| 脚本 | 说明 | 依赖 |
|------|------|------|
| `generate_image.py` | HTTP 直接调用（推荐） | 无，仅用标准库 |
| `generate_image_sdk.py` | 使用官方 SDK | `pip install volcengine-python-sdk[ark]` |

**推荐使用 `generate_image.py`**，无需额外依赖。

### 脚本参数

```
--prompt TEXT         图片生成 Prompt（必填）
--image PATH          参考产品图路径（可选，用于图生图锁定外观）
--size SIZE           图片尺寸（可选，默认1920x1920）
--output-dir DIR      输出目录（可选，默认generated-images）
--format FORMAT       图片格式 png/jpeg/webp（可选，默认png）
--n N                 生成数量（可选，默认1）
--env-file FILE       指定.env文件（可选）
```

---

## 常见问题

| 问题 | 解决方案 |
|------|---------|
| 品牌色漂移 | 从产品图提取颜色hex码并在Prompt中指定 |
| 产品占比失控 | Prompt中明确写产品占比百分比 |
| 留白不足 | Prompt中追加留白声明 |
| 小红书太假 | 应用Anti-AI技巧（iPhone原相机、噪点等） |
| 多图不一致 | 生成Campaign Style Lock统一风格 |
| 像素不足报错 | 使用≥1920x1920的尺寸 |
| API 400错误 | 检查size参数和像素是否达标 |

---

## 输出格式模板

批量生成完成后，按以下格式汇报：

```markdown
## 🎨 生成完成

### 产品特征（自动提取）
- 产品类型：xxx
- 产品颜色：xxx
- 产品风格：xxx

### Campaign Style Lock
- 固定色板：xxx
- 冷暖调：xxx

### 生成结果
| 图类型 | 文件 | 尺寸 |
|--------|------|------|
| 小红书-松弛生活 | outputs/xxx.png | 2048x2732 |
| 抖音封面-冲击钩子 | outputs/xxx.png | 1440x2560 |
| 品牌KV-高端品质 | outputs/xxx.png | 2048x2048 |

### 图片预览
MEDIA:outputs/xxx-01.png
MEDIA:outputs/xxx-02.png
...
```
