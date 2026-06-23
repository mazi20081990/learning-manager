# 学习管家

基于AI的个性化学习系统，支持多用户、多模式、自动化学习计划生成与推送。

## 功能特性

### 核心功能
- **智能计划生成**：输入话题和学习时间，AI自动生成结构化学习计划
- **自动内容生成**：每日根据计划生成学习内容，整合网络资料
- **多渠道推送**：支持钉钉、微信公众号、Server酱推送
- **学习模式切换**：学生模式（理论理解）/ 工作模式（实践应用）

### 增强功能
- **考试系统**：单选/多选/判断题，自动评分，错题集
- **复习机制**：艾宾浩斯遗忘曲线，错题定期复习
- **图片生成**：AI自动生成手绘风格教学插图
- **多用户支持**：管理员添加用户，独立学习计划

### 高级功能
- **成就系统**：徽章、积分、学习挑战、每日打卡
- **PWA离线支持**：无网络也能学习
- **语音输入**：Web Speech API语音输入
- **OCR拍照导入**：拍照识别学习计划

## 技术架构

### 前端
- 纯HTML/CSS/JS（无框架，轻量）
- 响应式设计（手机/平板/电脑）
- 深色模式支持

### 后端
- Python Flask（轻量Web框架）
- SQLite数据库（文件型，零配置）
- APScheduler定时任务

### 外部服务
- 大模型API（支持多Key轮换）
- 秘塔搜索API（每日100次免费额度）
- Pollinations.ai图片生成（完全免费）

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/your-username/learning-manager.git
cd learning-manager
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填写你的API Keys
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 启动应用
```bash
cd backend
python run.py
```

### 5. 访问应用
打开浏览器访问 http://localhost:5000

## Docker部署

### 使用Docker Compose
```bash
cd docker
docker-compose up -d
```

### 手动构建
```bash
docker build -f docker/Dockerfile -t learning-manager .
docker run -d -p 5000:5000 --name learning-manager learning-manager
```

## 配置说明

### 必需配置
- `FLASK_SECRET_KEY`: Flask密钥
- `LLM_API_KEYS`: 大模型API Keys（支持多个，用逗号分隔）
- `LLM_API_BASE`: 大模型API地址
- `MITA_API_KEY`: 秘塔搜索API Key
- `DINGTALK_WEBHOOK`: 钉钉Webhook地址

### 可选配置
- `WECHAT_APP_ID`: 微信公众号AppID
- `WECHAT_APP_SECRET`: 微信公众号AppSecret
- `SERVERCHAN_KEY`: Server酱Key
- `GITHUB_TOKEN`: GitHub Token（用于内容托管）

## 使用指南

### 创建学习计划
1. 登录系统
2. 点击"创建计划"
3. 输入学习主题和天数
4. 选择学习模式（学生/工作）
5. 系统自动生成学习计划

### 每日学习
1. 早上8点系统自动生成学习内容
2. 8:30推送学习通知到钉钉
3. 点击链接进入学习页面
4. 学习完成后点击"已掌握"

### 提问功能
1. 在学习页面底部输入问题
2. 系统自动回答
3. 问题历史保存在侧边栏

## 成本优化

### 免费API
- **秘塔搜索**: 每日100次免费额度
- **Pollinations.ai**: 完全免费图片生成
- **大模型API**: 支持多Key轮换，优先使用免费额度

### 额度管理
- 搜索额度接近上限时自动告警
- 核心知识点优先搜索
- 提问按需搜索

## 项目结构

```
learning-manager/
├── backend/
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── models/       # 数据模型
│   │   ├── services/     # 业务逻辑
│   │   ├── utils/        # 工具类
│   │   ├── static/       # 静态文件
│   │   └── templates/    # HTML模板
│   ├── tests/            # 测试用例
│   └── run.py            # 启动文件
├── docker/               # Docker配置
├── docs/                 # 文档
├── .github/workflows/    # CI/CD
├── requirements.txt      # Python依赖
└── README.md            # 项目说明
```

## 开发计划

### 第一阶段：MVP核心功能
- [x] 计划生成
- [x] 内容生成
- [x] 推送通知
- [x] Web界面

### 第二阶段：增强功能
- [ ] 考试系统
- [ ] 复习机制
- [ ] 图片生成
- [ ] 多用户支持

### 第三阶段：高级功能
- [ ] 成就系统
- [ ] PWA离线支持
- [ ] 语音输入
- [ ] OCR拍照导入

## 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，欢迎提交Issue或联系开发者。

---

**学习管家** - 让学习更智能、更高效！
