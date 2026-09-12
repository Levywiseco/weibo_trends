#!/usr/bin/env python3
"""
微博热搜趋势分析器 - GitHub Actions 云端版本
支持 Claude Agent SDK 智能分析

版本: 3.0 (Cloud Edition)
作者: GitHub Actions 自动化
"""

import argparse
import os
import random
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
        
        prompt = f"""你是一位顶尖的创意总监、互联网产品专家和商业模式创新者。请用「逆向思维」和「跨界融合」的方法，深度分析以下微博热搜榜单，为每个热点挖掘出令人眼前一亮的创新产品创意。

当前微博热搜TOP{len(hotspots)}:
{hotspot_text}

## 🧠 创意思维方法论（必须运用）

请运用以下至少2种创意方法来生成产品创意：

1. **SCAMPER法**：替代(Substitute)、合并(Combine)、适应(Adapt)、修改(Modify)、另作他用(Put to other uses)、删除(Eliminate)、重组(Rearrange)
2. **跨界融合**：将热点与完全不相关的领域结合（如：传统文化+区块链、美食+AR、社会事件+游戏化）
3. **逆向思维**：从用户痛点的反面思考，找到反常识的解决方案
4. **极端用户法**：思考最边缘用户群体的独特需求
5. **10x思维**：如何让现有解决方案好10倍而不是10%
6. **第一性原理**：回归问题本质，重新定义问题

## 📋 分析维度

请为每个热搜提供：

1. **热点分类**：体育/娱乐/科技/社会/民生/消费/文化/健康/教育/财经/国际等
2. **情感倾向**：正面/中性/负面
3. **用户画像**：具体的人群特征（年龄段、职业、兴趣标签、消费能力等）
4. **隐藏需求**：用户表面关注热点，背后真正的深层需求是什么？
5. **产品创意**：⭐必须是独特的、有创意的产品构思，绝对禁止"XX社区"、"XX追踪器"等无创意模板
6. **创意来源**：说明使用了哪种创意方法生成这个产品
7. **核心功能**：3个最关键的差异化功能点
8. **变现模式**：具体的商业模式（订阅/交易/广告/增值服务等）
9. **竞争壁垒**：为什么别人难以复制
10. **综合评分**：0-100分

## ⚠️ 严格禁止

- ❌ "XX话题社区"、"XX话题追踪器"、"XX讨论平台"
- ❌ 简单的信息聚合类产品
- ❌ 没有明确变现模式的产品
- ❌ 已经存在大量同类竞品的产品
- ❌ 纯概念性没有落地可能的产品

## ✅ 鼓励的创意方向

- 💡 将热点与硬件/IoT结合
- 💡 将热点游戏化，用游戏机制解决问题
- 💡 将热点与AI/大模型深度结合
- 💡 发现热点中的"反共识"机会
- 💡 面向被忽视的小众人群设计产品
- 💡 将线下场景线上化，或线上场景线下化

## 📊 评分标准

- 95-100分：革命性创新，可能改变行业格局
- 85-94分：高度创新，具有独特竞争壁垒
- 75-84分：较好创意，有一定市场空间
- 65-74分：一般创意，创新不足
- 65分以下：创意平庸，不建议投入

请返回纯JSON数组格式（必须严格遵循）：
```json
[
  {{
    "热点分类": "...",
    "情感倾向": "正面/中性/负面",
    "用户画像": "具体描述目标用户特征",
    "隐藏需求": "用户深层需求分析",
    "产品名称": "有创意的产品名（必须独特）",
    "创意来源": "使用的创意方法",
    "核心功能": "三个关键功能点",
    "商业价值": "具体变现模式和市场规模预估",
    "创新点": "与现有产品的核心差异",
    "竞争壁垒": "难以被复制的原因",
    "综合评分": 85,
    "评分等级": "优秀",
    "分析洞察": "对这个热点的独特见解"
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
                                'hidden_need': analysis.get('隐藏需求', ''),
                                'creative_method': analysis.get('创意来源', ''),
                                'business_value': analysis.get('商业价值', '待评估'),
                                'innovation': analysis.get('创新点', ''),
                                'barrier': analysis.get('竞争壁垒', ''),
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
        """基础分析单个热点（不使用Claude时的备选方案）- 使用创意思维模板"""
        # 扩充的创意模板库 - 基于跨界融合和创新思维
        idea_templates = {
            # 安全类 - 跨界IoT硬件
            "火灾|安全|事故|爆炸|地震|灾害": {
                "category": "社会安全",
                "sentiment": "负面",
                "name": "「守护者」家庭安全机器人",
                "function": "1.AI视觉识别危险行为 2.多传感器环境监测 3.一键SOS联动救援",
                "users": "有老人小孩的家庭、独居人群、高端社区",
                "hidden_need": "人们需要的不是警报，而是「被守护」的安心感",
                "creative_method": "跨界融合：安全监测 + 陪伴机器人",
                "business_value": "硬件销售(3999元/台) + 月费服务(99元/月) + 保险合作分成",
                "innovation": "把冷冰冰的安防设备变成有温度的家庭成员",
                "barrier": "硬件+AI算法+救援网络的组合壁垒",
                "score": 88
            },
            # 体育类 - 游戏化思维
            "篮球|足球|网球|体育|运动|比赛|夺冠|奥运|世界杯|冠军": {
                "category": "体育",
                "sentiment": "正面",
                "name": "「球探RPG」体育养成游戏",
                "function": "1.真实球员数据驱动 2.经理人养成玩法 3.实时赛事联动奖励",
                "users": "18-35岁男性球迷、游戏玩家、体育博彩替代需求",
                "hidden_need": "球迷想要「参与感」而非只是旁观者",
                "creative_method": "游戏化：体育观赛 + RPG养成机制",
                "business_value": "内购道具 + 赛季通行证 + 品牌赞助植入，预计年收入5000万+",
                "innovation": "用游戏机制激活被动观赛用户，创造日活粘性",
                "barrier": "体育版权合作 + 游戏研发能力双门槛",
                "score": 86
            },
            # 航天科技 - AR/VR沉浸式
            "太空|航天|火箭|卫星|探测|月球|火星|宇宙": {
                "category": "科技",
                "sentiment": "正面",
                "name": "「星际公民」AR太空探索",
                "function": "1.手机AR模拟太空行走 2.收集虚拟星球NFT 3.航天任务剧情游戏",
                "users": "10-25岁学生、科幻爱好者、亲子教育场景",
                "hidden_need": "每个人内心都有一个太空梦，但99.99%的人无法实现",
                "creative_method": "SCAMPER-适应：把专业航天体验平民化",
                "business_value": "虚拟道具销售 + 教育机构授权 + 航天周边电商",
                "innovation": "用游戏降低航天科普门槛，用NFT创造收藏价值",
                "barrier": "NASA/中国航天授权 + AR技术积累",
                "score": 89
            },
            # 影视娱乐 - 社交+AI
            "电影|电视剧|综艺|票房|演员|导演|剧集|追剧": {
                "category": "娱乐",
                "sentiment": "中性",
                "name": "「剧本杀影院」沉浸式观影",
                "function": "1.AI生成平行剧情分支 2.观众投票决定剧情走向 3.线下观影+线上互动",
                "users": "18-30岁城市青年、情侣约会、闺蜜社交",
                "hidden_need": "观众厌倦被动接受，想要成为故事的参与者",
                "creative_method": "逆向思维：从「看剧」变成「玩剧」",
                "business_value": "票价溢价(88-168元) + 剧情道具销售 + 影视IP合作",
                "innovation": "把单向的影视消费变成双向互动体验",
                "barrier": "影院合作资源 + AI剧情生成技术",
                "score": 84
            },
            # 数码消费 - 极端用户法（匹配手机品牌和苹果+数字的组合）
            "手机|小米|华为|iPhone|数码|电脑|平板|荣耀|vivo|OPPO|苹果\\d|苹果手机|苹果发布|苹果新品": {
                "category": "消费电子",
                "sentiment": "中性",
                "name": "「数码遗嘱」设备传承服务",
                "function": "1.数字资产一键迁移 2.设备使用习惯继承 3.旧设备残值最大化",
                "users": "换机频繁用户、数字资产丰富者、家庭多设备用户",
                "hidden_need": "换新设备的痛点不是价格，而是「数字生活断裂」",
                "creative_method": "极端用户法：关注换机时「失去」的焦虑",
                "business_value": "服务订阅(年费199) + 以旧换新溢价 + 设备回收差价",
                "innovation": "从卖设备转向「卖数字生活连续性」",
                "barrier": "跨品牌数据迁移技术 + 用户信任积累",
                "score": 82
            },
            # AI技术 - 第一性原理
            "AI|人工智能|ChatGPT|GPT|大模型|机器人|智能": {
                "category": "科技",
                "sentiment": "正面",
                "name": "「AI分身」数字克隆服务",
                "function": "1.学习你的说话方式 2.代你处理简单沟通 3.7x24小时在线响应",
                "users": "企业高管、网红KOL、高净值人群、远距离家庭",
                "hidden_need": "人们缺的不是AI助手，而是「另一个自己」",
                "creative_method": "第一性原理：AI的终极价值是「人的延伸」",
                "business_value": "高端订阅(999元/月) + 企业定制 + API调用",
                "innovation": "从通用AI到「个人AI」，每个人都有专属AI分身",
                "barrier": "个性化训练技术 + 数据隐私合规",
                "score": 93
            },
            # 金融投资 - 逆向思维
            "股票|基金|理财|投资|A股|暴涨|暴跌|牛市|熊市|金银": {
                "category": "金融",
                "sentiment": "中性",
                "name": "「后悔药」模拟投资复盘",
                "function": "1.历史买卖点回测 2.平行宇宙收益对比 3.投资心理分析报告",
                "users": "散户投资者、投资教育用户、金融专业学生",
                "hidden_need": "投资者真正的痛点是「后悔」和「不甘心」",
                "creative_method": "逆向思维：不预测未来，而是复盘过去",
                "business_value": "工具订阅(月费39元) + 投教课程 + 券商导流",
                "innovation": "把「后悔」情绪产品化，用复盘替代预测",
                "barrier": "历史数据完整性 + 心理学算法模型",
                "score": 85
            },
            # 出行春运 - 10x思维
            "春运|春节|车票|高铁|火车|抢票|回家|返乡": {
                "category": "民生出行",
                "sentiment": "中性",
                "name": "「拼座」返乡顺风车联盟",
                "function": "1.私家车主+乘客智能匹配 2.企业包车拼团 3.沿途城市接力换乘",
                "users": "二三线城市返乡人群、有车族、企业HR",
                "hidden_need": "春运的本质问题是「供需时空错配」",
                "creative_method": "10x思维：不是优化抢票，而是创造新运力",
                "business_value": "服务费抽成(10%) + 保险销售 + 沿途商业合作",
                "innovation": "把闲置私家车运力聚合起来解决春运难题",
                "barrier": "安全信任体系 + 政策合规 + 规模效应",
                "score": 80
            },
            # 明星粉丝 - 区块链+元宇宙
            "明星|爱豆|粉丝|演唱会|idol|偶像|出道|应援": {
                "category": "娱乐",
                "sentiment": "正面",
                "name": "「饭圈DAO」粉丝共创平台",
                "function": "1.粉丝投票决策明星活动 2.应援贡献积分链上存证 3.限量周边NFT发行",
                "users": "核心粉丝群体、饭圈组织者、娱乐公司",
                "hidden_need": "粉丝要的不只是追星，而是「被看见的贡献」",
                "creative_method": "跨界融合：粉丝经济 + DAO治理 + Web3",
                "business_value": "NFT发行分成 + 活动策划费 + 周边电商",
                "innovation": "用区块链让粉丝贡献可追溯、可变现",
                "barrier": "头部艺人合作 + 粉丝社群运营能力",
                "score": 78
            },
            # 节气文化 - 传统文化创新
            "立春|春分|谷雨|清明|节气|躲春|咬春|习俗|传统": {
                "category": "文化",
                "sentiment": "正面",
                "name": "「节气盲盒」文化体验订阅",
                "function": "1.每个节气寄送主题盲盒 2.AR扫描解锁节气故事 3.线下节气市集联动",
                "users": "25-40岁文化消费者、亲子家庭、送礼需求",
                "hidden_need": "现代人对传统文化是「想了解但没时间」",
                "creative_method": "SCAMPER-合并：节气文化 + 盲盒经济 + AR科技",
                "business_value": "订阅制(年费698元) + 单品销售 + 品牌联名",
                "innovation": "把抽象的传统文化变成可触摸、可分享的体验",
                "barrier": "供应链整合 + 文化IP授权 + 内容创作",
                "score": 86
            },
            # 美食健康 - 个性化
            "美食|餐厅|吃|菜|火锅|烧烤|外卖|食物|食品安全|中毒": {
                "category": "健康",
                "sentiment": "中性",
                "name": "「食愈」情绪化饮食顾问",
                "function": "1.根据情绪推荐食谱 2.AI营养师定制菜单 3.食材一键配送到家",
                "users": "独居青年、健身人群、饮食焦虑者",
                "hidden_need": "吃什么的背后是「今天心情如何」",
                "creative_method": "跨界融合：心理学 + 营养学 + 即时配送",
                "business_value": "会员订阅(月费79元) + 食材电商 + 餐饮品牌合作",
                "innovation": "从「吃什么」升维到「今天需要什么能量」",
                "barrier": "情绪识别算法 + 营养学知识图谱 + 供应链",
                "score": 84
            },
            # 教育学习
            "考试|高考|考研|学生|老师|学校|毕业|大学|中学": {
                "category": "教育",
                "sentiment": "中性",
                "name": "「时光机」未来职业体验",
                "function": "1.VR体验100种职业日常 2.AI生成你的职业适配度 3.与从业者1v1连线",
                "users": "高中生、大学生、迷茫期职场人、家长",
                "hidden_need": "学生填志愿时根本不了解这个专业未来做什么",
                "creative_method": "逆向思维：不是教「怎么考」而是展示「为什么考」",
                "business_value": "体验付费(单次98元) + 学校采购 + 企业雇主品牌合作",
                "innovation": "用沉浸式体验解决职业认知盲区",
                "barrier": "VR内容制作 + 各行业人脉资源",
                "score": 87
            },
            # 房产家居
            "房价|买房|租房|装修|房子|楼市|房贷": {
                "category": "房产",
                "sentiment": "中性",
                "name": "「邻里值」社区透明度指数",
                "function": "1.小区真实居住体验评分 2.邻居画像匿名展示 3.物业服务实时监督",
                "users": "购房者、租房者、社区居民、物业公司",
                "hidden_need": "买房最大的未知数是「未来的邻居和物业」",
                "creative_method": "极端用户法：关注入住后的「后悔」场景",
                "business_value": "房产平台合作分成 + 物业SaaS + 社区广告",
                "innovation": "把社区软实力量化，让买房决策更透明",
                "barrier": "数据采集难度 + 隐私合规 + 用户信任",
                "score": 83
            },
            # 宠物经济
            "宠物|猫|狗|萌宠|铲屎官|养猫|养狗": {
                "category": "宠物",
                "sentiment": "正面",
                "name": "「毛孩语」宠物情绪翻译器",
                "function": "1.AI识别宠物叫声含义 2.健康状态实时监测 3.宠物社交匹配约玩",
                "users": "宠物主人、宠物医院、宠物品牌",
                "hidden_need": "铲屎官最大的焦虑是「不知道它想要什么」",
                "creative_method": "SCAMPER-替代：用AI替代人的猜测",
                "business_value": "硬件销售(299元) + 增值服务 + 宠物电商导流",
                "innovation": "真正的「人宠沟通」而非单向照顾",
                "barrier": "宠物行为学研究 + AI算法训练数据",
                "score": 85
            },
            # 国际政治
            "日本|美国|俄罗斯|国际|外交|贸易|关税|制裁": {
                "category": "国际",
                "sentiment": "中性",
                "name": "「世界观」地缘政治可视化",
                "function": "1.国际关系动态图谱 2.事件影响链路追踪 3.投资避险预警提示",
                "users": "跨境贸易从业者、投资者、时政爱好者、学生",
                "hidden_need": "国际新闻太多太碎，普通人看不懂影响",
                "creative_method": "第一性原理：复杂信息需要「可视化降维」",
                "business_value": "专业版订阅(199元/月) + 企业风控服务 + 智库合作",
                "innovation": "把专业地缘政治分析平民化、可视化",
                "barrier": "专业分析团队 + 数据源整合",
                "score": 81
            },
        }
        
        # 匹配关键词
        selected = None
        for pattern, template in idea_templates.items():
            if re.search(pattern, title, re.IGNORECASE):
                selected = template.copy()
                break
        
        # 如果没有匹配，使用动态生成的创意模板（避免千篇一律）
        if not selected:
            # 根据标题特征动态生成创意
            creative_templates = [
                {
                    "name": f"「{title[:4]}效应」趋势预测引擎",
                    "function": "1.热点生命周期预测 2.关联话题挖掘 3.营销时机提醒",
                    "users": "营销从业者、自媒体人、品牌方",
                    "hidden_need": "热点转瞬即逝，人们需要的是「先知先觉」",
                    "creative_method": "第一性原理：热点的价值在于「时机把握」",
                    "business_value": "SaaS订阅(月费299元) + API服务 + 定制报告",
                    "innovation": "从事后追热点到事前预判热点",
                    "barrier": "预测算法准确性 + 数据源覆盖度",
                    "score": 76
                },
                {
                    "name": f"「反转实验室」真相核查游戏",
                    "function": "1.热点事件多视角呈现 2.玩家扮演侦探找证据 3.真相揭晓奖励机制",
                    "users": "信息素养关注者、游戏玩家、学生群体",
                    "hidden_need": "人们厌倦了被反转打脸，想主动辨别真假",
                    "creative_method": "游戏化：信息核查 + 侦探游戏机制",
                    "business_value": "游戏内购 + 教育机构合作 + 媒体合作",
                    "innovation": "把严肃的事实核查变成有趣的推理游戏",
                    "barrier": "内容生产能力 + 游戏化设计",
                    "score": 79
                },
                {
                    "name": f"「情绪温度计」舆情可视化",
                    "function": "1.实时公众情绪追踪 2.情绪传染路径分析 3.品牌危机预警",
                    "users": "企业公关、政府舆情部门、媒体",
                    "hidden_need": "热点背后是群体情绪，情绪才是真正的机会/风险",
                    "creative_method": "10x思维：从「事件监测」升级到「情绪感知」",
                    "business_value": "企业SaaS(年费10万+) + 危机咨询 + 数据报告",
                    "innovation": "比传统舆情监测早一步感知情绪变化",
                    "barrier": "情绪识别AI + 全网数据采集能力",
                    "score": 82
                },
            ]
            selected = random.choice(creative_templates)
            selected["category"] = "社会热点"
            selected["sentiment"] = "中性"
        
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
            "hidden_need": selected.get('hidden_need', ''),
            "creative_method": selected.get('creative_method', ''),
            "business_value": selected['business_value'],
            "innovation": selected['innovation'],
            "barrier": selected.get('barrier', ''),
            "insight": f"基于创意思维模板的分析，已运用SCAMPER/跨界融合/逆向思维等方法",
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
            
            # 隐藏需求（新增）
            if analysis.get('hidden_need'):
                report.append(f"**🎯 隐藏需求**: {analysis['hidden_need']}")
                report.append("")
            
            # 产品创意
            report.append(f"**💡 创意产品**: {analysis['name']}")
            
            # 创意来源（新增）
            if analysis.get('creative_method'):
                report.append(f"- **创意方法**: {analysis['creative_method']}")
            
            report.append(f"- **核心功能**: {analysis['function']}")
            if analysis.get('business_value'):
                report.append(f"- **商业价值**: {analysis['business_value']}")
            if analysis.get('innovation'):
                report.append(f"- **创新点**: {analysis['innovation']}")
            if analysis.get('barrier'):
                report.append(f"- **竞争壁垒**: {analysis['barrier']}")
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
