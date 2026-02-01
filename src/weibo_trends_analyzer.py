#!/usr/bin/env python3
"""
微博热搜趋势分析器 - GitHub Actions 云端版本
支持 Claude Agent SDK 智能分析

版本: 3.0 (Cloud Edition)
作者: GitHub Actions 自动化
"""

import argparse
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import requests
import json
import re

# Claude Agent SDK 导入
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    print("⚠️ anthropic 库未安装，将使用基础分析模式")


class WeiboTrendsAnalyzer:
    """微博热搜趋势分析器"""
    
    def __init__(self, tianapi_key: str = None, anthropic_key: str = None):
        """
        初始化分析器
        
        Args:
            tianapi_key: 天API密钥（优先从环境变量获取）
            anthropic_key: Anthropic API密钥（优先从环境变量获取）
        """
        # 从环境变量或参数获取API密钥
        self.tianapi_key = tianapi_key or os.environ.get('TIANAPI_KEY')
        self.anthropic_key = anthropic_key or os.environ.get('ANTHROPIC_API_KEY')
        
        # Claude API 配置（支持第三方代理）
        self.claude_base_url = os.environ.get('CLAUDE_BASE_URL', 'https://code.newcli.com/claude/aws')
        self.claude_model = os.environ.get('CLAUDE_MODEL', 'opus')
        
        if not self.tianapi_key:
            raise ValueError("❌ 未找到天API密钥！请设置 TIANAPI_KEY 环境变量或通过参数传入")
        
        self.api_url = f"https://apis.tianapi.com/weibohot/index?key={self.tianapi_key}"
        self.hotspots: List[Dict] = []
        self.analysis_results: List[Dict] = []
        
        # 初始化 Claude 客户端（支持自定义base_url）
        self.claude_client = None
        if CLAUDE_AVAILABLE and self.anthropic_key:
            try:
                self.claude_client = anthropic.Anthropic(
                    api_key=self.anthropic_key,
                    base_url=self.claude_base_url
                )
                print(f"✅ Claude Agent SDK 已初始化")
                print(f"   API地址: {self.claude_base_url}")
                print(f"   模型: {self.claude_model}")
            except Exception as e:
                print(f"⚠️ Claude 初始化失败: {e}")
    
    def fetch_hotspots(self, limit: int = 10) -> List[Dict]:
        """
        从天API获取微博热搜榜单
        
        Args:
            limit: 获取热搜数量
            
        Returns:
            热搜列表
        """
        try:
            print(f"🔍 正在获取微博热搜数据...")
            response = requests.get(self.api_url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != 200:
                print(f"❌ API错误: {data.get('msg', '未知错误')}")
                return []
            
            result_list = data.get("result", {}).get("list", [])
            
            self.hotspots = []
            for idx, item in enumerate(result_list[:limit], 1):
                title = item.get("hotword", "").strip()
                heat_str = item.get("hotwordnum", "0").strip()
                heat = int(re.sub(r'[^\d]', '', heat_str)) if heat_str else 0
                tag = item.get("hottag", "").strip()
                
                self.hotspots.append({
                    "rank": idx,
                    "title": title,
                    "heat": heat,
                    "tag": tag
                })
            
            print(f"✅ 成功获取 {len(self.hotspots)} 条热搜")
            return self.hotspots
            
        except requests.exceptions.Timeout:
            print("❌ API请求超时")
            return []
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return []
        except Exception as e:
            print(f"❌ 获取热搜失败: {e}")
            return []
    
    def analyze_with_claude(self, hotspots: List[Dict]) -> List[Dict]:
        """
        使用 Claude Agent SDK 进行智能分析
        
        Args:
            hotspots: 热搜列表
            
        Returns:
            分析结果列表
        """
        if not self.claude_client:
            print("⚠️ Claude 不可用，使用基础分析")
            return self.analyze_basic(hotspots)
        
        print("🤖 使用 Claude Agent SDK 进行智能分析...")
        
        # 构建热搜数据
        hotspot_text = "\n".join([
            f"{h['rank']}. {h['title']} (热度: {h['heat']:,})"
            for h in hotspots
        ])
        
        prompt = f"""你是一位资深的互联网趋势分析师和产品经理。请深度分析以下微博热搜榜单，提供多维度洞察。

当前微博热搜TOP{len(hotspots)}:
{hotspot_text}

请为每个热搜提供以下深度分析：

1. **热点分类**：体育、娱乐、科技、社会、民生、消费等
2. **情感倾向**：正面、中性、负面
3. **用户画像**：主要关注人群的年龄、性别、兴趣等
4. **产品创意**：基于热点的创新产品构思（避免千篇一律的"社区"）
5. **核心功能**：产品的独特价值主张
6. **商业价值**：市场潜力、变现可能性
7. **创新点**：与现有产品的差异化
8. **综合评分**：0-100分（考虑：热度持久性、商业价值、技术可行性）

**评分标准：**
- 90-100分：具有重大商业价值和创新性
- 80-89分：优秀的产品创意，值得深入探索
- 70-79分：良好创意，但需进一步优化
- 60-69分：一般创意，商业价值有限
- 60分以下：不建议投入

**重要：**
- 避免简单的"XX话题社区"这种低价值建议
- 深挖热点背后的用户需求和痛点
- 关注跨界融合和创新模式
- 如果热点缺乏产品化价值，明确指出

请返回纯JSON数组格式：
```json
[
  {{
    "热点分类": "...",
    "情感倾向": "...",
    "用户画像": "...",
    "产品名称": "...",
    "核心功能": "...",
    "商业价值": "...",
    "创新点": "...",
    "综合评分": 85,
    "评分等级": "优秀",
    "分析洞察": "..."
  }}
]
```"""

        try:
            message = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # 解析Claude响应
            response_text = message.content[0].text
            
            # 提取JSON部分
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                analysis_data = json.loads(json_match.group())
                
                results = []
                for i, hotspot in enumerate(hotspots):
                    if i < len(analysis_data):
                        analysis = analysis_data[i]
                        results.append({
                            **hotspot,
                            'analysis': {
                                'category': analysis.get('热点分类', '未分类'),
                                'sentiment': analysis.get('情感倾向', '中性'),
                                'name': analysis.get('产品名称', f"{hotspot['title']}创意产品"),
                                'function': analysis.get('核心功能', '待分析'),
                                'users': analysis.get('用户画像', '广大用户'),
                                'business_value': analysis.get('商业价值', '待评估'),
                                'innovation': analysis.get('创新点', ''),
                                'insight': analysis.get('分析洞察', ''),
                                'score': analysis.get('综合评分', 75),
                                'grade': analysis.get('评分等级', '良好')
                            }
                        })
                    else:
                        # 如果Claude返回数量不足，使用基础分析补充
                        basic = self.analyze_hotspot_basic(hotspot['title'], hotspot['heat'])
                        results.append({**hotspot, 'analysis': basic})
                
                print(f"✅ Claude 智能分析完成")
                return results
            else:
                print("⚠️ 无法解析Claude响应，使用基础分析")
                return self.analyze_basic(hotspots)
                
        except anthropic.APIError as e:
            print(f"⚠️ Claude API错误: {e}")
            return self.analyze_basic(hotspots)
        except Exception as e:
            print(f"⚠️ Claude分析异常: {e}")
            return self.analyze_basic(hotspots)
    
    def analyze_hotspot_basic(self, title: str, heat: int) -> Dict:
        """基础分析单个热点（不使用Claude时的备选方案）"""
        # 更智能的分类和产品创意模板
        idea_templates = {
            # 体育类
            "火灾|安全|事故|爆炸": {
                "category": "社会安全",
                "sentiment": "负面",
                "name": "智能安全预警系统",
                "function": "利用AI和大数据实时监测和预警各类安全风险，提供应急响应方案",
                "users": "企业安全部门、社区管理者、政府应急部门",
                "business_value": "B端SaaS订阅服务，年费模式，市场规模大",
                "innovation": "多源数据融合 + AI风险预测 + 应急联动",
                "score": 85
            },
            "篮球|足球|网球|体育|运动|比赛|夺冠": {
                "category": "体育",
                "sentiment": "正面",
                "name": "AI体育数据分析平台",
                "function": "为球迷和专业人士提供深度赛事数据分析、球员表现追踪、比赛预测",
                "users": "体育爱好者、体育博彩用户、教练员、球探",
                "business_value": "订阅会员 + 数据API变现 + 广告合作",
                "innovation": "实时数据可视化 + 预测模型 + 社交互动",
                "score": 82
            },
            "太空|航天|火箭|卫星|探测": {
                "category": "科技",
                "sentiment": "正面",
                "name": "航天科普互动平台",
                "function": "沉浸式航天知识学习、虚拟太空探索、航天新闻聚合",
                "users": "青少年学生、科技爱好者、教育机构",
                "business_value": "教育付费内容 + VR/AR体验 + B端授权",
                "innovation": "游戏化学习 + AR/VR技术 + 实时航天数据",
                "score": 88
            },
            "电影|电视剧|综艺|票房|演员|导演": {
                "category": "娱乐",
                "sentiment": "中性",
                "name": "智能观影决策助手",
                "function": "基于AI的个性化影视推荐、观影社交、影评聚合",
                "users": "影迷、剧迷、年轻用户群体",
                "business_value": "会员订阅 + 影院合作分成 + 电影宣发",
                "innovation": "情绪化推荐算法 + 观影社交 + 跨平台聚合",
                "score": 80
            },
            "手机|小米|华为|苹果|iPhone|数码": {
                "category": "消费电子",
                "sentiment": "中性",
                "name": "智能消费决策工具",
                "function": "对比分析、性价比计算、用户评价聚合、价格追踪",
                "users": "数码爱好者、理性消费者、学生群体",
                "business_value": "电商导购佣金 + 会员服务 + 数据服务",
                "innovation": "全网比价 + AI需求匹配 + 社区UGC",
                "score": 78
            },
            "AI|人工智能|ChatGPT|GPT|大模型": {
                "category": "科技",
                "sentiment": "正面",
                "name": "AI能力市场",
                "function": "连接AI服务商和需求方，提供开箱即用的AI能力",
                "users": "中小企业、创业者、开发者、个人用户",
                "business_value": "交易抽成 + SaaS订阅 + API调用计费",
                "innovation": "零门槛AI使用 + 能力组合 + 效果保障",
                "score": 92
            },
            "股票|基金|理财|投资|A股": {
                "category": "金融",
                "sentiment": "中性",
                "name": "普惠智能投顾",
                "function": "为普通用户提供AI驱动的投资建议和风险管理",
                "users": "个人投资者、理财新手、上班族",
                "business_value": "管理费抽成 + 增值服务 + 金融产品分销",
                "innovation": "低门槛 + 风险可视化 + 社区学习",
                "score": 85
            },
            "春运|春节|车票|高铁|火车": {
                "category": "民生出行",
                "sentiment": "中性",
                "name": "智能出行规划助手",
                "function": "多模式出行方案对比、抢票提醒、行程管理",
                "users": "春运出行人群、商务人士、旅游爱好者",
                "business_value": "交通服务商合作 + 增值服务 + 广告",
                "innovation": "多维度优化（时间/价格/舒适度） + 智能提醒",
                "score": 76
            },
            "明星|爱豆|粉丝|演唱会|idol": {
                "category": "娱乐",
                "sentiment": "正面",
                "name": "粉丝经济平台",
                "function": "明星周边、活动票务、粉丝社交、应援工具",
                "users": "娱乐粉丝、追星族、年轻女性群体",
                "business_value": "周边电商 + 票务分成 + 会员服务",
                "innovation": "区块链数字藏品 + 虚拟见面会 + 粉丝贡献积分",
                "score": 73
            },
        }
        
        # 匹配关键词
        selected = None
        for pattern, template in idea_templates.items():
            if re.search(pattern, title):
                selected = template.copy()
                break
        
        # 如果没有匹配，使用默认模板
        if not selected:
            selected = {
                "category": "社会热点",
                "sentiment": "中性",
                "name": f"{title}话题追踪器",
                "function": f"实时追踪'{title}'相关动态、舆情分析、用户讨论聚合",
                "users": "关注此话题的用户",
                "business_value": "热点营销工具、舆情监测服务",
                "innovation": "实时性强、多维度分析",
                "score": 70
            }
        
        # 根据热度调整分数
        base_score = selected['score']
        if heat > 1000000:
            score = min(100, base_score + 8)
        elif heat > 500000:
            score = min(95, base_score + 4)
        else:
            score = base_score
        
        # 确定评分等级
        if score >= 90:
            grade = "卓越"
        elif score >= 80:
            grade = "优秀"
        elif score >= 70:
            grade = "良好"
        elif score >= 60:
            grade = "一般"
        else:
            grade = "较弱"
        
        return {
            "category": selected['category'],
            "sentiment": selected['sentiment'],
            "name": selected['name'],
            "function": selected['function'],
            "users": selected['users'],
            "business_value": selected['business_value'],
            "innovation": selected['innovation'],
            "insight": f"基于规则引擎的基础分析，建议结合实际市场调研",
            "score": score,
            "grade": grade
        }
    
    def analyze_basic(self, hotspots: List[Dict]) -> List[Dict]:
        """使用基础规则分析所有热点"""
        print("📊 使用基础规则分析...")
        results = []
        for hotspot in hotspots:
            analysis = self.analyze_hotspot_basic(hotspot['title'], hotspot['heat'])
            results.append({**hotspot, 'analysis': analysis})
        return results
    
    def generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        report = []
        
        # 报告头部
        report.append("# 🔥 微博热搜产品创意分析报告")
        report.append("")
        report.append(f"> **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"> **分析引擎**: {'Claude Agent SDK' if self.claude_client else '基础规则引擎'}")
        report.append(f"> **热搜数量**: {len(self.analysis_results)} 条")
        report.append("")
        report.append("---")
        report.append("")
        
        # 统计数据
        excellent_count = sum(1 for r in self.analysis_results if r['analysis']['grade'] == '优秀')
        good_count = sum(1 for r in self.analysis_results if r['analysis']['grade'] == '良好')
        avg_score = sum(r['analysis']['score'] for r in self.analysis_results) / len(self.analysis_results) if self.analysis_results else 0
        
        # 分类统计
        categories = {}
        sentiments = {'正面': 0, '中性': 0, '负面': 0}
        for r in self.analysis_results:
            cat = r['analysis'].get('category', '未分类')
            categories[cat] = categories.get(cat, 0) + 1
            sent = r['analysis'].get('sentiment', '中性')
            if sent in sentiments:
                sentiments[sent] += 1
        
        report.append("## 📊 分析概览")
        report.append("")
        report.append("### 整体评分")
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 优秀创意 | {excellent_count} 个 ⭐ |")
        report.append(f"| 良好创意 | {good_count} 个 |")
        report.append(f"| 平均评分 | {avg_score:.1f} 分 |")
        report.append("")
        
        report.append("### 热点分类")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            report.append(f"- **{cat}**: {count} 条")
        report.append("")
        
        report.append("### 情感倾向")
        for sent, count in sentiments.items():
            if count > 0:
                emoji = "😊" if sent == "正面" else ("😐" if sent == "中性" else "😟")
                report.append(f"- {emoji} **{sent}**: {count} 条")
        report.append("")
        report.append("---")
        report.append("")
        
        # 详细分析
        report.append("## 📝 详细分析")
        report.append("")
        
        for result in self.analysis_results:
            analysis = result['analysis']
            star = "⭐ " if analysis['grade'] == '优秀' else ""
            
            report.append(f"### {star}【第{result['rank']}名】{result['title']}")
            report.append("")
            report.append(f"**📈 热度**: {result['heat']:,}")
            if result.get('tag'):
                report.append(f" | **🏷️ 标签**: {result['tag']}")
            report.append("")
            
            # 分类和情感
            if analysis.get('category'):
                report.append(f"**🔖 分类**: {analysis['category']}")
            if analysis.get('sentiment'):
                emoji = "😊" if analysis['sentiment'] == "正面" else ("😐" if analysis['sentiment'] == "中性" else "😟")
                report.append(f" | **{emoji} 情感**: {analysis['sentiment']}")
            report.append("")
            
            # 用户画像
            if analysis.get('users'):
                report.append(f"**👥 用户画像**: {analysis['users']}")
                report.append("")
            
            # 产品创意
            report.append(f"**💡 创意产品**: {analysis['name']}")
            report.append(f"- **核心功能**: {analysis['function']}")
            if analysis.get('business_value'):
                report.append(f"- **商业价值**: {analysis['business_value']}")
            if analysis.get('innovation'):
                report.append(f"- **创新点**: {analysis['innovation']}")
            report.append("")
            
            # AI洞察
            if analysis.get('insight'):
                report.append(f"**🔍 分析洞察**: {analysis['insight']}")
                report.append("")
            
            # 评分
            score_emoji = "🌟" if analysis['score'] >= 90 else ("⭐" if analysis['score'] >= 80 else "✨")
            report.append(f"**{score_emoji} 综合评分**: {analysis['score']}分 ({analysis['grade']})")
            report.append("")
            report.append("---")
            report.append("")
        
        # 报告尾部
        report.append("---")
        report.append("")
        report.append("## 📌 说明")
        report.append("")
        report.append("- 本报告由 GitHub Actions 自动生成")
        report.append("- 数据来源：微博热搜榜（天API）")
        report.append("- 分析仅供参考，不构成商业建议")
        report.append("")
        
        return "\n".join(report)
    
    def run_analysis(
        self, 
        limit: int = 10, 
        output_file: str = None,
        use_claude: bool = True
    ) -> str:
        """
        运行完整分析流程
        
        Args:
            limit: 分析热搜数量
            output_file: 输出文件路径
            use_claude: 是否使用Claude分析
            
        Returns:
            分析报告文本
        """
        print("=" * 60)
        print("🚀 微博热搜趋势分析器 v3.0 (Cloud Edition)")
        print("=" * 60)
        print("")
        
        # 获取热搜
        hotspots = self.fetch_hotspots(limit)
        if not hotspots:
            print("❌ 未能获取热搜数据，分析终止")
            return ""
        
        # 分析热点
        if use_claude and self.claude_client:
            self.analysis_results = self.analyze_with_claude(hotspots)
        else:
            self.analysis_results = self.analyze_basic(hotspots)
        
        # 生成报告
        report = self.generate_markdown_report()
        
        # 打印报告
        print("")
        print(report)
        
        # 保存到文件
        if output_file:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n📁 报告已保存到: {output_file}")
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='微博热搜趋势分析器 - GitHub Actions 云端版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python weibo_trends_analyzer.py                    # 分析前10个热搜
  python weibo_trends_analyzer.py -n 5               # 分析前5个热搜
  python weibo_trends_analyzer.py -o report.md       # 保存报告到文件
  python weibo_trends_analyzer.py --use-claude false # 不使用Claude分析

环境变量:
  TIANAPI_KEY       - 天API密钥（必需）
  ANTHROPIC_API_KEY - Claude API密钥（可选，用于智能分析）
        """
    )
    
    parser.add_argument(
        '-n', '--number',
        type=int,
        default=10,
        help='要分析的热搜数量（默认：10）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='输出文件路径（可选，建议使用.md扩展名）'
    )
    
    parser.add_argument(
        '--use-claude',
        type=str,
        default='true',
        choices=['true', 'false'],
        help='是否使用Claude智能分析（默认：true）'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='微博热搜趋势分析器 v3.0 (Cloud Edition)'
    )
    
    args = parser.parse_args()
    
    try:
        # 初始化分析器
        analyzer = WeiboTrendsAnalyzer()
        
        # 运行分析
        use_claude = args.use_claude.lower() == 'true'
        analyzer.run_analysis(
            limit=args.number,
            output_file=args.output,
            use_claude=use_claude
        )
        
        print("\n✅ 分析完成！")
        sys.exit(0)
        
    except ValueError as e:
        print(f"\n❌ 配置错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
