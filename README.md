# 🔥 微博热搜趋势分析器

基于 GitHub Actions 的云端自动化微博热搜分析工具，集成 Claude Agent SDK 提供智能产品创意分析。

## ✨ 功能特点

- 🕐 **定时执行**：每天自动执行两次（早8点、晚8点）
- 🤖 **智能分析**：集成 Claude Agent SDK 进行深度分析
- 📊 **自动报告**：生成 Markdown 格式分析报告
- 📁 **持久化存储**：报告自动提交到仓库
- 🔔 **灵活配置**：支持手动触发和参数自定义

## 🚀 快速开始

### 1. Fork 仓库

点击右上角 Fork 按钮，将仓库 Fork 到你的 GitHub 账号。

### 2. 配置 Secrets

进入仓库 Settings → Secrets and variables → Actions → New repository secret

需要配置的 Secrets：

| Secret 名称 | 说明 | 必需 |
|------------|------|------|
| `TIANAPI_KEY` | 天API密钥 | ✅ 是 |
| `ANTHROPIC_API_KEY` | Claude API密钥 | ⭐ 推荐 |

### 3. 启用 Actions

进入仓库的 Actions 页面，点击 "I understand my workflows, go ahead and enable them"

### 4. 手动运行测试

- 进入 Actions → "微博热搜趋势分析" workflow
- 点击 "Run workflow"
- 选择参数后运行

## 📖 使用说明

### 定时执行

工作流默认在以下时间自动执行（北京时间）：
- 每天 08:00
- 每天 20:00

### 手动触发

支持以下参数：
- **hotspot_count**: 分析热搜数量（默认：10）
- **use_claude**: 是否使用Claude分析（默认：true）

### 查看报告

报告会自动保存到 `reports/` 目录，格式为：
```
reports/report_YYYYMMDD_HHMMSS.md
```

## 🔧 本地开发

```bash
# 克隆仓库
git clone https://github.com/your-username/weibo-trends-analyzer.git
cd weibo-trends-analyzer

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export TIANAPI_KEY="your_tianapi_key"
export ANTHROPIC_API_KEY="your_anthropic_key"

# 运行分析
python src/weibo_trends_analyzer.py -n 10 -o reports/test.md
```

## 📝 API 说明

### 天API

- 官网：https://www.tianapi.com/
- 接口：微博热搜榜 (`/weibohot/index`)
- 文档：https://www.tianapi.com/apiview/246

### Anthropic Claude

- 官网：https://console.anthropic.com/
- 模型：claude-sonnet-4-20250514
- 文档：https://docs.anthropic.com/

## 📄 许可证

MIT License

## 🙏 致谢

- [天API](https://www.tianapi.com/) - 提供微博热搜数据
- [Anthropic](https://www.anthropic.com/) - 提供 Claude AI 能力
- [GitHub Actions](https://github.com/features/actions) - 提供自动化执行环境
