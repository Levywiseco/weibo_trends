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
        
        prompt = f"""请分析以下微博热搜，为每个热点生成一个创新产品创意。

当前微博热搜TOP{len(hotspots)}:
{hotspot_text}

请为每个热搜提供以下分析（用JSON格式返回）：
1. 产品名称：基于热点的创意产品名
2. 核心功能：产品的主要功能描述
3. 目标用户：产品的目标用户群体
4. 创新点：产品的独特创新之处
5. 综合评分：0-100分，评估商业可行性和创新性
6. 评分等级：优秀(80+)、良好(60-79)、一般(60以下)

请返回纯JSON数组格式，每个元素对应一个热搜的分析结果。"""

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
                                'name': analysis.get('产品名称', f"{hotspot['title']}创意产品"),
                                'function': analysis.get('核心功能', '待分析'),
                                'users': analysis.get('目标用户', '广大用户'),
                                'innovation': analysis.get('创新点', ''),
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
        # 关键词匹配模板
        idea_templates = {
            "火灾|安全|事故": ("智能安全预警系统", "利用AI技术实时监测安全风险", "企业、社区、学校", 85),
            "男篮|女篮|足球|体育": ("体育数据分析平台", "提供比赛数据分析、球员表现评估", "体育爱好者、教练员", 82),
            "太空|航天|火箭": ("航天科普教育平台", "传播航天知识，激发科学兴趣", "学生、科技爱好者", 88),
            "电影|电视剧|综艺": ("娱乐内容推荐引擎", "基于用户喜好推荐个性化内容", "年轻用户、影迷", 85),
            "小米|华为|苹果|手机": ("智能消费决策助手", "帮助用户做出明智消费决策", "消费者、购物爱好者", 83),
            "AI|人工智能|ChatGPT": ("AI能力体验平台", "让普通用户轻松体验AI能力", "职场人士、学生", 90),
            "股票|基金|理财": ("智能投资顾问", "提供个性化投资建议和风险评估", "投资者、理财用户", 80),
        }
        
        # 匹配关键词
        selected_idea = None
        for pattern, idea in idea_templates.items():
            if re.search(pattern, title):
                selected_idea = idea
                break
        
        if not selected_idea:
            selected_idea = (f"{title}专属社区", f"围绕{title}打造专属讨论社区", "关注此话题的用户", 75)
        
        name, function, users, base_score = selected_idea
        
        # 根据热度调整分数
        if heat > 1000000:
            score = min(100, base_score + 10)
        elif heat > 500000:
            score = min(95, base_score + 5)
        else:
            score = base_score
        
        grade = "优秀" if score >= 80 else "良好" if score >= 60 else "一般"
        
        return {
            "name": name,
            "function": function,
            "users": users,
            "innovation": "基于热点的创新应用",
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
        
        report.append("## 📊 分析概览")
        report.append("")
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 优秀创意 | {excellent_count} 个 ⭐ |")
        report.append(f"| 良好创意 | {good_count} 个 |")
        report.append(f"| 平均评分 | {avg_score:.1f} 分 |")
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
            report.append(f"- **热度**: {result['heat']:,}")
            if result.get('tag'):
                report.append(f"- **标签**: {result['tag']}")
            report.append(f"- **创意产品**: {analysis['name']}")
            report.append(f"- **核心功能**: {analysis['function']}")
            report.append(f"- **目标用户**: {analysis['users']}")
            if analysis.get('innovation'):
                report.append(f"- **创新点**: {analysis['innovation']}")
            report.append(f"- **综合评分**: {analysis['score']}分 ({analysis['grade']})")
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
