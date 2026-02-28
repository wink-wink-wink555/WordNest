# WordNest 🎯

你的专属英语单词手账！(｡♥‿♥｡) 一个基于Flask的现代化个人单词学习系统，让你把那些"死活记不住"的单词都收进小窝里慢慢消化~ 支持AI智能助手、知识图谱可视化等黑科技，让背单词从此不再是噩梦！✧(≖ ◡ ≖✿)

<div align="center">
  <img src="screenshots/LOGO.jpg" alt="WordNest Logo" width="350"/>
</div>

<div align="center">

![WordNest Logo](https://img.shields.io/badge/WordNest-✨_Build_your_own_dictionary-ff69b4?style=for-the-badge)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-green?style=for-the-badge&logo=flask)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

## 💡 为什么做这个

作为一个被英语单词折磨过（其实还在被折磨...）的普通人，我试过市面上能找到的各种背单词软件... (´･ω･`)

**然而现实是残酷的：**
- 🤢 **UI设计反直觉**：要么花里胡哨找不到重点，要么丑到没眼看 😟
- 😵 **重复会的单词**：明明已经掌握的词还在刷，浪费时间又打击信心 🥺
- 📚 **海量词库迷茫**：几万个单词看得眼花，不知道该从哪下手 🥹
- ⚡ **效率感人**：学了半天发现都在重复劳动，真正需要攻克的生词没几个 😭

**忍无可忍的时候，我想：** 既然现有的都不好用，不如自己撸一个！(ง •̀_•́)ง

于是WordNest就诞生啦~ 一个真正专注于**你的生词**的单词手账，告别无效重复，让每一分钟的学习都用在刀刃上！

**开发者**: [@wink-wink-wink555](https://github.com/wink-wink-wink555) | 一个被单词软件伤害过的带学僧 (◕‿◕)

## ✨ 项目特色

### 📚 个人单词手账
- **专属词汇库**：只收录你自己添加的生词，告别无用功！(๑•̀ㅂ•́)و✧
- **智能标记系统**：星标重点单词，针对性攻克难点
- **个性化定制**：你的单词库，你做主！每个词都是你的"老对手"

### 🤖 AI智能助手
- **智能例句生成**：Ollama + Qwen本地大模型，秒出地道例句 ٩(◕‿◕)۶
- **记忆技巧助手**：AI生成记忆方法和学习笔记，让单词"过目不忘"
- **知识图谱魔法**：DeepSeek API绘制词汇关联图，发现单词间的神秘联系✨

### 🎨 颜值即正义
- **响应式设计**：流畅顺滑的界面设计，随时随地刷单词 (´∀｀)♡
- **夜间模式**：深夜背书护眼神器，再也不怕被室友嫌弃开灯啦
- **动效交互**：丝滑过渡动画，连切换单词都赏心悦目
- **键盘快捷键**：键盘侠的福音，效率满分！⚡

### 🔒 安全感满满
- **本地运行**：你的单词本只属于你，隐私100%保护 (｡◕‿◕｡)
- **离线使用**：没网也能背单词，地铁上的学习时光不浪费
- **数据导出**：CSV格式随时备份，再也不怕数据丢失的恐惧

## 📸 产品预览

来看看WordNest的真容吧！每一个界面都充满了爱~ ✨

### 🎯 单词抽查模式
随机抽取你的生词，测试记忆效果：

<div align="center">
<img src="screenshots/1.png" alt="单词抽查界面" width="600"/>
<p><em>清爽的抽查界面，专注于单词本身 (◕‿◕)</em></p>
</div>

点击显示释义，检验学习成果：

<div align="center">
<img src="screenshots/2.png" alt="查看单词释义" width="600"/>
<p><em>详细的词性、释义、例句，一目了然！</em></p>
</div>

### 📚 个人词库管理
完整的单词列表，你的学习轨迹：

<div align="center">
<img src="screenshots/3.png" alt="单词列表完整视图" width="600"/>
<p><em>展示释义的完整视图，随时回顾学习内容</em></p>
</div>

简洁模式，快速浏览：

<div align="center">
<img src="screenshots/4.png" alt="单词列表简洁视图" width="600"/>
<p><em>隐藏释义的简洁视图，测试自己的记忆</em></p>
</div>

选中单词，即时查看详情：

<div align="center">
<img src="screenshots/7.png" alt="选中单词显示详情" width="600"/>
<p><em>点击单词立即显示详情，交互超级顺滑~</em></p>
</div>

随时编辑或进入其它单词列表：

<div align="center">
<img src="screenshots/10.png" alt="管理单词列表" width="600"/>
<p><em>多单词列表支持~点击单词列表立即重命名、编辑、进入该单词列表！</em></p>
</div>

随时创建新的单词列表：

<div align="center">
<img src="screenshots/11.png" alt="创建单词列表" width="600"/>
<p><em>多单词列表支持~随时创建新的单词列表！</em></p>
</div>

### 🕸️ AI知识图谱魔法（Beta版）
DeepSeek API绘制的词汇关联图谱：

<div align="center">
<img src="screenshots/5.png" alt="知识图谱可视化" width="600"/>
<p><em>神奇的知识图谱，发现单词间的隐秘联系 ✨</em></p>
</div>

智能学习路径建议：

<div align="center">
<img src="screenshots/6.png" alt="学习路径建议" width="600"/>
<p><em>AI贴心提供学习建议，让你的学习更有方向感</em></p>
</div>

### ➕ 添加新单词
简单直观的添加界面：

<div align="center">
<img src="screenshots/8.png" alt="添加新单词界面" width="600"/>
<p><em>支持多词性、多释义，支持AI一键填充哦！</em></p>
</div>

### 🌙 夜间模式
护眼的深色主题：

<div align="center">
<img src="screenshots/9.png" alt="夜间模式界面" width="600"/>
<p><em>深夜学习也不累眼，温柔的夜间模式 (｡♥‿♥｡)</em></p>
</div>

## 🚀 快速开始

### 环境要求

- Python 3.8+ （现在的电脑基本都支持啦~ ）
- 2GB 可用磁盘空间 （给你的单词们一个温暖的家）
- DeepSeek API 用于AI魔法功能 ✨

### 安装步骤

1. **把项目抱回家** (づ｡◕‿‿◕｡)づ
```bash
git clone https://github.com/wink-wink-wink555/WordNest.git
cd WordNest
```

2. **给项目一个独立的小房间**
```bash
# Windows用户看这里 ↓
python -m venv venv
venv\Scripts\activate

# macOS/Linux用户看这里 ↓
python3 -m venv venv
source venv/bin/activate
```

3. **安装必要的工具包**
```bash
pip install -r requirements.txt
```

4. **配置API密钥**（想要AI功能就配置一下哦~）

  项目使用 `config.py` 进行配置管理。编辑 `config.py` 文件，将默认值改为你的配置：
  
```python
DEEPSEEK_API_KEY = '你的密钥'
```

5. **启动你的单词小窝** ✨
```bash
python app.py
```

6. **开始你的单词手账之旅**
   
   打开浏览器访问：http://127.0.0.1:5000
   
   恭喜！你的专属单词手账上线啦！(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧

## 📖 使用指南

### 📝 你的专属单词手账

这不是普通的背单词软件哦！这是你的私人单词收藏夹~  (◕‿◕)♡

**核心理念**：只收录你亲手添加的"不会"单词，告别海量词库的迷茫！每个词都是你的"老对手"，通过反复温习来彻底拿下它们！

#### 🎯 学习模式
- 🎲 **随机测试**：从你的词汇库中随机抽取单词，每次都是惊喜！
- ⭐ **标记重点**：星标那些"死活记不住"的单词，重点攻克
- 📖 **查看释义**：空格键一键显示/隐藏，测试自己的记忆效果
- ⏭️ **无限切换**：方向键快速切换，刷单词上瘾停不下来

#### ⌨️ 快捷键小贴士
- `空格键`：显示/隐藏释义（最常用！）
- `→`：下一个单词  
- `←`：查看单词详细信息
- `Esc`：关闭弹窗

### 📚 个人词库管理

#### 词汇收集
- ➕ **添加生词**：遇到不会的单词马上收录，支持多词性、多释义
- ✏️ **完善信息**：随时编辑单词信息，让你的词库越来越丰富
- 🗑️ **清理单词**：已经掌握的单词可以移除，保持词库精简
- 🔍 **快速定位**：按字母索引快速找到目标单词

#### 🤖 AI学习助手
- 🧠 **Ollama + Qwen例句生成**：本地AI为你的单词量身定制地道例句 
- 💡 **智能记忆技巧**：AI分析单词特点，提供个性化记忆方法
- 🕸️ **DeepSeek知识图谱**：可视化展示单词间的关联，发现学习规律

### 📊 数据管理

#### 备份与分享
- 📤 **CSV导出**：把你的词汇库导出分享给小伙伴，一起进步！
- 📥 **数据安全**：定期备份你的学习成果，再也不怕重装系统啦
- ⚙️ **个性化设置**：你的偏好你做主，系统贴心记录每个细节

## 🏗️ 项目架构

本项目采用**现代化分层架构设计**，代码结构清晰，易于维护和扩展：

```
WordNest/
├── 📄 app.py                    # Flask应用主入口（应用工厂模式）
├── ⚙️ config.py                 # 应用配置管理
├── 🗃️ models.py                 # 数据库模型定义
│
├── 📁 routes/                   # 🎯 路由层（BluePrints）
│   ├── __init__.py              # 路由模块初始化
│   ├── word_routes.py           # 单词CRUD + 自测功能
│   ├── graph_routes.py          # 知识图谱展示
│   └── api_routes.py            # RESTful API接口
│
├── 📁 services/                 # 💼 服务层（业务逻辑）
│   ├── __init__.py              # 服务模块初始化
│   ├── word_service.py          # 单词业务逻辑
│   ├── llm_service.py           # LLM AI服务
│   └── graph_service.py         # 知识图谱服务
│
├── 📁 utils/                    # 🛠️ 工具模块
│   ├── __init__.py              # 工具模块初始化
│   ├── constants.py             # 常量定义
│   └── settings.py              # 设置文件管理
│
├── 📁 static/                   # 🎨 静态资源
│   ├── style.css                # 样式文件
│   ├── script.js                # 主要脚本
│   └── js/
│       └── vis-network.min.js   # 图谱可视化库
│
├── 📁 templates/                # 🖼️ HTML模板
│   ├── index.html               # 主页面（单词自测）
│   ├── word_list.html           # 词汇列表
│   ├── add_word.html            # 添加单词
│   ├── add_definition.html      # 添加释义
│   ├── edit_word.html           # 编辑单词
│   └── knowledge_graph.html     # 知识图谱
│
├── 📁 instance/                 # 🗄️ 数据库文件夹
│   └── words.db                 # SQLite数据库
│
├── ⚙️ settings.json             # 应用设置（本地生成）
├── 📋 settings.example.json     # 设置模板
├── 🚫 .gitignore                # Git忽略规则
├── 📋 requirements.txt          # Python依赖
└── 📖 README.md                 # 项目文档
```

### 🎯 架构亮点

**三层架构模式 - 关注点分离**

1. **路由层（Routes）**
   - 处理HTTP请求和响应
   - 参数验证和错误处理
   - 使用Flask Blueprint模块化管理

2. **服务层（Services）**
   - 封装核心业务逻辑
   - 可复用的功能模块
   - 与路由层解耦，提高可测试性

3. **数据层（Models）**
   - SQLAlchemy ORM数据模型
   - 数据库操作封装
   - 支持多种数据库切换

**设计优势** ✨
- 📦 **模块化**：各层职责清晰，易于理解
- 🔧 **可维护**：代码组织合理，修改影响小
- 🧪 **可测试**：业务逻辑独立，方便单元测试
- 🚀 **可扩展**：添加新功能只需扩展对应层

## 🔧 AI魔法配置

想要解锁AI超能力？来来来，按步骤配置就好啦~ ✨

### 🧠 本地AI助手设置 (Ollama + Qwen)

让AI在你的电脑里安家，生成专属例句和学习笔记：

1. **安装Ollama** (本地AI的家园)
```bash
# 访问 https://ollama.com/ 下载安装包
# 就像安装普通软件一样，点点点就好 (◡‿◡)
   
# 安装完后，下载超聪明的Qwen模型
ollama pull qwen2.5:3b
```

2. **配置DeepSeek API** (知识图谱魔法师)

编辑 `config.py` 文件，将默认值改为你的配置~

```python
DEEPSEEK_API_KEY = '你的密钥'
```

### 数据库配置

默认使用SQLite，支持其他数据库：

```bash
# PostgreSQL示例
DATABASE_URI=postgresql://username:password@localhost/wordnest

# MySQL示例  
DATABASE_URI=mysql://username:password@localhost/wordnest
```

### 部署配置

生产环境部署使用Gunicorn：

```bash
# 安装gunicorn（已包含在requirements.txt中）
pip install gunicorn

# 启动生产服务器
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 🤝 贡献指南

欢迎为WordNest贡献代码！请遵循以下步骤：

### 开发环境设置

1. **Fork本仓库**
2. **创建功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **安装开发依赖**
   ```bash
   pip install pytest pytest-flask black flake8
   ```
4. **运行测试**
   ```bash
   pytest
   ```
5. **代码格式化**
   ```bash
   black .
   flake8 .
   ```

### 🏗️ 架构开发指南

如果您想为项目添加新功能，请遵循以下分层架构原则：

**1. 添加新的业务功能**
```
步骤1: 在 services/ 中创建或扩展服务类
步骤2: 在 routes/ 中添加对应的路由处理
步骤3: 如需新页面，在 templates/ 添加模板
步骤4: 更新 config.py（如有新配置项）
```

**2. 代码组织原则**
- ✅ **路由层**：只处理HTTP请求/响应，调用服务层
- ✅ **服务层**：包含所有业务逻辑，可复用
- ✅ **数据层**：只负责数据模型和数据库操作
- ❌ **避免**：在路由中直接操作数据库
- ❌ **避免**：在服务层处理HTTP请求对象

**3. 示例：添加单词收藏功能**
```python
# 步骤1: services/word_service.py
class WordService:
    @staticmethod
    def toggle_favorite(word_str):
        # 业务逻辑
        pass

# 步骤2: routes/word_routes.py
@word_bp.route('/favorite/<word>', methods=['POST'])
def favorite_word(word):
    if WordService.toggle_favorite(word):
        return jsonify({'success': True})
    return jsonify({'error': '操作失败'}), 400
```

### 提交规范

- 🎨 `feat:` 新功能
- 🐛 `fix:` Bug修复  
- 📚 `docs:` 文档更新
- 💄 `style:` 代码风格
- ♻️ `refactor:` 重构
- ⚡ `perf:` 性能优化
- 🔧 `chore:` 构建/工具

### Pull Request

1. 确保代码通过所有测试
2. 更新相关文档
3. 详细描述改动内容
4. 等待代码审查

## 🐛 问题反馈

遇到问题？请通过以下方式反馈：

1. **GitHub Issues**：[提交问题](https://github.com/wink-wink-wink555/WordNest/issues)
2. **功能建议**：在Issues中使用`enhancement`标签
3. **Bug报告**：使用Issue模板提供详细信息

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

- **Flask**：优秀的Python Web框架，让开发变得轻松愉快
- **SQLAlchemy**：强大的ORM工具，数据库操作so easy
- **Ollama**：本地大模型的守护者，让AI触手可及
- **Vis.js**：优美的图谱可视化库，让知识连接可见
- **DeepSeek**：强大的AI引擎，知识图谱的幕后英雄
- **所有英语学习者们**：项目的灵感来源，为了让背单词不再痛苦！(ง •̀_•́)ง

## 📞 联系作者

有问题想交流？想要合作？或者只是想说句"谢谢"？都欢迎联系我哦~ (◕‿◕)♡

- **📧 Email**: [yfsun.jeff@gmail.com](mailto:yfsun.jeff@gmail.com)
- **🐱 GitHub**: [wink-wink-wink555](https://github.com/wink-wink-wink555)
- **💼 LinkedIn**: [Yifei Sun](https://www.linkedin.com/in/yifei-sun-0bab66341/)
- **📺 Bilibili**: [NO_Desire](https://space.bilibili.com/623490717)

## ⭐ Star History

如果这个项目对你有帮助，请给我们一个Star！

[![Star History Chart](https://api.star-history.com/svg?repos=wink-wink-wink555/WordNest&type=Date)](https://star-history.com/#wink-wink-wink555/WordNest&Date)

---

<div align="center">

**让每一个英语学习梦想都能闪闪发光 ✨**

**记住：最好的单词本，是你亲手打造的那一本！** (｡♥‿♥｡)

Made with ❤️ for 所有被单词折磨过的同胞们

[📖 查看文档](https://github.com/wink-wink-wink555/WordNest/wiki) | [🚀 快速开始](#-快速开始) | [🤝 参与贡献](#-贡献指南)

</div> 
