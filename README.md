# AVDC - AI Code 简体中文增强版

## 项目说明

基于 [AVDC (yoshiko2)](https://github.com/yoshiko2/AVDC) 原始程序，通过 **AI Code** 辅助开发进行功能增强。

**⚠️ 声明：本项目仅供学习参考和测试使用，请勿用于商业用途。**

---

## 新增功能

### 2026年5月更新

#### 1. 默认启用自动翻译 🌐
- **翻译范围**：标题、简介、演员名字、标签、系列、厂商等所有文本字段
- **翻译语言**：自动识别日文和繁体中文，翻译为简体中文
- **翻译API**：使用 Google 翻译 API，支持备用方案
- **关闭方法**：`config.ini` → `[translate]` → `enabled = False`

#### 2. 增强简繁转换 📝
- 内置数百个常用词汇的简繁转换字典
- 涵盖影视、日常用语等多个领域

#### 3. 智能语言检测 🔍
- 自动识别日文假名（平假名、片假名）
- 自动识别繁体中文字符

---

### 2025年2月更新

1. **智能翻译功能** - 自动将日文标题和简介翻译为中文
2. **演员ID标准化** - NFO中使用 `<tmdbid>` 纯数字格式
3. **演员头像管理** - 自动下载演员头像到 `.actors` 文件夹
4. **仅刮削模式** - 不移动视频文件，仅生成元数据
5. **强制重新刮削** - 一键清理旧NFO并重新生成
6. **NFO格式优化** - XML转义、文本清洗、URL处理
7. **语言优先级** - 支持 sc/tc/ja/en 四种语言
8. **macOS/Linux支持** - `start.sh` 一键启动脚本

---

## 快速启动

### macOS / Linux
```bash
./start.sh
```

### Windows
直接运行 `AVDC.exe` 或 `python AVDC_Main.py`

---

## 配置文件说明

```ini
[translate]
enabled = True    # 启用翻译

[actor]
download_actor_photo = 1     # 下载演员头像
actor_photo_folder = .actors  # 演员头像文件夹

[language]
priority = sc,tc,ja          # 语言优先级
```

---

## 文件结构

```
AVDC/
├── AVDC_Main.py              # 主程序
├── config.ini                # 配置文件
├── start.sh                  # 一键启动脚本
├── Function/
│   ├── translate.py          # 翻译模块
│   ├── actor_db.py           # 演员数据库
│   └── ...
├── Getter/                   # 数据源适配器
└── Log/                      # 日志目录
```

---

## 开源声明

- **原始作者**: yoshiko2
- **增强版本**: AI Code 辅助开发
- **开源协议**: GPL-3.0

---

## 更新记录

详细更新记录请查看 [CHANGELOG.md](CHANGELOG.md)

---

**⚠️ 本项目仅供学习参考和测试使用**
