# 广告AI生图Skill

> **上传产品图 → 指定图类型 → 自动批量生成**
> **支持小红书、抖音、B站三大平台**
> **适配火山引擎 Doubao-Seedream API**

---

## 快速开始

### 1. 配置API

在skill目录创建 `.env`：

```dotenv
IMG_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
IMG_MODEL=doubao-seedream-3-0-t2i-250415
IMG_API_KEY=your-volcengine-api-key
```

**获取API Key**：[火山引擎方舟控制台](https://console.volcengine.com/ark)

### 2. 使用示例

**上传**：产品图.jpg

**输入**：
```
小红书种草图（3张）
抖音封面（冲击钩子型，1张）
品牌KV（1张）
```

**Skill自动**：
```
→ 提取产品特征
→ 匹配模板
→ 生成Style Lock
→ 自动扩写Prompt
→ 批量生成图片
```

---

## 支持的图类型

| 类型 | 触发词 | 尺寸建议 |
|-----|-------|---------|
| 小红书种草 | 小红书、种草、KOL | 1024x1024 或 1024x1792 |
| 抖音封面 | 抖音、冲击钩子、短视频 | 1024x1792（9:16竖版） |
| B站封面 | B站、科技评测、知识科普 | 1792x1024（16:9横版） |
| 品牌KV | 品牌KV、主视觉 | 1792x1024 |
| 促销海报 | 促销、Banner、海报 | 1024x1792 |

---

## 生图脚本

```bash
# 直接Prompt生成
python3 scripts/generate_image.py --prompt "..." --size 1024x1024

# 从文件读取Prompt
python3 scripts/generate_image.py --prompt-file prompt.txt --output-dir outputs

# 使用参考图（推荐！确保产品一致性）
python3 scripts/generate_image.py --image product.jpg --prompt "..." --size 1024x1792
```

**支持的尺寸**：
- `1024x1024` - 正方形
- `1024x1792` - 竖版（9:16）
- `1792x1024` - 横版（16:9）
- `512x512` - 小尺寸

---

## 自动化流程

用户只需：**上传产品图 + 指定图类型**

Skill自动完成：
1. ✅ 产品特征提取（类型、颜色、材质、风格）
2. ✅ 模板匹配（小红书/抖音/B站）
3. ✅ Campaign Style Lock生成
4. ✅ Prompt自动扩写
5. ✅ 批量调用API生成
6. ✅ 返回图片路径

---

## 相关资源

**火山引擎官方文档**：
- [Seedream API文档](https://www.volcengine.com/docs/82379/1544825)
- [文生图最佳实践](https://www.volcengine.com/docs/82379/1544826)
- [方舟控制台](https://console.volcengine.com/ark)

**相关记忆**：
- [[integrated-marketing-methodology]]