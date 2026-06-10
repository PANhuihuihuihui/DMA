import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./styles.css";
import { approveDraftVersion, loadPublishJob, loadPublishingWorkflow, queueFakePublish } from "./api/publishingClient.js";
import { ApprovalSnapshot } from "./components/ApprovalSnapshot.jsx";
import { PublishTimeline } from "./components/PublishTimeline.jsx";
import { RetryPublishControl } from "./components/RetryPublishControl.jsx";
import {
  RETRYABLE_PUBLISH_STATUSES,
  normalizeApprovalSnapshot,
  normalizePublishJob,
  normalizeWorkflow,
} from "./models/publishing.js";
import { AppRoutes } from "./routes/AppRoutes.jsx";
import { clearDemoWorkspacePreferences, readPreference, writePreference } from "./storage/preferences.js";

import cafeOwner from "../assets/cafe-owner.png";
import clinic from "../assets/clinic.png";
import restaurant from "../assets/restaurant.png";
import salon from "../assets/salon.png";
import shop from "../assets/shop.png";

const LANGUAGE_STORAGE_KEY = "localpilot-language";

const zhTranslations = {
  Product: "产品",
  Solutions: "解决方案",
  "Local ROI": "本地 ROI",
  Pricing: "价格",
  "Log in": "登录",
  "Join the pilot": "加入试点",
  "AI marketing operator for local businesses": "为本地商家打造的 AI 营销运营助手",
  "Your local business marketing team,": "你的本地生意营销团队，",
  "powered by AI.": "由 AI 驱动。",
  "Upload a video or promotion and get a week of platform-native content for TikTok, Instagram, Facebook, and Xiaohongshu.":
    "上传一个视频或促销信息，就能生成一周适配 TikTok、Instagram、Facebook 和小红书的原生内容。",
  "Watch workflow": "查看流程",
  "4.9/5 from 120+ local business owners": "120+ 本地商家评分 4.9/5",
  "No credit card required": "无需信用卡",
  "Cancel anytime": "随时取消",
  Overview: "概览",
  Campaigns: "营销活动",
  Calendar: "日历",
  Content: "内容",
  Analytics: "分析",
  "Trend-to-Action": "趋势转行动",
  Competitors: "竞品",
  "AI set": "AI 已配置",
  Input: "输入",
  "Weekend lunch special video": "周末午餐特惠视频",
  "Uploaded May 16, 2026 - 10:42 AM": "上传于 2026 年 5 月 16 日 10:42",
  Campaign: "营销活动",
  "May 19 - May 25, 2026": "2026 年 5 月 19 日 - 5 月 25 日",
  "4 platforms - 16 pieces of content": "4 个平台 - 16 条内容",
  "View app demo": "查看应用演示",
  Hook: "钩子",
  Reel: "短视频",
  "Local Post": "本地帖子",
  "种草 Note": "种草笔记",
  Approved: "已批准",
  "Campaign calendar": "营销日历",
  "TikTok Hook": "TikTok 开场",
  "Behind Scenes": "幕后花絮",
  "Menu Highlight": "菜单亮点",
  Story: "故事",
  "Event Post": "活动帖子",
  "Hot now: \"crispy chicken sandwich\"": "当前热门：“脆皮鸡肉三明治”",
  "Mentions are up 126% in your area.": "你所在区域的提及量上涨 126%。",
  "Create content idea": "生成内容创意",
  "View full report": "查看完整报告",
  Calls: "来电",
  Bookings: "预订",
  DMs: "私信",
  "Coupon Scans": "优惠券扫码",
  Saves: "收藏",
  "Map Clicks": "地图点击",
  "Upload once.": "上传一次。",
  "Grow all week.": "增长一整周。",
  "LocalPilot AI turns one video, menu item, service, or promotion into platform-native content that gets noticed and drives action.":
    "LocalPilot AI 将一个视频、菜单项、服务或促销信息变成适合各平台的原生内容，帮助被看见并推动行动。",
  Upload: "上传",
  "AI creates": "AI 生成",
  Schedule: "排期",
  "You grow": "你增长",
  "Upload a video or share your promotion.": "上传视频或分享促销信息。",
  "AI creates native content for every channel.": "AI 为每个渠道生成原生内容。",
  "We schedule a week that fits your business.": "我们为你的生意安排一周内容。",
  "Track local results that matter.": "追踪真正重要的本地结果。",
  "Built for restaurants, salons, clinics, and shops.": "为餐厅、沙龙、诊所和商店打造。",
  "Start with proven playbooks for local businesses where every booking, visit, and call matters.":
    "从经过验证的本地生意打法开始，让每一次预订、到店和来电都有价值。",
  Restaurants: "餐厅",
  "Fill tables and turn specials into loyal regulars.": "提高上座率，把特惠变成回头客。",
  Salons: "沙龙",
  "Show off your work and keep chairs booked.": "展示作品，让预约持续不断。",
  Clinics: "诊所",
  "Build trust and grow appointment demand.": "建立信任并提升预约需求。",
  Shops: "商店",
  "Highlight products and drive foot traffic.": "突出产品并带动到店客流。",
  "Local ROI, not vanity metrics": "本地 ROI，而不是虚荣指标",
  "Know what marketing actually brings customers.": "知道营销真正带来了哪些客户。",
  "We track calls, bookings, DMs, coupon scans, saves, and map clicks so owners can see what is working and keep growing.":
    "我们追踪来电、预订、私信、优惠券扫码、收藏和地图点击，帮助商家看清什么有效并持续增长。",
  "Coupon scans": "优惠券扫码",
  "Map clicks": "地图点击",
  "Track customer intent and revenue signals inside the same workflow.": "在同一个流程中追踪客户意图和收入信号。",
  "Xiaohongshu-native growth": "小红书原生增长",
  "Native strategy, not translation.": "原生策略，而不是简单翻译。",
  "Create RED notes with Chinese copy, 种草 framing, search keywords, cover text, save-oriented structure, and KOC-ready briefs.":
    "生成带有中文文案、种草框架、搜索关键词、封面标题、收藏导向结构和 KOC 简报的小红书笔记。",
  "本地午餐推荐": "本地午餐推荐",
  "关键词: 周末午餐, 本地探店, 适合朋友聚餐, 性价比": "关键词：周末午餐，本地探店，适合朋友聚餐，性价比",
  "1,248 saves": "1,248 收藏",
  "983 likes": "983 点赞",
  "156 comments": "156 评论",
  "Pilot plans": "试点方案",
  "Simple plans for early customers. Built to prove local ROI fast.": "为早期客户设计的简单方案，快速验证本地 ROI。",
  "Most popular": "最受欢迎",
  "Starter Pilot": "入门试点",
  "Perfect for trying it out.": "适合先试用。",
  "Growth Pilot": "增长试点",
  "For businesses ready to grow.": "适合准备增长的商家。",
  "Scale Pilot": "规模试点",
  "For agencies and multi-location teams.": "适合代理商和多门店团队。",
  "14-day pilot": "14 天试点",
  "/ week": "/ 周",
  "Request demo": "预约演示",
  "1 business location": "1 个门店",
  "1 video or promotion per week": "每周 1 个视频或促销",
  "4 platforms": "4 个平台",
  "Local ROI dashboard": "本地 ROI 看板",
  "Up to 3 uploads per week": "每周最多 3 次上传",
  "4 platforms including Xiaohongshu": "4 个平台，包含小红书",
  "Trend-to-Action and competitor watcher": "趋势转行动和竞品观察",
  "Up to 3 locations": "最多 3 个地点",
  "Approval workspace": "审批工作区",
  "Client-ready reports": "客户可读报告",
  "Priority support": "优先支持",
  "Join the LocalPilot AI pilot": "加入 LocalPilot AI 试点",
  "Pilot access": "试点访问",
  Name: "姓名",
  "Your name": "你的姓名",
  "Business name": "商家名称",
  Email: "邮箱",
  "Business type": "商家类型",
  "Restaurant or cafe": "餐厅或咖啡店",
  "Salon or beauty": "沙龙或美容",
  "Clinic or wellness": "诊所或健康服务",
  "Retail shop": "零售店",
  "Other local service": "其他本地服务",
  "Biggest marketing challenge": "最大的营销挑战",
  "Request pilot invite": "申请试点邀请",
  "Log in to the LocalPilot AI app demo": "登录 LocalPilot AI 应用演示",
  "Demo workspace": "演示工作区",
  "Use any name and email. This is a local prototype session with fake client and campaign data.":
    "可使用任意姓名和邮箱。这是一个带有模拟客户和营销数据的本地原型会话。",
  "Work email": "工作邮箱",
  Workspace: "工作区",
  "Northstar Local Growth": "北极星本地增长",
  "Brightside Agency Demo": "Brightside 代理演示",
  "LocalPilot Customer Preview": "LocalPilot 客户预览",
  "Enter app demo": "进入应用演示",
  Close: "关闭",
  Home: "首页",
  "AI Studio": "AI 工作室",
  Publish: "发布",
  Inbox: "收件箱",
  Discover: "发现",
  Reports: "报告",
  "Media Library": "媒体库",
  Approvals: "审批",
  Clients: "客户",
  Settings: "设置",
  "8 client locations": "8 个客户地点",
  "LocalPilot edge": "LocalPilot 优势",
  "Xiaohongshu + local ROI": "小红书 + 本地 ROI",
  "Native RED content, booking signals, calls, map clicks, and guided posting in one workflow.":
    "在一个流程中完成小红书原生内容、预订信号、来电、地图点击和引导式发布。",
  "Agency demo workspace": "代理商演示工作区",
  "Home command center": "首页指挥中心",
  "Create with AI": "用 AI 创建",
  "Review calendar": "查看日历",
  "Reset demo": "重置演示",
  "Log out": "退出",
  "Business input": "商家输入",
  "Native outputs": "原生输出",
  "TikTok, IG, FB, RED, Google": "TikTok、IG、FB、小红书、Google",
  "Local ROI intent": "本地 ROI 意图",
  "Calls, bookings, DMs, scans, saves, maps": "来电、预订、私信、扫码、收藏、地图",
  "Package ready": "交付包就绪",
  "Local growth workbench": "本地增长工作台",
  "One input, channel-native growth plan": "一个输入，生成渠道原生增长方案",
  "Create, refine, schedule": "创建、优化、排期",
  "AI campaign generator": "AI 营销活动生成器",
  "Network-tailored posts": "按平台定制的帖子",
  "Publishing pipeline": "发布流程",
  "Client-visible planning": "客户可见的计划",
  "Week, grid, and list planning": "周视图、网格和列表计划",
  Engage: "互动",
  "Unified comments and DMs": "统一评论和私信",
  "Trend-to-action": "趋势转行动",
  "Local discovery feed": "本地发现信息流",
  "Social + business outcomes": "社交 + 生意结果",
  "Performance intelligence": "效果智能",
  "Agency proof": "代理商成果证明",
  "Branded client reporting": "品牌化客户报告",
  Assets: "素材",
  "Reusable content library": "可复用内容库",
  "Client collaboration": "客户协作",
  "Review and sign-off": "审核和签署",
  "Agency workspace": "代理工作区",
  "Client management": "客户管理",
  Controls: "控制",
  "Workspace configuration": "工作区配置",
  Week: "周",
  Grid: "网格",
  List: "列表",
  Type: "类型",
  Offer: "优惠",
  Goal: "目标",
  Audience: "受众",
  "Regenerate weekly plan": "重新生成周计划",
  "Needs review": "待审核",
  "Needs changes": "需修改",
  "Approve plan": "批准计划",
  "Approve exact draft": "批准确切草稿",
  "Request changes": "请求修改",
  "Post angle": "发布角度",
  Caption: "文案",
  CTA: "行动按钮",
  KPI: "指标",
  "Publishing mode": "发布方式",
  "Assets included": "包含素材",
  "Tracking events": "追踪事件",
  "Why this should work": "为什么有效",
  "Owner action and risk check": "商家操作和风险检查",
  "Delivery package": "交付包",
  "Save package": "保存交付包",
  "What the customer gets": "客户将获得",
  "Local ROI handoff": "本地 ROI 交接",
  "Competitor watcher": "竞品观察",
  "Approve slot": "批准时段",
  "Request edit": "请求编辑",
  Generate: "生成",
  "Suggested reply": "建议回复",
  "Best signal": "最佳信号",
  "Owner-led content is creating higher local intent.": "由店主出镜的内容正在创造更高的本地意图。",
  "Add note": "添加备注",
  Capability: "能力",
  "Run demo action": "运行演示操作",
  Mark: "标记",
  "Package readiness": "交付包就绪度",
  "AI recommendations": "AI 建议",
  "3 new": "3 条新建议",
  "Approval queue": "审批队列",
  pending: "待处理",
  Approve: "批准",
  "All channels approved": "所有渠道已批准",
  "Ready to save the posting package": "可以保存发布包",
  Save: "保存",
  "Competitor watch": "竞品观察",
  "Hot now": "当前热门",
  "Local ROI loop": "本地 ROI 循环",
  calls: "来电",
  bookings: "预订",
  "map clicks": "地图点击",
};

Object.assign(zhTranslations, {
  "This lunch special hits different.": "这个午餐特惠真的不一样。",
  "Weekend lunch just got booked.": "周末午餐预约已经开始起量。",
  "Fresh ingredients. Big flavor. See you this weekend.": "新鲜食材，大满足风味。周末见。",
  "周末午餐推荐, 好吃不贵, 值得打卡.": "周末午餐推荐，好吃不贵，值得打卡。",
  "LocalPilot AI home": "LocalPilot AI 首页",
  "Primary navigation": "主导航",
  "Toggle navigation": "展开或收起导航",
  "Customer rating": "客户评分",
  "Local cafe owner reviewing marketing on a tablet": "本地咖啡店老板在平板上查看营销内容",
  "Product sidebar preview": "产品侧边栏预览",
  "Businesses / Sunny Side Bistro": "商家 / Sunny Side Bistro",
  "Restaurant lunch special": "餐厅午餐特惠",
  "campaign preview": "营销预览",
  "Weekly campaign calendar": "每周营销日历",
  Mon: "周一",
  Tue: "周二",
  Wed: "周三",
  Thu: "周四",
  Fri: "周五",
  Sat: "周六",
  Sun: "周日",
  "12:00 PM": "中午 12:00",
  "6:00 PM": "下午 6:00",
  visual: "视觉图",
  "Your local business marketing team, powered by AI.": "你的本地生意营销团队，由 AI 驱动。",
  "What do you want LocalPilot AI to help with first?": "你希望 LocalPilot AI 先帮你解决什么？",
  "you@business.com": "you@business.com",
  "Alex Morgan": "Alex Morgan",
  "alex@agency.com": "alex@agency.com",
  "Switch language between English and Chinese": "在英文和中文之间切换",
  "App navigation": "应用导航",
  "Demo sections": "演示模块",
  "Selected client": "已选择客户",
  "Workspace summary": "工作区摘要",
  "Primary demo panel": "主演示面板",
  "Calendar view": "日历视图",
  "Channel plans": "渠道方案",
  "generated campaign preview": "生成的营销预览",
  "LocalPilot standout features": "LocalPilot 核心亮点",
  "Ready-to-deliver campaign package": "可交付的营销活动包",
  "Selected campaign preview": "已选择营销预览",
  "Ask AI Studio to create, refine, analyze, or schedule...": "让 AI 工作室创建、优化、分析或排期...",
  "Calendar overview": "日历概览",
  "Insights and approvals": "洞察和审批",
  Composer: "编辑器",
  "Turn one offer into channel-specific posts with captions, hashtags, and cover copy.":
    "把一个优惠转成各渠道专属帖子，包含标题、标签和封面文案。",
  "Bulk schedule": "批量排期",
  "Queue weeks of posts from AI-generated campaign plans or CSV-style batches.":
    "从 AI 生成的营销计划或表格批量排期多周帖子。",
  "Assisted publishing": "辅助发布",
  "Package ready-to-post assets for channels with limited publishing APIs.":
    "为发布 API 受限的渠道打包可直接发布的素材。",
  "Trending topics": "热门话题",
  "Score platform trends as useful, risky, or irrelevant for each local business.":
    "为每个本地商家判断平台趋势是有用、有风险还是不相关。",
  "Track nearby businesses, offers, posting rhythm, and engagement spikes.":
    "追踪附近商家的优惠、发布节奏和互动峰值。",
  "Content sources": "内容来源",
  "Organize RSS, local news, newsletters, and inspiration by client workspace.":
    "按客户工作区整理 RSS、本地新闻、newsletter 和灵感来源。",
  "Scheduled reports": "定时报告",
  "Send presentation-ready summaries for social results and Local ROI.":
    "发送可直接展示的社交效果和本地 ROI 总结。",
  "Client notes": "客户说明",
  "Explain what changed, what worked, and what to approve next.":
    "说明发生了什么、什么有效，以及下一步要批准什么。",
  "Export package": "导出包",
  "Bundle top posts, analytics, comments, and next-week recommendations.":
    "打包最佳帖子、数据分析、评论和下周建议。",
  "Brand folders": "品牌文件夹",
  "Store approved images, videos, logos, offers, and campaign references per client.":
    "按客户保存已批准图片、视频、Logo、优惠和营销参考。",
  "AI variants": "AI 变体",
  "Generate captions, image prompts, thumbnails, and first-comment ideas from assets.":
    "基于素材生成标题、图片提示词、缩略图和首评创意。",
  "Usage history": "使用历史",
  "See where every asset has been published and how it performed.":
    "查看每个素材发布到哪里以及表现如何。",
  "No-login review": "免登录审核",
  "Share client approval links without exposing the full workspace.":
    "分享客户审批链接，同时不暴露完整工作区。",
  "Revision notes": "修改备注",
  "Keep client comments, internal notes, and final approvals attached to each post.":
    "把客户评论、内部备注和最终审批都关联到每条帖子。",
  "Compliance checklist": "合规清单",
  "Flag risky claims, missing disclaimers, and platform limits.":
    "标记风险表述、缺失免责声明和平台限制。",
  "Workspace separation": "工作区隔离",
  "Keep accounts, calendars, media, reports, and roles separate per client.":
    "按客户隔离账号、日历、媒体、报告和角色。",
  "Onboarding profile": "入驻资料",
  "Capture business type, location, offers, audience, voice, and competitors.":
    "收集商家类型、位置、优惠、受众、语气和竞品。",
  "Service tiers": "服务层级",
  "Track pilot, growth, and multi-location clients from one command center.":
    "在一个指挥中心管理试点、增长和多门店客户。",
  "Social accounts": "社交账号",
  "Mock TikTok, Instagram, Facebook, Xiaohongshu, and Google Business workflows.":
    "模拟 TikTok、Instagram、Facebook、小红书和 Google 商家流程。",
  "Brand knowledge": "品牌知识",
  "Save voice, services, offers, customer profile, and approved phrases.":
    "保存品牌语气、服务、优惠、客户画像和已批准用语。",
  "Team roles": "团队角色",
  "Assign creators, reviewers, approvers, and report recipients.":
    "分配创作者、审核者、审批者和报告接收人。",
  Ready: "就绪",
  "Needs setup": "需设置",
  Assisted: "辅助",
  Hot: "热门",
  Rising: "上升",
  Watch: "观察",
  Ignore: "忽略",
  Included: "已包含",
  Draft: "草稿",
  Saved: "已保存",
  Generated: "已生成",
  Available: "可用",
  Pending: "待处理",
  Active: "启用",
  Template: "模板",
  Mocked: "已模拟",
  Later: "稍后",
  Scheduled: "已排期",
  "TikTok vertical cut": "TikTok 竖版剪辑",
  "Schedule after owner approval": "商家批准后排期",
  "Instagram story reminder": "Instagram Story 提醒",
  "Attach DM keyword tracking": "附加私信关键词追踪",
  "Xiaohongshu RED note": "小红书笔记",
  "Copy package for manual publish": "复制手动发布包",
  "Google Local update": "Google 本地更新",
  "Confirm hours and offer window": "确认营业时间和优惠窗口",
  "Trend-to-action queue": "趋势转行动队列",
  "Convert local competitor and trend signals into specific post ideas for the selected business.":
    "把本地竞品和趋势信号转成当前商家的具体帖子创意。",
  "Owner-led lunch specials": "店主出镜午餐特惠",
  "Use owner intro in TikTok and Facebook": "在 TikTok 和 Facebook 使用店主开场",
  "Weekend near me searches": "附近周末搜索",
  "Create Google Local and RED keyword set": "创建 Google 本地和小红书关键词组",
  "Under $15 captions": "15 美元以内文案",
  "Test price-anchor caption on Instagram": "在 Instagram 测试价格锚点文案",
  "Generic viral audio": "通用热门音频",
  "Low fit for local conversion goal": "与本地转化目标匹配度低",
  "Client-ready proof": "客户可读成果",
  "Show the owner what was created, what got approved, and which local actions were generated.":
    "向商家展示创建了什么、批准了什么，以及带来了哪些本地行动。",
  "Channel plan summary": "渠道方案总结",
  "Five native outputs with status": "五个原生输出及状态",
  "Local ROI snapshot": "本地 ROI 快照",
  "Calls, DMs, saves, coupon scans, map clicks": "来电、私信、收藏、优惠券扫码、地图点击",
  "Next week recommendation": "下周建议",
  "Owner intro plus weekday offer test": "店主开场 + 工作日优惠测试",
  "Agency report": "代理商报告",
  "PDF-style handoff prepared from fake data": "基于模拟数据准备的 PDF 风格交接",
  "Lunch special hero clip": "午餐特惠主视频",
  "Used by TikTok and Instagram": "用于 TikTok 和 Instagram",
  "RED cover title": "小红书封面标题",
  "Used by Xiaohongshu package": "用于小红书发布包",
  "Owner intro prompt": "店主开场提示",
  "Requested before final export": "最终导出前需要补充",
  "Google profile image": "Google 资料图片",
  "Ready for local update": "可用于本地更新",
  "Owner sign-off": "商家签署",
  "Review every channel plan, request changes, and prepare a no-login approval package.":
    "审核每个渠道方案、提出修改，并准备免登录审批包。",
  "TikTok hook and coupon wording": "TikTok 开场和优惠券措辞",
  "Approve or request edit": "批准或请求编辑",
  "Instagram DM keyword": "Instagram 私信关键词",
  "Confirm auto-reply wording": "确认自动回复措辞",
  "Xiaohongshu Chinese copy": "小红书中文文案",
  "Review cover title and keywords": "审核封面标题和关键词",
  "Google Local offer window": "Google 本地优惠窗口",
  "Confirm hours and phone CTA": "确认营业时间和电话行动按钮",
  "Client workspace": "客户工作区",
  "Switch fake local business profiles and load the right offers, audience, channels, and ROI events.":
    "切换模拟本地商家资料，并加载对应优惠、受众、渠道和 ROI 事件。",
  "Restaurant local visit workflow": "餐厅到店转化流程",
  "Northline HVAC": "Northline HVAC",
  "Calls and booked service visits": "来电和已预约上门服务",
  "Glow Room Salon": "Glow Room Salon",
  "DMs, bookings, and saves": "私信、预约和收藏",
  "Harbor Family Clinic": "Harbor Family Clinic",
  "Appointment requests and calls": "预约请求和来电",
  "Demo configuration": "演示配置",
  "Mock the operational controls that will later connect to Odoo, social accounts, and customer data.":
    "模拟之后会连接 Odoo、社交账号和客户数据的运营控制项。",
  "TikTok, Instagram, Facebook, RED, Google": "TikTok、Instagram、Facebook、小红书、Google",
  "Business knowledge": "商家知识",
  "Offer, goal, audience, voice, competitors": "优惠、目标、受众、语气、竞品",
  "ROI events": "ROI 事件",
  "Calls, bookings, DMs, coupon scans, saves, maps": "来电、预订、私信、优惠券扫码、收藏、地图",
  "Odoo connection": "Odoo 连接",
  "Replace fake sample data with customer records": "用客户记录替换模拟样本数据",
  "TikTok hook": "TikTok 开场",
  "Lunch special trend angle": "午餐特惠趋势角度",
  "Instagram Reel": "Instagram Reel",
  "Visual story + offer CTA": "视觉故事 + 优惠行动按钮",
  "Facebook post": "Facebook 帖子",
  "Community update": "社区更新",
  "Xiaohongshu note": "小红书笔记",
  "Searchable Chinese content": "可搜索中文内容",
  "Story reminder": "Story 提醒",
  "Coupon scan push": "优惠券扫码推动",
  "Weekly channel plan": "每周渠道方案",
  "Create five channel-native outputs from one offer.": "从一个优惠生成五个渠道原生输出。",
  Rewrite: "改写",
  "Convert the offer into Chinese save-first discovery copy.": "把优惠转成以收藏为先的中文发现文案。",
  Prepare: "准备",
  "Owner approval note": "商家审批说明",
  "Explain what the owner needs to approve before publishing.": "说明商家发布前需要批准什么。",
  Map: "映射",
  "Local ROI events": "本地 ROI 事件",
  "Attach calls, DMs, coupon scans, saves, and map clicks.": "关联来电、私信、优惠券扫码、收藏和地图点击。",
  "Instagram DM": "Instagram 私信",
  "Mia R.": "Mia R.",
  "Do you have tables for four at 12:30?": "12:30 还有四人桌吗？",
  "Booking request": "预订请求",
  "Yes, we can help. Want me to hold a 12:30 table for four under your name?":
    "可以，我们能帮忙。需要我用你的名字保留 12:30 的四人桌吗？",
  "Send booking reply": "发送预订回复",
  "Facebook comment": "Facebook 评论",
  "Tom B.": "Tom B.",
  "Is the weekend lunch special available for takeout?": "周末午餐特惠可以外带吗？",
  "Offer question": "优惠咨询",
  "Yes, takeout is available until 2 PM. You can call ahead and we will have it ready.":
    "可以外带，供应到下午 2 点。你可以提前打电话，我们会帮你准备好。",
  "Reply publicly": "公开回复",
  "Xiaohongshu comment": "小红书评论",
  "Local visit question": "到店问题",
  "Translate + reply": "翻译并回复",
  "Facebook and Google Local drove call taps.": "Facebook 和 Google 本地带来了电话点击。",
  "Instagram DM keyword created appointment intent.": "Instagram 私信关键词产生了预约意图。",
  "Story reminder captured direct questions.": "Story 提醒捕获了直接咨询。",
  "TikTok offer code was used in-store.": "TikTok 优惠码已在店内使用。",
  "Xiaohongshu and Instagram created return intent.": "小红书和 Instagram 带来了回访意图。",
  "Google Local captured nearby searchers.": "Google 本地捕获了附近搜索用户。",
  "One offer becomes five native plans": "一个优惠生成五个原生方案",
  "Each channel gets a different hook, CTA, KPI, and publishing path instead of copy-paste posting.":
    "每个渠道都有不同钩子、行动按钮、指标和发布路径，而不是复制粘贴。",
  "Xiaohongshu is built as a native channel": "小红书作为原生渠道构建",
  "Chinese copy, save-first structure, search keywords, cover text, and KOC/UGC guidance are included.":
    "包含中文文案、收藏优先结构、搜索关键词、封面文字和 KOC/UGC 指引。",
  "Local ROI is attached before publishing": "发布前就绑定本地 ROI",
  "Calls, bookings, DMs, coupon scans, saves, and map clicks are mapped to the content before approval.":
    "审批前就把来电、预订、私信、优惠券扫码、收藏和地图点击映射到内容。",
  "Assisted publishing is part of delivery": "辅助发布也是交付的一部分",
  "For restricted channels, LocalPilot saves a ready-to-post package with assets, caption, and checklist.":
    "对于受限渠道，LocalPilot 会保存包含素材、文案和清单的可发布包。",
  "Demand capture through a fast local hook": "用快速本地钩子捕获需求",
  "22s vertical video": "22 秒竖版视频",
  "Owner-led short video with a fast before/after payoff and a clear local offer.":
    "店主出镜短视频，快速展示前后效果，并给出清晰本地优惠。",
  "Schedule video after owner approval": "商家批准后排期视频",
  "Monday 9:00 AM": "周一上午 9:00",
  "22s vertical cut": "22 秒竖版剪辑",
  "cover text": "封面文字",
  "coupon code": "优惠码",
  "first comment": "首条评论",
  "coupon scan": "优惠券扫码",
  "profile tap": "资料点击",
  "map click": "地图点击",
  "Keep claim simple and make the offer window visible in the first caption line.":
    "保持表述简单，并在文案第一行明确优惠有效时间。",
  "POV: your weekday lunch break finally got upgraded.": "POV：你的工作日午休终于升级了。",
  "Fresh plate, fast service, and a lunch special worth saving. Show this post at checkout today.":
    "新鲜餐盘、快速出餐、值得收藏的午餐特惠。今天结账时出示这条帖子。",
  "Lunch under 15 minutes": "15 分钟内吃上午餐",
  "Show coupon in-store": "到店出示优惠券",
  "Uses a short sensory opening, clear local payoff, and a redeemable action instead of a generic brand post.":
    "用短促感官开场、明确本地收益和可兑换动作，避免泛泛品牌帖。",
  "Approve video cut and coupon wording": "批准视频剪辑和优惠券措辞",
  "Hook in first 2 seconds": "前 2 秒出现钩子",
  "Owner voiceover approved": "店主旁白已批准",
  "Coupon code attached": "优惠码已附加",
  "Visual proof for saves, DMs, and profile visits": "用视觉证明推动收藏、私信和资料访问",
  "Reel + story follow-up": "Reel + Story 跟进",
  "Reel sells the visual craving; story turns attention into a DM keyword.":
    "Reel 激发视觉欲望，Story 把注意力转成私信关键词。",
  "Schedule Reel and story reminder": "排期 Reel 和 Story 提醒",
  "Tuesday 12:30 PM": "周二中午 12:30",
  "Reel caption": "Reel 文案",
  "story sticker": "Story 贴纸",
  "DM keyword": "私信关键词",
  "thumbnail cover": "缩略图封面",
  "save": "收藏",
  "profile visit": "资料访问",
  "Story reminder should use the same DM keyword so replies can be counted.":
    "Story 提醒应使用相同私信关键词，方便统计回复。",
  "Your next lunch plan is already handled.": "你的下一顿午餐已经安排好了。",
  "Golden, fresh, and ready before your break is over. DM LUNCH and we will send today’s special.":
    "金黄新鲜，午休结束前就能吃上。私信 LUNCH，我们会发送今日特惠。",
  "Today’s lunch special": "今日午餐特惠",
  "Combines appetizing visuals with a DM keyword so the business can capture intent and reply quickly.":
    "把诱人的视觉和私信关键词结合起来，让商家捕获意图并快速回复。",
  "Approve story sticker and DM reply draft": "批准 Story 贴纸和私信回复草稿",
  "Reel caption ready": "Reel 文案已准备",
  "Story sticker queued": "Story 贴纸已排队",
  "Auto-reply draft prepared": "自动回复草稿已准备",
  "Local trust and community reach": "本地信任和社区触达",
  "Community post": "社区帖子",
  "Neighbor-style update that feels useful in local groups and owner pages.":
    "像邻里更新一样有用，适合本地群组和商家主页。",
  "Assisted publish to page and local group": "辅助发布到主页和本地群组",
  "Wednesday 6:00 PM": "周三下午 6:00",
  "community-safe copy": "社区友好文案",
  "call CTA": "电话行动按钮",
  "owner note": "商家说明",
  "comment reply": "评论回复",
  "call tap": "电话点击",
  comment: "评论",
  share: "分享",
  "Avoid spammy sales phrasing so the post stays appropriate for community spaces.":
    "避免强销售措辞，让帖子适合社区空间。",
  "A fresh lunch special for neighbors this week.": "本周给邻居们的新鲜午餐特惠。",
  "We made extra for the weekday rush. Stop by before 2 PM, or call ahead and we will have it ready.":
    "我们为工作日高峰多准备了一些。下午 2 点前到店，或提前来电我们帮你备好。",
  "Neighborhood lunch update": "邻里午餐更新",
  "Call ahead": "提前来电",
  "Speaks like a neighborhood update, not an ad, and drives calls from people who already know the area.":
    "语气像邻里更新而不是广告，并推动熟悉本地的人打电话。",
  "Approve creative angle, CTA, and tracking event": "批准创意角度、行动按钮和追踪事件",
  "Confirm call-ahead availability": "确认可提前来电",
  "Community-safe copy": "社区友好文案",
  "Call CTA verified": "电话行动按钮已验证",
  "Local group timing selected": "本地群组发布时间已选择",
  "Searchable Chinese-language discovery": "可搜索的中文发现",
  "RED note": "小红书笔记",
  "Save-first local recommendation note with Chinese search keywords and cover copy.":
    "收藏优先的本地推荐笔记，包含中文搜索关键词和封面文案。",
  "Assisted RED publishing package": "辅助小红书发布包",
  "Thursday 8:00 PM": "周四晚上 8:00",
  "Chinese note": "中文笔记",
  "cover title": "封面标题",
  "keyword set": "关键词组",
  "KOC brief": "KOC 简报",
  inquiry: "咨询",
  "Do not translate directly. Keep the note useful, searchable, and recommendation-led.":
    "不要直译。保持笔记有用、可搜索，并以推荐为导向。",
  "Uses save-first structure, Chinese copy, search keywords, and 种草 framing instead of direct translation.":
    "使用收藏优先结构、中文文案、搜索关键词和种草框架，而不是直译。",
  "Review Chinese copy and cover text": "审核中文文案和封面文字",
  "Keywords added": "关键词已添加",
  "Cover text approved": "封面文字已批准",
  "KOC brief ready": "KOC 简报已准备",
  "High-intent local conversion": "高意图本地转化",
  "Business profile update": "商家资料更新",
  "Profile update for people already searching nearby and ready to call or get directions.":
    "面向正在附近搜索、准备来电或导航的人群的资料更新。",
  "Google Business profile update": "Google 商家资料更新",
  "Friday 10:00 AM": "周五上午 10:00",
  "business profile caption": "商家资料文案",
  "offer window": "优惠窗口",
  "map CTA": "地图行动按钮",
  "direction request": "导航请求",
  "Hours, location, phone number, and offer expiration must be confirmed before publishing.":
    "发布前必须确认营业时间、地址、电话号码和优惠截止时间。",
  "Today’s special is live near you.": "附近今日特惠已上线。",
  "Fresh weekday lunch special available until 2 PM. Tap for directions or call ahead.":
    "工作日午餐特惠供应至下午 2 点。点击导航或提前来电。",
  "Lunch special near me": "附近午餐特惠",
  "Get directions": "获取路线",
  "Captures people already searching nearby and ties the content to directions, calls, and visits.":
    "捕获正在附近搜索的人，并把内容绑定到导航、来电和到店。",
  "Confirm service area, hours, and phone CTA": "确认服务区域、营业时间和电话行动按钮",
  "Business hours checked": "营业时间已检查",
  "Map CTA active": "地图行动按钮已启用",
  "Offer expiry set": "优惠截止时间已设置",
  "Five platform-native post plans with captions and CTAs.": "五个渠道原生帖子方案，包含文案和行动按钮。",
  "Channel-specific assets, tracking events, and publishing mode.": "各渠道专属素材、追踪事件和发布方式。",
  "Approval status and frozen snapshots returned by the workflow API.": "审批状态和冻结快照由工作流 API 返回。",
  "Calls and map clicks attached to Google Local and Facebook.": "来电和地图点击已关联到 Google 本地和 Facebook。",
  "DM keyword tracking attached to Instagram.": "私信关键词追踪已关联到 Instagram。",
  "Saves and profile visits attached to Xiaohongshu.": "收藏和资料访问已关联到小红书。",
  "Nearby owner-led offers are outperforming menu-only posts.": "附近店主出镜优惠表现优于纯菜单帖子。",
  "Price anchoring and short owner intros are the strongest patterns.": "价格锚点和店主短开场是最强模式。",
  "Next action: request a 10-second owner intro before final export.": "下一步：最终导出前请求 10 秒店主开场。",
  "Build a week of posts for": "为",
  "using the offer": "使用优惠",
  "Make each channel native and track local business outcomes.": "让每个渠道都原生化，并追踪本地生意结果。",
  "Drafted a local campaign with platform-specific captions, approval notes, and ROI events to track.":
    "已生成本地营销活动，包含平台专属文案、审批说明和待追踪 ROI 事件。",
  "I will create platform-native posts, reserve Xiaohongshu for searchable recommendations, and track calls, DMs, coupon scans, bookings, and map clicks.":
    "我会创建平台原生帖子，为小红书保留可搜索推荐内容，并追踪来电、私信、优惠券扫码、预订和地图点击。",
  "LocalPilot connects the content plan to business actions: calls from Facebook and Google, DMs from Instagram, saves from Xiaohongshu, and coupon scans from TikTok.":
    "LocalPilot 把内容计划连接到生意动作：Facebook 和 Google 带来来电，Instagram 带来私信，小红书带来收藏，TikTok 带来优惠券扫码。",
  "This module uses fake demo data for customer review.": "此模块使用模拟演示数据，方便客户审核。",
  "Move the Facebook offer to Thursday morning for stronger local group pickup.":
    "把 Facebook 优惠移到周四上午，以获得更强本地群组触达。",
  "Create a RED note around \"weekend lunch near me\" with save-first formatting.":
    "围绕“附近周末午餐”创建小红书笔记，并采用收藏优先格式。",
  "Recycle the top Instagram Reel as an evergreen campaign next month.":
    "下个月把表现最佳的 Instagram Reel 复用为常青活动。",
  "Nearby competitors are getting traction with owner-led lunch specials and \"under $15\" captions.":
    "附近竞品正在通过店主出镜午餐特惠和“15 美元以内”文案获得增长。",
  "AI marketing operator for local businesses.": "为本地商家打造的 AI 营销运营助手。",
  "Goal:": "目标：",
  for: "，面向",
  "within a": "，覆盖",
  "channels approved and": "个渠道已批准，",
  "owner tasks complete.": "个商家任务已完成。",
  "channels approved. Complete checklist items, then save the assisted publishing package.":
    "个渠道已批准。完成清单后保存辅助发布包。",
  plan: "方案",
  "KPI:": "指标：",
  ".": "。",
  "HVAC service": "HVAC 服务",
  "Coupon scans + map clicks": "优惠券扫码 + 地图点击",
  "DMs + saves": "私信 + 收藏",
  "Calls + repeat visits": "来电 + 复访",
  "Saves + profile visits": "收藏 + 资料访问",
  "Map clicks + calls": "地图点击 + 来电",
  "Calls + quote clicks": "来电 + 报价点击",
  "DMs + booked visits": "私信 + 已预约上门",
  "Calls + referrals": "来电 + 转介绍",
  "Saves + inquiries": "收藏 + 咨询",
  "Website visits + calls": "网站访问 + 来电",
  "DMs + appointment requests": "私信 + 预约请求",
  "Calls + shares": "来电 + 分享",
  "Calls + directions": "来电 + 导航",
  "Map clicks + saves": "地图点击 + 收藏",
  "Messages + calls": "消息 + 来电",
});

const zhPhraseTranslations = Object.entries({
  "Goal: ": "目标：",
  " for ": "，面向 ",
  " within a ": "，覆盖 ",
  "AI strategy": "AI 策略",
  "Turn one offer into channel-specific customer actions.": "把一个优惠转成各渠道专属客户行动。",
  "TikTok earns attention, Instagram captures DMs, Facebook builds local trust, Xiaohongshu creates searchable Chinese discovery, and Google Local captures high-intent visits.":
    "TikTok 获取注意力，Instagram 捕获私信，Facebook 建立本地信任，小红书创造可搜索中文发现，Google 本地捕获高意图到店用户。",
  " channels pending": " 个渠道待处理",
  " channels approved. Complete checklist items, then save the assisted publishing package.":
    " 个渠道已批准。完成清单后保存辅助发布包。",
  " channels approved and ": " 个渠道已批准，",
  " owner tasks complete.": " 个商家任务已完成。",
  " ready for owner review": " 可提交给商家审核",
  " plan": " 方案",
  " · KPI: ": " · 指标：",
  " ROI note added to report.": " ROI 备注已添加到报告。",
  " demo action saved.": " 演示操作已保存。",
  " marked in ": " 已标记于 ",
  " saved.": " 已保存。",
  " approved.": " 已批准。",
  " marked for changes.": " 已标记为需修改。",
  " completed.": " 已完成。",
  " completed for ": " 已为 ",
  "I updated channel copy, approval notes, and local ROI tracking in the demo plan.":
    "我已更新演示方案中的渠道文案、审批说明和本地 ROI 追踪。",
  "Drafted a local campaign from ": "已根据 ",
  ". I added platform-specific captions, a Xiaohongshu angle, approval notes, and ROI events to track.":
    " 生成本地营销活动，并加入平台专属文案、小红书角度、审批说明和 ROI 追踪事件。",
  " is promoting ": " 正在推广 ",
  ". Built to ": "。目标是 ",
  "Captures high-intent local searchers who are ready to call, request directions, or book ":
    "捕获准备来电、导航或预约 ",
  "Uses Chinese copy, save-first structure, and searchable local keywords for ":
    "为 ",
  " discovery.": " 发现使用中文文案、收藏优先结构和可搜索本地关键词。",
  "Matches ": "将 ",
  " behavior to a concrete local action instead of reposting the same generic message.":
    " 行为匹配到具体本地行动，而不是重复发布泛泛内容。",
  "Confirm ": "确认 ",
  " details": " 详情",
  "Attach ": "附加 ",
  " tracking": " 追踪",
  "Review ": "审核 ",
  " copy": " 文案",
  "KPI:": "指标：",
  "Show coupon in-store": "到店出示优惠券",
  "Call ahead": "提前来电",
  "Get directions": "获取路线",
  "Book tune-up": "预约保养",
  "Book consult": "预约咨询",
  "Request appointment": "请求预约",
  "Book appointment": "预约",
  "Visit this weekend": "本周末到店",
  "Ask about availability": "询问库存",
  "near me": "附近",
  "Restaurant or cafe客户": "餐厅或咖啡店客户",
  "HVAC service客户": "HVAC 服务客户",
  "Salon or beauty客户": "沙龙或美容客户",
  "Clinic or wellness客户": "诊所或健康服务客户",
  "Retail shop客户": "零售店客户",
  "Restaurant or cafe推荐": "餐厅或咖啡店推荐",
  "HVAC service推荐": "HVAC 服务推荐",
  "Salon or beauty推荐": "沙龙或美容推荐",
  "Clinic or wellness推荐": "诊所或健康服务推荐",
  "Retail shop推荐": "零售店推荐",
  "Weekend lunch special": "周末午餐特惠",
  "Spring AC tune-up": "春季空调保养",
  "New client color refresh": "新客染发焕新",
  "Same-week wellness visit": "本周健康问诊",
  "Weekend decor drop": "周末家居新品",
  "increase weekday lunch visits": "提升工作日午餐到店",
  "book high-intent service calls before peak season": "旺季前预约高意图服务来电",
  "fill weekday appointment gaps": "填补工作日预约空档",
  "increase appointment requests from local families": "提升本地家庭预约请求",
  "drive store visits and product saves": "带动到店和商品收藏",
  "3-mile local audience": "3 英里本地受众",
  "homeowners within 12 miles": "12 英里内房主",
  "beauty clients within 5 miles": "5 英里内美容客户",
  "families within 8 miles": "8 英里内家庭",
  "local shoppers within 6 miles": "6 英里内本地购物者",
  "coupon scans": "优惠券扫码",
  "quote requests": "报价请求",
  "booked visits": "已预约上门",
  "website visits": "网站访问",
  "appointment requests": "预约请求",
  "profile visits": "资料访问",
  "repeat visits": "复访",
  "referrals": "转介绍",
  "shares": "分享",
  "directions": "导航",
  "inquiries": "咨询",
  "comments": "评论",
  "calls": "来电",
  "bookings": "预订",
});

const sortedZhPhraseTranslations = [...zhPhraseTranslations].sort((a, b) => b[0].length - a[0].length);

const translateDynamicText = (text) => {
  const normalized = normalizeTextKey(text);
  const exact = zhTranslations[normalized];
  if (exact) {
    return exact;
  }

  let translated = normalized
    .replace(/^(\d+) channels pending$/, "$1 个渠道待处理")
    .replace(/^(\d+)\/(\d+) channels approved\. Complete checklist items, then save the assisted publishing package\.$/, "$1/$2 个渠道已批准。完成清单后保存辅助发布包。")
    .replace(/^(\d+)% ready for owner review$/, "$1% 可提交给商家审核")
    .replace(/^(\d+)\/(\d+) channels approved and (\d+)\/(\d+) owner tasks complete\.$/, "$1/$2 个渠道已批准，$3/$4 个商家任务已完成。")
    .replace(/^Build a week of posts for (.+) using the offer "(.+)"\. Make each channel native and track local business outcomes\.$/, "为 $1 使用优惠“$2”生成一周帖子。让每个渠道都原生化，并追踪本地生意结果。")
    .replace(/^(.+) is promoting (.+)\. Built to (.+)\.$/, "$1 正在推广 $2。目标是 $3。")
    .replace(/^Captures high-intent local searchers who are ready to call, request directions, or book (.+)\.$/, "捕获准备来电、导航或预约 $1 的高意图本地搜索用户。")
    .replace(/^Uses Chinese copy, save-first structure, and searchable local keywords for (.+) discovery\.$/, "为 $1 发现使用中文文案、收藏优先结构和可搜索本地关键词。")
    .replace(/^Matches (.+) behavior to a concrete local action instead of reposting the same generic message\.$/, "将 $1 的用户行为匹配到具体本地行动，而不是重复发布泛泛内容。")
    .replace(/^Confirm (.+) details$/, "确认 $1 详情")
    .replace(/^Attach (.+) tracking$/, "附加 $1 追踪")
    .replace(/^Review (.+) copy$/, "审核 $1 文案")
    .replace(/^(.+) plan$/, "$1 方案")
    .replace(/^(.+) ROI note added to report\.$/, "$1 ROI 备注已添加到报告。")
    .replace(/^(.+) demo action saved\.$/, "$1 演示操作已保存。")
    .replace(/^(.+) marked in (.+)\.$/, "$1 已标记于 $2。")
    .replace(/^(.+) saved\.$/, "$1 已保存。")
    .replace(/^(.+) approved\.$/, "$1 已批准。")
    .replace(/^(.+) marked for changes\.$/, "$1 已标记为需修改。")
    .replace(/^(.+) completed\.$/, "$1 已完成。")
    .replace(/^(.+) completed for (.+)\. I updated channel copy, approval notes, and local ROI tracking in the demo plan\.$/, "$1 已为 $2 完成。我已更新演示方案中的渠道文案、审批说明和本地 ROI 追踪。")
    .replace(/^Drafted a local campaign from "(.+)"\. I added platform-specific captions, a Xiaohongshu angle, approval notes, and ROI events to track\.$/, "已根据“$1”生成本地营销活动，并加入平台专属文案、小红书角度、审批说明和 ROI 追踪事件。");

  for (const [source, target] of sortedZhPhraseTranslations) {
    translated = translated.split(source).join(target);
  }

  return translated === normalized ? null : translated;
};

const normalizeTextKey = (text) => text.trim().replace(/\s+/g, " ");

const translateTextNode = (node, language) => {
  const currentText = node.nodeValue || "";
  if (!currentText.trim()) {
    return;
  }

  const translatedText = node.__localpilotTranslatedText;
  if (language === "zh") {
    if (!translatedText || currentText !== translatedText) {
      node.__localpilotOriginalText = currentText;
    }

    const originalText = node.__localpilotOriginalText || currentText;
    const leading = originalText.match(/^\s*/)?.[0] || "";
    const trailing = originalText.match(/\s*$/)?.[0] || "";
    const translated = translateDynamicText(originalText);

    if (translated) {
      node.__localpilotTranslatedText = `${leading}${translated}${trailing}`;
      if (node.nodeValue !== node.__localpilotTranslatedText) {
        node.nodeValue = node.__localpilotTranslatedText;
      }
    }

    return;
  }

  if (node.__localpilotOriginalText && node.nodeValue !== node.__localpilotOriginalText) {
    node.nodeValue = node.__localpilotOriginalText;
  }
};

const shouldTranslateTextNode = (node) => {
  const parent = node.parentElement;
  return Boolean(parent && !parent.closest("[data-no-translate], script, style, textarea, input"));
};

const translatableAttributes = ["placeholder", "aria-label", "alt", "title"];

const translateElementAttributes = (element, language) => {
  if (element.closest("[data-no-translate], script, style")) {
    return;
  }

  translatableAttributes.forEach((attributeName) => {
    const currentValue = element.getAttribute(attributeName);
    if (!currentValue?.trim()) {
      return;
    }

    element.__localpilotOriginalAttributes ||= {};
    element.__localpilotTranslatedAttributes ||= {};

    if (language === "zh") {
      if (!element.__localpilotTranslatedAttributes[attributeName] || currentValue !== element.__localpilotTranslatedAttributes[attributeName]) {
        element.__localpilotOriginalAttributes[attributeName] = currentValue;
      }

      const originalValue = element.__localpilotOriginalAttributes[attributeName] || currentValue;
      const translated = translateDynamicText(originalValue);
      if (translated) {
        element.__localpilotTranslatedAttributes[attributeName] = translated;
        element.setAttribute(attributeName, translated);
      }
      return;
    }

    if (element.__localpilotOriginalAttributes[attributeName]) {
      element.setAttribute(attributeName, element.__localpilotOriginalAttributes[attributeName]);
    }
  });
};

const translateCampaignInputValue = (element, language) => {
  if (!element.matches(".campaign-builder input")) {
    return;
  }

  if (language === "zh") {
    if (!element.__localpilotTranslatedValue || element.value !== element.__localpilotTranslatedValue) {
      element.__localpilotOriginalValue = element.value;
    }
    const translated = translateDynamicText(element.__localpilotOriginalValue || element.value);
    if (translated) {
      element.__localpilotTranslatedValue = translated;
      element.value = translated;
    }
    return;
  }

  if (element.__localpilotOriginalValue && element.value !== element.__localpilotOriginalValue) {
    element.value = element.__localpilotOriginalValue;
  }
};

const translateSubtree = (root, language) => {
  [root, ...root.querySelectorAll("*")].forEach((element) => {
    translateElementAttributes(element, language);
    translateCampaignInputValue(element, language);
  });

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => (shouldTranslateTextNode(node) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT),
  });

  while (walker.nextNode()) {
    translateTextNode(walker.currentNode, language);
  }
};

const LanguageContext = createContext(null);

function LanguageProvider({ children }) {
  const [language, setLanguage] = useState(() => readPreference(LANGUAGE_STORAGE_KEY, "en"));

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      toggleLanguage: () => setLanguage((current) => (current === "zh" ? "en" : "zh")),
    }),
    [language],
  );

  useEffect(() => {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    writePreference(LANGUAGE_STORAGE_KEY, language);
  }, [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used inside LanguageProvider");
  }
  return context;
}

function TranslationLayer() {
  const { language } = useLanguage();

  useEffect(() => {
    const root = document.getElementById("root");
    if (!root) {
      return undefined;
    }

    let translateTimer = 0;
    const applyTranslations = () => {
      window.clearTimeout(translateTimer);
      translateTimer = window.setTimeout(() => translateSubtree(root, language), 80);
    };

    applyTranslations();
    const observer = new MutationObserver(applyTranslations);
    observer.observe(root, { childList: true, subtree: true });

    return () => {
      window.clearTimeout(translateTimer);
      observer.disconnect();
    };
  }, [language]);

  return null;
}

function LanguageToggle({ compact = false }) {
  const { language, toggleLanguage } = useLanguage();

  return (
    <button
      className={`language-toggle ${compact ? "compact-toggle" : ""}`}
      type="button"
      onClick={toggleLanguage}
      aria-label="Switch language between English and Chinese"
      aria-pressed={language === "zh"}
      data-no-translate
    >
      <span className={language === "en" ? "active" : ""}>EN</span>
      <span className={language === "zh" ? "active" : ""}>中文</span>
    </button>
  );
}

const platforms = [
  ["TikTok", "Hook", "This lunch special hits different.", restaurant],
  ["Instagram", "Reel", "Weekend lunch just got booked.", restaurant],
  ["Facebook", "Local Post", "Fresh ingredients. Big flavor. See you this weekend.", restaurant],
  ["Xiaohongshu", "种草 Note", "周末午餐推荐, 好吃不贵, 值得打卡.", restaurant],
];

const modules = [
  "Home",
  "AI Studio",
  "Publish",
  "Calendar",
  "Inbox",
  "Discover",
  "Analytics",
  "Reports",
  "Media Library",
  "Approvals",
  "Clients",
  "Settings",
];

const moduleSlug = (module) => module.toLowerCase().replace(/[^a-z0-9]+/g, "-");

const moduleFromSlug = (slug) =>
  modules.find((module) => moduleSlug(module) === slug || module.toLowerCase() === String(slug || "").toLowerCase());

const moduleDetails = {
  Home: {
    kicker: "Local growth workbench",
    title: "One input, channel-native growth plan",
    view: "workbench",
  },
  "AI Studio": {
    kicker: "Create, refine, schedule",
    title: "AI campaign generator",
    view: "ai",
  },
  Publish: {
    kicker: "Network-tailored posts",
    title: "Publishing pipeline",
    cards: [
      ["Composer", "Turn one offer into channel-specific posts with captions, hashtags, and cover copy."],
      ["Bulk schedule", "Queue weeks of posts from AI-generated campaign plans or CSV-style batches."],
      ["Assisted publishing", "Package ready-to-post assets for channels with limited publishing APIs."],
    ],
  },
  Calendar: {
    kicker: "Client-visible planning",
    title: "Weekly publishing plan",
    summary: "Pick the next slot, review the copy, and keep the week moving.",
    view: "calendar",
  },
  Inbox: {
    kicker: "Engage",
    title: "Unified comments and DMs",
    view: "inbox",
  },
  Discover: {
    kicker: "Trend-to-action",
    title: "Local discovery feed",
    cards: [
      ["Trending topics", "Score platform trends as useful, risky, or irrelevant for each local business."],
      ["Competitor watcher", "Track nearby businesses, offers, posting rhythm, and engagement spikes."],
      ["Content sources", "Organize RSS, local news, newsletters, and inspiration by client workspace."],
    ],
  },
  Analytics: {
    kicker: "Social + business outcomes",
    title: "Performance intelligence",
    view: "analytics",
  },
  Reports: {
    kicker: "Agency proof",
    title: "Branded client reporting",
    cards: [
      ["Scheduled reports", "Send presentation-ready summaries for social results and Local ROI."],
      ["Client notes", "Explain what changed, what worked, and what to approve next."],
      ["Export package", "Bundle top posts, analytics, comments, and next-week recommendations."],
    ],
  },
  "Media Library": {
    kicker: "Assets",
    title: "Reusable content library",
    cards: [
      ["Brand folders", "Store approved images, videos, logos, offers, and campaign references per client."],
      ["AI variants", "Generate captions, image prompts, thumbnails, and first-comment ideas from assets."],
      ["Usage history", "See where every asset has been published and how it performed."],
    ],
  },
  Approvals: {
    kicker: "Client collaboration",
    title: "Review and sign-off",
    cards: [
      ["No-login review", "Share client approval links without exposing the full workspace."],
      ["Revision notes", "Keep client comments, internal notes, and final approvals attached to each post."],
      ["Compliance checklist", "Flag risky claims, missing disclaimers, and platform limits."],
    ],
  },
  Clients: {
    kicker: "Agency workspace",
    title: "Client management",
    cards: [
      ["Workspace separation", "Keep accounts, calendars, media, reports, and roles separate per client."],
      ["Onboarding profile", "Capture business type, location, offers, audience, voice, and competitors."],
      ["Service tiers", "Track pilot, growth, and multi-location clients from one command center."],
    ],
  },
  Settings: {
    kicker: "Controls",
    title: "Workspace configuration",
    cards: [
      ["Social accounts", "Mock TikTok, Instagram, Facebook, Xiaohongshu, and Google Business workflows."],
      ["Brand knowledge", "Save voice, services, offers, customer profile, and approved phrases."],
      ["Team roles", "Assign creators, reviewers, approvers, and report recipients."],
    ],
  },
};

const moduleWorkflows = {
  Publish: {
    focus: "Publishing pipeline",
    summary: "Turn approved channel plans into scheduled posts or assisted publishing packages.",
    steps: [
      ["Ready", "TikTok vertical cut", "Schedule after owner approval"],
      ["Needs setup", "Instagram story reminder", "Attach DM keyword tracking"],
      ["Assisted", "Xiaohongshu RED note", "Copy package for manual publish"],
      ["Ready", "Google Local update", "Confirm hours and offer window"],
    ],
  },
  Discover: {
    focus: "Trend-to-action queue",
    summary: "Convert local competitor and trend signals into specific post ideas for the selected business.",
    steps: [
      ["Hot", "Owner-led lunch specials", "Use owner intro in TikTok and Facebook"],
      ["Rising", "Weekend near me searches", "Create Google Local and RED keyword set"],
      ["Watch", "Under $15 captions", "Test price-anchor caption on Instagram"],
      ["Ignore", "Generic viral audio", "Low fit for local conversion goal"],
    ],
  },
  Reports: {
    focus: "Client-ready proof",
    summary: "Show the owner what was created, what got approved, and which local actions were generated.",
    steps: [
      ["Included", "Channel plan summary", "Five native outputs with status"],
      ["Included", "Local ROI snapshot", "Calls, DMs, saves, coupon scans, map clicks"],
      ["Draft", "Next week recommendation", "Owner intro plus weekday offer test"],
      ["Export", "Agency report", "PDF-style handoff prepared from fake data"],
    ],
  },
  "Media Library": {
    focus: "Reusable assets",
    summary: "Keep approved visuals, captions, offers, and generated variants tied to the business profile.",
    steps: [
      ["Saved", "Lunch special hero clip", "Used by TikTok and Instagram"],
      ["Generated", "RED cover title", "Used by Xiaohongshu package"],
      ["Saved", "Owner intro prompt", "Requested before final export"],
      ["Available", "Google profile image", "Ready for local update"],
    ],
  },
  Approvals: {
    focus: "Owner sign-off",
    summary: "Review every channel plan, request changes, and prepare a no-login approval package.",
    steps: [
      ["Pending", "TikTok hook and coupon wording", "Approve or request edit"],
      ["Pending", "Instagram DM keyword", "Confirm auto-reply wording"],
      ["Pending", "Xiaohongshu Chinese copy", "Review cover title and keywords"],
      ["Pending", "Google Local offer window", "Confirm hours and phone CTA"],
    ],
  },
  Clients: {
    focus: "Client workspace",
    summary: "Switch fake local business profiles and load the right offers, audience, channels, and ROI events.",
    steps: [
      ["Active", "Sunny Side Bistro", "Restaurant local visit workflow"],
      ["Template", "Northline HVAC", "Calls and booked service visits"],
      ["Template", "Glow Room Salon", "DMs, bookings, and saves"],
      ["Template", "Harbor Family Clinic", "Appointment requests and calls"],
    ],
  },
  Settings: {
    focus: "Demo configuration",
    summary: "Mock the operational controls that will later connect to Odoo, social accounts, and customer data.",
    steps: [
      ["Mocked", "Social accounts", "TikTok, Instagram, Facebook, RED, Google"],
      ["Mocked", "Business knowledge", "Offer, goal, audience, voice, competitors"],
      ["Mocked", "ROI events", "Calls, bookings, DMs, coupon scans, saves, maps"],
      ["Later", "Odoo connection", "Replace fake sample data with customer records"],
    ],
  },
};

const schedule = [
  ["Mon 9:00", "TikTok hook", "Lunch special trend angle", "Approved", "green"],
  ["Tue 12:30", "Instagram Reel", "Visual story + offer CTA", "Needs review", "coral"],
  ["Wed 6:00", "Facebook post", "Community update", "Scheduled", "blue"],
  ["Thu 8:00", "Xiaohongshu note", "Searchable Chinese content", "Draft", "red"],
  ["Fri 10:00", "Story reminder", "Coupon scan push", "Ready", "green"],
];

const aiStudioTasks = [
  ["Generate", "Weekly channel plan", "Create five channel-native outputs from one offer."],
  ["Rewrite", "Xiaohongshu note", "Convert the offer into Chinese save-first discovery copy."],
  ["Prepare", "Owner approval note", "Explain what the owner needs to approve before publishing."],
  ["Map", "Local ROI events", "Attach calls, DMs, coupon scans, saves, and map clicks."],
];

const inboxThreads = [
  {
    source: "Instagram DM",
    customer: "Mia R.",
    message: "Do you have tables for four at 12:30?",
    intent: "Booking request",
    draft: "Yes, we can help. Want me to hold a 12:30 table for four under your name?",
    action: "Send booking reply",
  },
  {
    source: "Facebook comment",
    customer: "Tom B.",
    message: "Is the weekend lunch special available for takeout?",
    intent: "Offer question",
    draft: "Yes, takeout is available until 2 PM. You can call ahead and we will have it ready.",
    action: "Reply publicly",
  },
  {
    source: "Xiaohongshu comment",
    customer: "小林",
    message: "请问附近停车方便吗?",
    intent: "Local visit question",
    draft: "附近有街边停车和公共停车场，午餐时段建议提前一点到。",
    action: "Translate + reply",
  },
];

const localRoiSignals = [
  ["28", "Calls", "Facebook and Google Local drove call taps."],
  ["17", "Bookings", "Instagram DM keyword created appointment intent."],
  ["34", "DMs", "Story reminder captured direct questions."],
  ["52", "Coupon scans", "TikTok offer code was used in-store."],
  ["91", "Saves", "Xiaohongshu and Instagram created return intent."],
  ["76", "Map clicks", "Google Local captured nearby searchers."],
];

const walkthroughSteps = [
  {
    title: "Start with the offer",
    module: "Home",
    note: "Show how one business input creates a weekly plan.",
    channel: 0,
  },
  {
    title: "Inspect Xiaohongshu",
    module: "Home",
    note: "Highlight native Chinese copy, keywords, cover text, and save-first structure.",
    channel: 3,
  },
  {
    title: "Generate with AI",
    module: "AI Studio",
    note: "Show task buttons and the per-channel AI output list.",
  },
  {
    title: "Review the calendar",
    module: "Calendar",
    note: "Approve or request edits from the scheduled post plan.",
    post: 1,
  },
  {
    title: "Reply to customers",
    module: "Inbox",
    note: "Show intent, suggested reply, and local visit context.",
    inbox: 2,
  },
  {
    title: "Explain local ROI",
    module: "Analytics",
    note: "Connect posts to calls, bookings, DMs, saves, coupon scans, and map clicks.",
  },
];

const pricingPlans = [
  {
    name: "Starter Pilot",
    description: "Perfect for trying it out.",
    price: "$0",
    suffix: "14-day pilot",
    cta: "Join the pilot",
    tone: "green",
    features: ["1 business location", "1 video or promotion per week", "4 platforms", "Local ROI dashboard"],
  },
  {
    name: "Growth Pilot",
    description: "For businesses ready to grow.",
    price: "$49",
    suffix: "/ week",
    cta: "Join the pilot",
    tone: "coral",
    popular: true,
    features: [
      "1 business location",
      "Up to 3 uploads per week",
      "4 platforms including Xiaohongshu",
      "Trend-to-Action and competitor watcher",
    ],
  },
  {
    name: "Scale Pilot",
    description: "For agencies and multi-location teams.",
    price: "$99",
    suffix: "/ week",
    cta: "Request demo",
    tone: "blue",
    features: ["Up to 3 locations", "Approval workspace", "Client-ready reports", "Priority support"],
  },
];

const defaultCampaignInput = {
  business: "Sunny Side Bistro",
  businessType: "restaurant",
  offer: "Weekend lunch special",
  goal: "increase weekday lunch visits",
  audience: "3-mile local audience",
};

const businessTemplates = {
  restaurant: {
    label: "Restaurant or cafe",
    business: "Sunny Side Bistro",
    offer: "Weekend lunch special",
    goal: "increase weekday lunch visits",
    audience: "3-mile local audience",
    kpis: "coupon scans, DMs, saves, map clicks",
    byChannel: {
      TikTok: ["POV: your weekday lunch break finally got upgraded.", "Show coupon in-store", "Coupon scans + map clicks"],
      Instagram: ["Your next lunch plan is already handled.", "DM LUNCH", "DMs + saves"],
      Facebook: ["A fresh lunch special for neighbors this week.", "Call ahead", "Calls + repeat visits"],
      Xiaohongshu: ["本地工作日午餐推荐, 方便又好吃", "收藏 + 到店打卡", "Saves + profile visits"],
      "Google Local": ["Today’s special is live near you.", "Get directions", "Map clicks + calls"],
    },
  },
  hvac: {
    label: "HVAC service",
    business: "Northline HVAC",
    offer: "Spring AC tune-up",
    goal: "book high-intent service calls before peak season",
    audience: "homeowners within 12 miles",
    kpis: "calls, quote requests, booked visits, map clicks",
    byChannel: {
      TikTok: ["Your AC should not wait until the first heat wave.", "Book tune-up", "Calls + quote clicks"],
      Instagram: ["Before the heat hits: quick AC tune-up checklist.", "DM COOL", "DMs + booked visits"],
      Facebook: ["Local homeowners: spring AC tune-ups are open this week.", "Call for appointment", "Calls + referrals"],
      Xiaohongshu: ["本地空调保养提醒, 夏天前先检查", "收藏 + 咨询预约", "Saves + inquiries"],
      "Google Local": ["AC tune-up appointments near you.", "Call now", "Map clicks + calls"],
    },
  },
  salon: {
    label: "Salon or beauty",
    business: "Glow Room Salon",
    offer: "New client color refresh",
    goal: "fill weekday appointment gaps",
    audience: "beauty clients within 5 miles",
    kpis: "DMs, bookings, saves, profile visits",
    byChannel: {
      TikTok: ["Watch this color refresh change the whole week.", "Book consult", "Profile visits + DMs"],
      Instagram: ["Soft color refresh with appointment openings this week.", "DM GLOW", "DMs + bookings"],
      Facebook: ["New client color appointments available this week.", "Message to book", "Messages + calls"],
      Xiaohongshu: ["本地染发护理推荐, 自然提亮发色", "收藏 + 私信预约", "Saves + inquiries"],
      "Google Local": ["Hair color appointments near you.", "Book appointment", "Map clicks + calls"],
    },
  },
  clinic: {
    label: "Clinic or wellness",
    business: "Harbor Family Clinic",
    offer: "Same-week wellness visit",
    goal: "increase appointment requests from local families",
    audience: "families within 8 miles",
    kpis: "calls, appointment requests, website visits",
    byChannel: {
      TikTok: ["Three signs it is time to schedule a wellness visit.", "Request appointment", "Website visits + calls"],
      Instagram: ["Same-week wellness visits for local families.", "DM APPT", "DMs + appointment requests"],
      Facebook: ["Same-week wellness appointments are available for local families.", "Call clinic", "Calls + shares"],
      Xiaohongshu: ["本地家庭诊所预约提醒, 本周可约", "收藏 + 咨询", "Saves + inquiries"],
      "Google Local": ["Wellness appointments near you.", "Call clinic", "Calls + directions"],
    },
  },
  retail: {
    label: "Retail shop",
    business: "Juniper Home Shop",
    offer: "Weekend decor drop",
    goal: "drive store visits and product saves",
    audience: "local shoppers within 6 miles",
    kpis: "saves, map clicks, coupon scans, DMs",
    byChannel: {
      TikTok: ["New weekend decor drop just hit the shelves.", "Visit this weekend", "Map clicks + saves"],
      Instagram: ["Save this weekend decor drop before it sells out.", "DM HOLD", "DMs + saves"],
      Facebook: ["New weekend decor arrivals are in-store now.", "Ask about availability", "Comments + calls"],
      Xiaohongshu: ["本地家居店新品推荐, 周末值得逛", "收藏 + 到店", "Saves + profile visits"],
      "Google Local": ["New decor arrivals near you.", "Get directions", "Map clicks + calls"],
    },
  },
};

const businessOptions = Object.entries(businessTemplates).map(([value, template]) => ({
  value,
  label: template.label,
  business: template.business,
}));

const localpilotDifferentiators = [
  {
    title: "One offer becomes five native plans",
    proof: "Each channel gets a different hook, CTA, KPI, and publishing path instead of copy-paste posting.",
  },
  {
    title: "Xiaohongshu is built as a native channel",
    proof: "Chinese copy, save-first structure, search keywords, cover text, and KOC/UGC guidance are included.",
  },
  {
    title: "Local ROI is attached before publishing",
    proof: "Calls, bookings, DMs, coupon scans, saves, and map clicks are mapped to the content before approval.",
  },
  {
    title: "Assisted publishing is part of delivery",
    proof: "For restricted channels, LocalPilot saves a ready-to-post package with assets, caption, and checklist.",
  },
];

const channelPlans = [
  {
    name: "TikTok",
    role: "Demand capture through a fast local hook",
    format: "22s vertical video",
    tone: "green",
    asset: restaurant,
    postAngle: "Owner-led short video with a fast before/after payoff and a clear local offer.",
    publishingMode: "Schedule video after owner approval",
    scheduleSlot: "Monday 9:00 AM",
    assets: ["22s vertical cut", "cover text", "coupon code", "first comment"],
    trackingEvents: ["coupon scan", "profile tap", "map click"],
    riskNote: "Keep claim simple and make the offer window visible in the first caption line.",
    nativeCreative: {
      hook: "POV: your weekday lunch break finally got upgraded.",
      caption: "Fresh plate, fast service, and a lunch special worth saving. Show this post at checkout today.",
      cover: "Lunch under 15 minutes",
      cta: "Show coupon in-store",
    },
    whyItWorks:
      "Uses a short sensory opening, clear local payoff, and a redeemable action instead of a generic brand post.",
    kpi: "Coupon scans + map clicks",
    ownerAction: "Approve video cut and coupon wording",
    checklist: ["Hook in first 2 seconds", "Owner voiceover approved", "Coupon code attached"],
  },
  {
    name: "Instagram",
    role: "Visual proof for saves, DMs, and profile visits",
    format: "Reel + story follow-up",
    tone: "coral",
    asset: restaurant,
    postAngle: "Reel sells the visual craving; story turns attention into a DM keyword.",
    publishingMode: "Schedule Reel and story reminder",
    scheduleSlot: "Tuesday 12:30 PM",
    assets: ["Reel caption", "story sticker", "DM keyword", "thumbnail cover"],
    trackingEvents: ["DM keyword", "save", "profile visit"],
    riskNote: "Story reminder should use the same DM keyword so replies can be counted.",
    nativeCreative: {
      hook: "Your next lunch plan is already handled.",
      caption: "Golden, fresh, and ready before your break is over. DM LUNCH and we will send today’s special.",
      cover: "Today’s lunch special",
      cta: "DM LUNCH",
    },
    whyItWorks:
      "Combines appetizing visuals with a DM keyword so the business can capture intent and reply quickly.",
    kpi: "DMs + saves",
    ownerAction: "Approve story sticker and DM reply draft",
    checklist: ["Reel caption ready", "Story sticker queued", "Auto-reply draft prepared"],
  },
  {
    name: "Facebook",
    role: "Local trust and community reach",
    format: "Community post",
    tone: "blue",
    asset: cafeOwner,
    postAngle: "Neighbor-style update that feels useful in local groups and owner pages.",
    publishingMode: "Assisted publish to page and local group",
    scheduleSlot: "Wednesday 6:00 PM",
    assets: ["community-safe copy", "call CTA", "owner note", "comment reply"],
    trackingEvents: ["call tap", "comment", "share"],
    riskNote: "Avoid spammy sales phrasing so the post stays appropriate for community spaces.",
    nativeCreative: {
      hook: "A fresh lunch special for neighbors this week.",
      caption:
        "We made extra for the weekday rush. Stop by before 2 PM, or call ahead and we will have it ready.",
      cover: "Neighborhood lunch update",
      cta: "Call ahead",
    },
    whyItWorks:
      "Speaks like a neighborhood update, not an ad, and drives calls from people who already know the area.",
    kpi: "Calls + repeat visits",
    ownerAction: "Confirm call-ahead availability",
    checklist: ["Community-safe copy", "Call CTA verified", "Local group timing selected"],
  },
  {
    name: "Xiaohongshu",
    role: "Searchable Chinese-language discovery",
    format: "RED note",
    tone: "red",
    asset: restaurant,
    postAngle: "Save-first local recommendation note with Chinese search keywords and cover copy.",
    publishingMode: "Assisted RED publishing package",
    scheduleSlot: "Thursday 8:00 PM",
    assets: ["Chinese note", "cover title", "keyword set", "KOC brief"],
    trackingEvents: ["save", "profile visit", "inquiry"],
    riskNote: "Do not translate directly. Keep the note useful, searchable, and recommendation-led.",
    nativeCreative: {
      hook: "本地工作日午餐推荐, 方便又好吃",
      caption: "适合上班族午餐、朋友小聚, 分量足, 出餐快。关键词: 本地探店 / 周中午餐 / 性价比",
      cover: "本地午餐推荐",
      cta: "收藏 + 到店打卡",
    },
    whyItWorks:
      "Uses save-first structure, Chinese copy, search keywords, and 种草 framing instead of direct translation.",
    kpi: "Saves + profile visits",
    ownerAction: "Review Chinese copy and cover text",
    checklist: ["Keywords added", "Cover text approved", "KOC brief ready"],
  },
  {
    name: "Google Local",
    role: "High-intent local conversion",
    format: "Business profile update",
    tone: "amber",
    asset: shop,
    postAngle: "Profile update for people already searching nearby and ready to call or get directions.",
    publishingMode: "Google Business profile update",
    scheduleSlot: "Friday 10:00 AM",
    assets: ["business profile caption", "offer window", "map CTA", "call CTA"],
    trackingEvents: ["map click", "call", "direction request"],
    riskNote: "Hours, location, phone number, and offer expiration must be confirmed before publishing.",
    nativeCreative: {
      hook: "Today’s special is live near you.",
      caption: "Fresh weekday lunch special available until 2 PM. Tap for directions or call ahead.",
      cover: "Lunch special near me",
      cta: "Get directions",
    },
    whyItWorks:
      "Captures people already searching nearby and ties the content to directions, calls, and visits.",
    kpi: "Map clicks + calls",
    ownerAction: "Confirm hours and offer window",
    checklist: ["Business hours checked", "Map CTA active", "Offer expiry set"],
  },
];

const inferBusinessType = (businessName) => {
  const match = businessOptions.find((option) => option.business === businessName);
  return match?.value || defaultCampaignInput.businessType;
};

const normalizeCampaignInput = (input = defaultCampaignInput) => {
  const inferredType = input?.businessType && businessTemplates[input.businessType]
    ? input.businessType
    : inferBusinessType(input?.business);
  const template = businessTemplates[inferredType] || businessTemplates[defaultCampaignInput.businessType];

  return {
    business: input?.business || template.business,
    businessType: inferredType,
    offer: input?.offer || template.offer,
    goal: input?.goal || template.goal,
    audience: input?.audience || template.audience,
  };
};

const buildPlansFromInput = (input = defaultCampaignInput) => {
  const normalizedInput = normalizeCampaignInput(input);
  const template = businessTemplates[normalizedInput.businessType] || businessTemplates.restaurant;

  return channelPlans.map((plan) => {
    const [hook, cta, kpi] = template.byChannel[plan.name] || template.byChannel.TikTok;
    const isRed = plan.name === "Xiaohongshu";
    const isGoogle = plan.name === "Google Local";

    return {
      ...plan,
      kpi,
      nativeCreative: {
        ...plan.nativeCreative,
        hook,
        caption: isRed
          ? `${normalizedInput.offer}，适合${template.label}客户收藏和咨询。关键词: 本地推荐 / ${normalizedInput.business}`
          : `${normalizedInput.business} is promoting ${normalizedInput.offer}. Built to ${normalizedInput.goal}.`,
        cover: isRed ? `${template.label}推荐` : isGoogle ? `${normalizedInput.offer} near me` : normalizedInput.offer,
        cta,
      },
      whyItWorks: isGoogle
        ? `Captures high-intent local searchers who are ready to call, request directions, or book ${normalizedInput.offer}.`
        : isRed
          ? `Uses Chinese copy, save-first structure, and searchable local keywords for ${template.label} discovery.`
          : `Matches ${plan.name} behavior to a concrete local action instead of reposting the same generic message.`,
      ownerAction: isGoogle
        ? "Confirm service area, hours, and phone CTA"
        : isRed
          ? "Review Chinese copy, cover text, and keywords"
        : "Approve creative angle, CTA, and tracking event",
      checklist: [
        `Confirm ${normalizedInput.offer} details`,
        `Attach ${cta} tracking`,
        `Review ${plan.name} copy`,
      ].map((text) => ({ text, done: false })),
      status: "Needs review",
    };
  });
};

const createInitialPlans = (input = defaultCampaignInput) =>
  buildPlansFromInput(input).map((plan) => ({
    ...plan,
    status: "Needs review",
    checklist: plan.checklist.map((item) =>
      typeof item === "string" ? { text: item, done: false } : { ...item, done: false },
    ),
  }));

const normalizePlan = (plan, index, input = defaultCampaignInput) => {
  const base = buildPlansFromInput(input)[index] || buildPlansFromInput(input)[0];
  return {
    ...base,
    ...plan,
    nativeCreative: {
      ...base.nativeCreative,
      ...(plan?.nativeCreative || {}),
    },
    status: plan?.status || "Needs review",
    checklist: Array.isArray(plan?.checklist)
      ? plan.checklist.map((item) =>
          typeof item === "string" ? { text: item, done: false } : { text: item.text, done: Boolean(item.done) },
        )
      : base.checklist.map((item) =>
          typeof item === "string" ? { text: item, done: false } : { text: item.text, done: Boolean(item.done) },
        ),
  };
};

const platformDisplayName = (platform = "") => {
  const normalized = platform.toLowerCase();
  if (normalized === "facebook") {
    return "Facebook";
  }
  if (normalized === "tiktok") {
    return "TikTok";
  }
  return platform || "Platform";
};

const workflowCampaignInput = (workflow) => {
  const campaign = workflow.campaigns[0];
  const profile = workflow.businessProfiles[0] || {};
  if (!campaign) {
    return normalizeCampaignInput(defaultCampaignInput);
  }

  return normalizeCampaignInput({
    business: profile.business_name || profile.businessName || defaultCampaignInput.business,
    businessType: profile.business_type || profile.businessType || defaultCampaignInput.businessType,
    offer: campaign.offer,
    goal: campaign.goal,
    audience: campaign.audience,
  });
};

const normalizeWorkflowStatus = (status) =>
  String(status || "needs_review")
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");

const planLifecycleStatus = (plan) => {
  if (plan?.publishJob?.currentStatus) {
    return plan.publishJob.currentStatus;
  }
  if (plan?.approvalSnapshot?.draftVersionId) {
    return "approved";
  }
  return "needs_review";
};

const canRetryPublishJob = (job) => {
  const normalizedJob = normalizePublishJob(job);
  return RETRYABLE_PUBLISH_STATUSES.includes(normalizedJob.currentStatus);
};

const workflowDraftToPlan = (draft, index, workflow) => {
  const displayName = platformDisplayName(draft.platform);
  const base = channelPlans.find((plan) => plan.name === displayName) || channelPlans[index] || channelPlans[0];
  const currentVersion = draft.currentVersion || {};
  const connectedChannel = workflow.connectedChannels.find((channelRef) => channelRef.id === draft.connectedChannelId);
  const approval = workflow.approvals.find(
    (item) => item.draftId === draft.id && item.draftVersionId === currentVersion.id,
  );
  const status = normalizeWorkflowStatus(draft.status);
  const mediaRefs = currentVersion.mediaRefs || [];

  return normalizePlan(
    {
      ...base,
      id: draft.id,
      platform: draft.platform,
      connectedChannelId: draft.connectedChannelId,
      connectedChannel,
      approvalId: approval?.id || "",
      currentVersion,
      approvalSnapshot: approval?.snapshot ? normalizeApprovalSnapshot(approval.snapshot) : null,
      mediaRefs,
      tokenBoundaryRef: connectedChannel?.tokenBoundaryRef || {},
      name: displayName,
      status,
      nativeCreative: {
        ...base.nativeCreative,
        hook: currentVersion.caption || base.nativeCreative.hook,
        caption: currentVersion.body || base.nativeCreative.caption,
        cover: currentVersion.caption || base.nativeCreative.cover,
        cta: currentVersion.cta || base.nativeCreative.cta,
      },
      role: connectedChannel?.displayName || base.role,
      format: `${displayName} draft v${currentVersion.versionNumber || 1}`,
      publishingMode: `Backend-backed ${displayName} workflow`,
      scheduleSlot: connectedChannel?.status || "Connected channel pending",
      assets: mediaRefs.length
        ? mediaRefs.map((media) => `${media.kind || "media"}: ${media.storageRef}`)
        : base.assets,
      trackingEvents: base.trackingEvents,
      ownerAction: approval?.snapshot
        ? "Approved snapshot is frozen for publishing"
        : "Review backend draft version and approve exact payload",
      riskNote: "Provider credentials stay behind the server token boundary.",
      checklist: [
        {
          text: `Draft version v${currentVersion.versionNumber || 1} selected`,
          done: Boolean(currentVersion.id),
        },
        {
          text: `${mediaRefs.length || 0} server media ref${mediaRefs.length === 1 ? "" : "s"} attached`,
          done: mediaRefs.length > 0,
        },
        {
          text: approval?.snapshot ? "Backend approval snapshot frozen" : "Exact approval pending",
          done: Boolean(approval?.snapshot),
        },
      ],
    },
    index,
    workflowCampaignInput(workflow),
  );
};

const loadStoredIndex = (key, fallback = 0) => {
  try {
    const value = Number.parseInt(readPreference(key, ""), 10);
    return Number.isFinite(value) && value >= 0 ? value : fallback;
  } catch {
    return fallback;
  }
};

const clampIndex = (index, collection) => Math.min(Math.max(index, 0), Math.max(collection.length - 1, 0));

const loadStoredModule = () => {
  try {
    return moduleFromSlug(readPreference("localpilot-demo-active-module")) || "Home";
  } catch {
    return "Home";
  }
};

function Brand() {
  return (
    <span className="brand-lockup">
      <span className="brand-mark">LP</span>
      <span>
        LocalPilot <strong>AI</strong>
      </span>
    </span>
  );
}

export function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [pilotOpen, setPilotOpen] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [toast, setToast] = useState("");
  const navigate = useNavigate();

  const showToast = (message) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  };

  const submitPilot = (event) => {
    event.preventDefault();
    event.currentTarget.reset();
    setPilotOpen(false);
    showToast("Thanks. Your pilot request is ready for this prototype.");
  };

  const submitLogin = (event) => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget).entries());
    writePreference(
      "localpilot-demo-session",
      JSON.stringify({ ...data, loggedInAt: new Date().toISOString() }),
    );
    navigate("/app");
  };

  return (
    <div className="marketing-page">
      <header className={`site-header ${menuOpen ? "menu-open" : ""}`}>
        <a className="brand" href="#top" aria-label="LocalPilot AI home">
          <Brand />
        </a>
        <nav className="nav-links" aria-label="Primary navigation">
          <a href="#product">Product</a>
          <a href="#solutions">Solutions</a>
          <a href="#roi">Local ROI</a>
          <a href="#pricing">Pricing</a>
        </nav>
        <div className="header-actions">
          <LanguageToggle />
          <button className="text-button" type="button" onClick={() => setLoginOpen(true)}>
            Log in
          </button>
          <button className="primary-button small" type="button" onClick={() => setPilotOpen(true)}>
            Join the pilot
          </button>
        </div>
        <button
          className="menu-button"
          type="button"
          aria-label="Toggle navigation"
          onClick={() => setMenuOpen((value) => !value)}
        >
          <span />
          <span />
        </button>
      </header>

      <main id="top">
        <section className="hero section-shell">
          <div className="hero-copy">
            <p className="eyebrow">AI marketing operator for local businesses</p>
            <h1>
              Your local business marketing team, <span className="accent">powered by AI.</span>
            </h1>
            <p className="hero-subtitle">
              Upload a video or promotion and get a week of platform-native content for TikTok,
              Instagram, Facebook, and Xiaohongshu.
            </p>
            <div className="cta-row">
              <button className="primary-button" type="button" onClick={() => setPilotOpen(true)}>
                Join the pilot
              </button>
              <a className="secondary-button" href="#workflow">
                Watch workflow
              </a>
            </div>
            <div className="rating-row" aria-label="Customer rating">
              <span className="stars" aria-hidden="true">
                ★★★★★
              </span>
              <span>4.9/5 from 120+ local business owners</span>
            </div>
            <div className="trust-row">
              <span>No credit card required</span>
              <span>Cancel anytime</span>
            </div>
          </div>

          <div className="hero-visual" id="product">
            <img className="hero-photo" src={cafeOwner} alt="Local cafe owner reviewing marketing on a tablet" />
            <div className="workspace-card">
              <aside className="workspace-sidebar" aria-label="Product sidebar preview">
                <div className="mini-brand">
                  <span className="brand-mark small-mark">LP</span>
                  <span>LocalPilot AI</span>
                </div>
                {["Overview", "Campaigns", "Calendar", "Content", "Analytics", "Trend-to-Action", "Competitors"].map(
                  (item, index) => (
                    <button className={`side-item ${index === 0 ? "active" : ""}`} type="button" key={item}>
                      {item}
                    </button>
                  ),
                )}
              </aside>
              <div className="workspace-main">
                <div className="workspace-top">
                  <div>
                    <p className="crumb">Businesses / Sunny Side Bistro</p>
                    <h2>Sunny Side Bistro</h2>
                  </div>
                  <div className="approval-pill">AI set</div>
                </div>
                <div className="summary-grid">
                  <article className="summary-card input-card">
                    <img src={restaurant} alt="Restaurant lunch special" />
                    <div>
                      <span>Input</span>
                      <strong>Weekend lunch special video</strong>
                      <small>Uploaded May 16, 2026 - 10:42 AM</small>
                    </div>
                  </article>
                  <article className="summary-card">
                    <span>Campaign</span>
                    <strong>May 19 - May 25, 2026</strong>
                    <small>4 platforms - 16 pieces of content</small>
                    <Link className="ghost-button" to="/app">
                      View app demo
                    </Link>
                  </article>
                </div>
                <div className="platform-grid">
                  {platforms.map(([name, type, copy, image]) => (
                    <article className="platform-card" key={name}>
                      <div className="platform-head">
                        <span>{name}</span>
                        <strong>{type}</strong>
                      </div>
                      <img src={image} alt={`${name} campaign preview`} />
                      <p>{copy}</p>
                      <span className="approved">Approved</span>
                    </article>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="dashboard section-shell" id="workflow">
          <div className="calendar-panel">
            <div className="panel-heading">
              <h2>Campaign calendar</h2>
              <span>May 19 - May 25, 2026</span>
            </div>
            <div className="calendar-grid" aria-label="Weekly campaign calendar">
              {["TikTok Hook", "Reel", "Behind Scenes", "Local Post", "Menu Highlight", "Story", "Event Post"].map(
                (item, index) => (
                  <div className={`calendar-day ${index % 3 === 1 ? "soft" : ""} ${index % 3 === 2 ? "blue" : ""}`} key={item}>
                    <span>{["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][index]}</span>
                    <strong>{item}</strong>
                    <small>{index % 2 ? "12:00 PM" : "6:00 PM"}</small>
                  </div>
                ),
              )}
            </div>
            <div className="insight-row">
              <div>
                <span className="insight-label">Trend-to-Action</span>
                <strong>Hot now: "crispy chicken sandwich"</strong>
                <p>Mentions are up 126% in your area.</p>
              </div>
              <button className="secondary-button compact" type="button" onClick={() => setLoginOpen(true)}>
                Create content idea
              </button>
            </div>
          </div>
          <div className="roi-panel">
            <div className="panel-heading">
              <h2>Local ROI</h2>
              <a href="#roi">View full report</a>
            </div>
            <div className="metric-grid">
              {[
                ["Calls", "28", "+40%"],
                ["Bookings", "17", "+55%"],
                ["DMs", "34", "+31%"],
                ["Coupon Scans", "52", "+63%"],
                ["Saves", "91", "+25%"],
                ["Map Clicks", "76", "+38%"],
              ].map(([label, value, change]) => (
                <div className="metric-card" key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>{change}</small>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="workflow-strip section-shell">
          <div>
            <h2>
              Upload once.
              <br />
              Grow all week.
            </h2>
            <p>
              LocalPilot AI turns one video, menu item, service, or promotion into platform-native
              content that gets noticed and drives action.
            </p>
          </div>
          <ol className="steps">
            {["Upload", "AI creates", "Schedule", "You grow"].map((step, index) => (
              <li key={step}>
                <span>{index + 1}</span>
                <strong>{step}</strong>
                <p>{["Upload a video or share your promotion.", "AI creates native content for every channel.", "We schedule a week that fits your business.", "Track local results that matter."][index]}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="section-shell" id="solutions">
          <div className="section-heading">
            <h2>Built for restaurants, salons, clinics, and shops.</h2>
            <p>Start with proven playbooks for local businesses where every booking, visit, and call matters.</p>
          </div>
          <div className="industry-grid">
            {[
              ["Restaurants", "Fill tables and turn specials into loyal regulars.", restaurant],
              ["Salons", "Show off your work and keep chairs booked.", salon],
              ["Clinics", "Build trust and grow appointment demand.", clinic],
              ["Shops", "Highlight products and drive foot traffic.", shop],
            ].map(([title, copy, image]) => (
              <article className="industry-card" key={title}>
                <img src={image} alt={`${title} visual`} />
                <div>
                  <strong>{title}</strong>
                  <p>{copy}</p>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="roi-section section-shell" id="roi">
          <div className="roi-copy">
            <p className="eyebrow">Local ROI, not vanity metrics</p>
            <h2>Know what marketing actually brings customers.</h2>
            <p>
              We track calls, bookings, DMs, coupon scans, saves, and map clicks so owners can see
              what is working and keep growing.
            </p>
          </div>
          <div className="roi-features">
            {["Calls", "Bookings", "DMs", "Coupon scans", "Saves", "Map clicks"].map((item) => (
              <article key={item}>
                <strong>{item}</strong>
                <p>Track customer intent and revenue signals inside the same workflow.</p>
              </article>
            ))}
          </div>
        </section>

        <section className="red-section section-shell">
          <div>
            <p className="eyebrow red">Xiaohongshu-native growth</p>
            <h2>Native strategy, not translation.</h2>
            <p>
              Create RED notes with Chinese copy, 种草 framing, search keywords, cover text,
              save-oriented structure, and KOC-ready briefs.
            </p>
          </div>
          <div className="red-card">
            <span className="red-badge">小红书</span>
            <h3>本地午餐推荐</h3>
            <p>关键词: 周末午餐, 本地探店, 适合朋友聚餐, 性价比</p>
            <div className="red-stats">
              <span>1,248 saves</span>
              <span>983 likes</span>
              <span>156 comments</span>
            </div>
          </div>
        </section>

        <section className="pricing section-shell" id="pricing">
          <div className="section-heading">
            <h2>Pilot plans</h2>
            <p>Simple plans for early customers. Built to prove local ROI fast.</p>
          </div>
          <div className="pricing-grid">
            {pricingPlans.map((plan) => (
              <article className={`price-card ${plan.popular ? "popular" : ""}`} key={plan.name}>
                {plan.popular && <div className="popular-ribbon">Most popular</div>}
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
                <strong>
                  {plan.price} <span>{plan.suffix}</span>
                </strong>
                <ul>
                  {plan.features.map((feature) => (
                    <li key={feature}>{feature}</li>
                  ))}
                </ul>
                <button className={`${plan.tone === "coral" ? "coral-button" : plan.tone === "blue" ? "blue-button" : "primary-button"}`} type="button" onClick={() => setPilotOpen(true)}>
                  {plan.cta}
                </button>
              </article>
            ))}
          </div>
        </section>
      </main>

      <footer className="site-footer section-shell">
        <a className="brand" href="#top">
          <Brand />
        </a>
        <p>AI marketing operator for local businesses.</p>
        <button className="primary-button small" type="button" onClick={() => setPilotOpen(true)}>
          Request demo
        </button>
      </footer>

      {pilotOpen && (
        <Modal title="Join the LocalPilot AI pilot" eyebrow="Pilot access" onClose={() => setPilotOpen(false)}>
          <form className="pilot-form" onSubmit={submitPilot}>
            <label>
              Name
              <input name="name" type="text" placeholder="Your name" required />
            </label>
            <label>
              Business name
              <input name="business" type="text" placeholder="Sunny Side Bistro" required />
            </label>
            <label>
              Email
              <input name="email" type="email" placeholder="you@business.com" required />
            </label>
            <label>
              Business type
              <select name="type">
                <option>Restaurant or cafe</option>
                <option>Salon or beauty</option>
                <option>Clinic or wellness</option>
                <option>Retail shop</option>
                <option>Other local service</option>
              </select>
            </label>
            <label className="full">
              Biggest marketing challenge
              <textarea name="challenge" rows="3" placeholder="What do you want LocalPilot AI to help with first?" />
            </label>
            <button className="primary-button full" type="submit">
              Request pilot invite
            </button>
          </form>
        </Modal>
      )}

      {loginOpen && (
        <Modal title="Log in to the LocalPilot AI app demo" eyebrow="Demo workspace" onClose={() => setLoginOpen(false)}>
          <p className="modal-copy">Use any name and email. This is a local prototype session with fake client and campaign data.</p>
          <form className="pilot-form" onSubmit={submitLogin}>
            <label>
              Name
              <input name="name" type="text" placeholder="Alex Morgan" required />
            </label>
            <label>
              Work email
              <input name="email" type="email" placeholder="alex@agency.com" required />
            </label>
            <label className="full">
              Workspace
              <select name="workspace">
                <option>Northstar Local Growth</option>
                <option>Brightside Agency Demo</option>
                <option>LocalPilot Customer Preview</option>
              </select>
            </label>
            <button className="primary-button full" type="submit">
              Enter app demo
            </button>
          </form>
        </Modal>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

function Modal({ eyebrow, title, children, onClose }) {
  return (
    <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && onClose()}>
      <section className="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">
        <button className="modal-close" type="button" aria-label="Close modal" onClick={onClose}>
          Close
        </button>
        <p className="eyebrow">{eyebrow}</p>
        <h2 id="modal-title">{title}</h2>
        {children}
      </section>
    </div>
  );
}

export function AppDemo() {
  const navigate = useNavigate();
  const location = useLocation();
  const session = useMemo(() => {
    try {
      return JSON.parse(readPreference("localpilot-demo-session", "null"));
    } catch {
      return null;
    }
  }, []);
  const initialModule = useMemo(() => {
    const queryModule = moduleFromSlug(new URLSearchParams(location.search).get("module"));
    return queryModule || loadStoredModule();
  }, [location.search]);
  const [activeModule, setActiveModule] = useState(initialModule);
  const [selectedPost, setSelectedPost] = useState(() => loadStoredIndex("localpilot-demo-selected-post"));
  const [selectedChannel, setSelectedChannel] = useState(() => loadStoredIndex("localpilot-demo-selected-channel"));
  const [selectedInbox, setSelectedInbox] = useState(() => loadStoredIndex("localpilot-demo-selected-inbox"));
  const [selectedWalkthrough, setSelectedWalkthrough] = useState(() =>
    loadStoredIndex("localpilot-demo-selected-walkthrough"),
  );
  const [workflow, setWorkflow] = useState(() => normalizeWorkflow());
  const [workflowStatus, setWorkflowStatus] = useState("loading");
  const [workflowError, setWorkflowError] = useState("");
  const [approvalPending, setApprovalPending] = useState("");
  const [publishPending, setPublishPending] = useState("");
  const [queuedPublishJobs, setQueuedPublishJobs] = useState({});
  const [aiResponse, setAiResponse] = useState(
    "I will create platform-native posts, reserve Xiaohongshu for searchable recommendations, and track calls, DMs, coupon scans, bookings, and map clicks.",
  );
  const [appToast, setAppToast] = useState("");
  const campaignInput = workflowCampaignInput(workflow);
  const publishJobsByApprovalId = useMemo(() => {
    const jobs = {};
    workflow.publishJobs.forEach((job) => {
      if (job.approvalId) {
        jobs[job.approvalId] = job;
      }
    });
    return { ...jobs, ...queuedPublishJobs };
  }, [queuedPublishJobs, workflow.publishJobs]);
  const plans = useMemo(
    () =>
      workflow.platformDrafts.map((draft, index) => {
        const plan = workflowDraftToPlan(draft, index, workflow);
        return {
          ...plan,
          publishJob: plan.approvalId ? publishJobsByApprovalId[plan.approvalId] || null : null,
        };
      }),
    [publishJobsByApprovalId, workflow],
  );
  const safeSelectedChannel = clampIndex(selectedChannel, plans);
  const safeSelectedPost = clampIndex(selectedPost, plans);
  const safeSelectedInbox = clampIndex(selectedInbox, inboxThreads);
  const config = moduleDetails[activeModule] || moduleDetails.Home;
  const channel = plans[safeSelectedChannel];
  const selectedPlan = plans[safeSelectedPost];
  const pendingPlans = plans.filter((plan) => plan.status !== "Approved");
  const approvedCount = plans.length - pendingPlans.length;
  const checklistDone = plans.reduce((total, plan) => total + plan.checklist.filter((item) => item.done).length, 0);
  const checklistTotal = plans.reduce((total, plan) => total + plan.checklist.length, 0);
  const checklistPercent = checklistTotal ? Math.round((checklistDone / checklistTotal) * 100) : 0;
  const approvalPercent = plans.length ? Math.round((approvedCount / plans.length) * 100) : 0;
  const packageReadiness = Math.round((approvalPercent + checklistPercent) / 2);
  const topbarPrimaryAction =
    activeModule === "Calendar"
      ? { label: "Approve exact draft", handler: () => approvePlan(safeSelectedPost) }
      : { label: "Create with AI", handler: () => selectModule("AI Studio") };
  const topbarSecondaryAction =
    activeModule === "Calendar"
      ? { label: "Save package", handler: () => exportPackage() }
      : { label: "Review calendar", handler: () => selectModule("Calendar") };
  const workspaceMetrics =
    activeModule === "Calendar"
      ? [
          ["Pending approvals", String(pendingPlans.length), "Need a decision before publishing"],
          ["Selected slot", selectedPlan?.name || "—", selectedPlan?.scheduleSlot || "Choose a slot"],
          ["Package readiness", `${packageReadiness}%`, `${approvedCount}/${plans.length || 0} approved`],
          ["Local ROI", "6 events", "Calls, bookings, DMs, saves, map clicks"],
        ]
      : [
          ["Business input", "1", campaignInput.offer],
          ["Native outputs", String(plans.length), plans.length ? "Facebook and TikTok backend drafts" : "Loading workflow"],
          ["Local ROI intent", "6", "Calls, bookings, DMs, scans, saves, maps"],
          ["Package ready", `${packageReadiness}%`, `${pendingPlans.length} channels pending`],
        ];

  const reloadWorkflow = async ({ silent = false } = {}) => {
    if (!silent) {
      setWorkflowStatus("loading");
    }
    setWorkflowError("");
    try {
      const nextWorkflow = normalizeWorkflow(await loadPublishingWorkflow());
      setWorkflow(nextWorkflow);
      setWorkflowStatus("ready");
    } catch (error) {
      setWorkflowStatus("error");
      setWorkflowError(error instanceof Error ? error.message : "Publishing status could not load.");
    }
  };

  useEffect(() => {
    reloadWorkflow();
  }, []);

  useEffect(() => {
    const queryModule = moduleFromSlug(new URLSearchParams(location.search).get("module"));
    if (queryModule && queryModule !== activeModule) {
      setActiveModule(queryModule);
    }
  }, [activeModule, location.search]);

  useEffect(() => {
    writePreference("localpilot-demo-active-module", moduleSlug(activeModule));
  }, [activeModule]);

  useEffect(() => {
    writePreference("localpilot-demo-selected-channel", String(safeSelectedChannel));
  }, [safeSelectedChannel]);

  useEffect(() => {
    writePreference("localpilot-demo-selected-post", String(safeSelectedPost));
  }, [safeSelectedPost]);

  useEffect(() => {
    writePreference("localpilot-demo-selected-inbox", String(safeSelectedInbox));
  }, [safeSelectedInbox]);

  useEffect(() => {
    writePreference("localpilot-demo-selected-walkthrough", String(selectedWalkthrough));
  }, [selectedWalkthrough]);

  const showAppToast = (message) => {
    setAppToast(message);
    window.setTimeout(() => setAppToast(""), 2200);
  };

  const logout = () => {
    writePreference("localpilot-demo-session", null);
    navigate("/");
  };

  const selectModule = (module) => {
    setActiveModule(module);
    navigate(`/app?module=${moduleSlug(module)}`, { replace: true });
  };

  const applyWalkthroughStep = (step, index) => {
    setSelectedWalkthrough(index);
    if (Number.isInteger(step.channel)) {
      setSelectedChannel(step.channel);
    }
    if (Number.isInteger(step.post)) {
      setSelectedPost(step.post);
    }
    if (Number.isInteger(step.inbox)) {
      setSelectedInbox(step.inbox);
    }
    selectModule(step.module);
    showAppToast(`Walkthrough: ${step.title}`);
  };

  const resetDemo = async () => {
    const confirmed = window.confirm(
      "Reset demo workspace: This clears local demo preferences and reloads seeded backend records. Published audit records stay unchanged.",
    );
    if (!confirmed) {
      return;
    }

    clearDemoWorkspacePreferences();
    selectModule("Home");
    setSelectedPost(0);
    setSelectedChannel(0);
    setSelectedInbox(0);
    setSelectedWalkthrough(0);
    setQueuedPublishJobs({});
    await reloadWorkflow();
    setAiResponse(
      "I will create platform-native posts, reserve Xiaohongshu for searchable recommendations, and track calls, DMs, coupon scans, bookings, and map clicks.",
    );
    showAppToast("Local demo preferences cleared. Backend workflow reloaded from seeded records.");
  };

  const approvePlan = async (index) => {
    const plan = plans[index];
    if (!plan?.id || !plan.currentVersion?.id) {
      showAppToast("Publishing status could not load. Reload the workflow and try again.");
      return;
    }
    if (plan.status === "Approved") {
      showAppToast(`${plan.name} draft v${plan.currentVersion.versionNumber} is already approved.`);
      return;
    }

    const confirmed = window.confirm(
      `Approve ${plan.name} draft v${plan.currentVersion.versionNumber}? LocalPilot will freeze this exact payload for publishing. Later edits will create a new version.`,
    );
    if (!confirmed) {
      return;
    }

    setApprovalPending(plan.id);
    try {
      await approveDraftVersion(plan.id, {
        draftVersionId: plan.currentVersion.id,
        confirmation: "APPROVE_EXACT_VERSION",
        approver: {
          name: session?.name || "Karen Li",
          email: session?.email || "karen@example.com",
        },
        mediaRefs: plan.mediaRefs.map((media) => media.mediaAssetId),
      });
      await reloadWorkflow({ silent: true });
      showAppToast(`${plan.name} draft v${plan.currentVersion.versionNumber} approved.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Approval failed.");
    } finally {
      setApprovalPending("");
    }
  };

  const queuePublishJob = async (index) => {
    const plan = plans[index];
    if (!plan?.approvalId || !plan.approvalSnapshot?.draftVersionId) {
      showAppToast("Approve this exact draft before starting a fake publish job.");
      return;
    }
    if (plan.publishJob?.id) {
      showAppToast(`${plan.name} fake publish timeline is already loaded.`);
      return;
    }

    setPublishPending(plan.id);
    try {
      const queued = await queueFakePublish(plan.approvalId);
      const queuedJob = normalizePublishJob(queued?.job);
      const loaded = queuedJob.id ? await loadPublishJob(queuedJob.id) : null;
      const nextJob = normalizePublishJob(loaded?.job || queuedJob);
      if (nextJob.approvalId) {
        setQueuedPublishJobs((currentJobs) => ({
          ...currentJobs,
          [nextJob.approvalId]: nextJob,
        }));
      }
      await reloadWorkflow({ silent: true });
      showAppToast(`${plan.name} fake publish timeline loaded.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Fake publish queue failed.");
    } finally {
      setPublishPending("");
    }
  };

  const acceptRetriedJob = async (job, platform = "Publish job") => {
    const nextJob = normalizePublishJob(job);
    if (nextJob.approvalId) {
      setQueuedPublishJobs((currentJobs) => ({
        ...currentJobs,
        [nextJob.approvalId]: nextJob,
      }));
    }
    await reloadWorkflow({ silent: true });
    showAppToast(`${platform} retry accepted. Attempt history updated.`);
  };

  const requestChanges = (index) => {
    const plan = plans[index];
    showAppToast(`${plan?.name || "Draft"} remains in backend review until a new version is created.`);
  };

  const toggleChecklist = (planIndex, itemIndex) => {
    const plan = plans[planIndex];
    const item = plan?.checklist[itemIndex];
    showAppToast(item?.done ? "Backend checklist item is already satisfied." : "Backend workflow controls this item.");
  };

  const regeneratePlan = (event) => {
    event.preventDefault();
    setSelectedChannel(0);
    reloadWorkflow();
    showAppToast("Workflow reloaded from backend draft records.");
  };

  const exportPackage = () => {
    showAppToast("Backend-backed workflow package is ready for assisted review.");
  };

  const applyBusinessType = (businessType) => {
    const template = businessTemplates[businessType] || businessTemplates.restaurant;
    setSelectedChannel(0);
    showAppToast(`${template.label} selection noted. Backend workflow records remain the source of truth.`);
  };

  const submitPrompt = (event) => {
    event.preventDefault();
    const prompt = new FormData(event.currentTarget).get("prompt")?.trim();
    setAiResponse(
      prompt
        ? `Drafted a local campaign from "${prompt}". I added platform-specific captions, a Xiaohongshu angle, approval notes, and ROI events to track.`
        : "Drafted a local campaign with platform-specific captions, approval notes, and ROI events to track.",
    );
    event.currentTarget.reset();
    showAppToast("AI Studio generated a demo response.");
  };

  const runAiTask = (task) => {
    setAiResponse(
      `${task} completed for ${campaignInput.business}. I updated channel copy, approval notes, and local ROI tracking in the demo plan.`,
    );
    showAppToast(`${task} completed.`);
  };

  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label="App navigation">
        <Link className="app-brand" to="/">
          <Brand />
        </Link>
        <div className="workspace-switcher">
          <span>Workspace</span>
          <strong>{session?.workspace || "Northstar Local Growth"}</strong>
          <small>8 client locations</small>
        </div>
        <nav className="app-nav" aria-label="Demo sections">
          {modules.map((module) => (
            <button
              className={`app-nav-item ${activeModule === module ? "active" : ""}`}
              type="button"
              key={module}
              onClick={() => selectModule(module)}
            >
              {module}
            </button>
          ))}
        </nav>
        <div className="sidebar-card">
          <span>LocalPilot edge</span>
          <strong>Xiaohongshu + local ROI</strong>
          <p>Native RED content, booking signals, calls, map clicks, and guided posting in one workflow.</p>
        </div>
      </aside>

      <main className="app-main">
        <header className="app-topbar">
          <div>
            <p className="app-kicker">Agency demo workspace</p>
            <h1>{config.title}</h1>
            {config.summary && <p className="topbar-summary">{config.summary}</p>}
          </div>
          <div className="topbar-actions">
            <LanguageToggle compact />
            <select
              aria-label="Selected client"
              value={campaignInput.businessType}
              onChange={(event) => applyBusinessType(event.target.value)}
            >
              {businessOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.business}
                </option>
              ))}
            </select>
            <button className="primary-action" type="button" onClick={topbarPrimaryAction.handler}>
              {topbarPrimaryAction.label}
            </button>
            <button className="secondary-action" type="button" onClick={topbarSecondaryAction.handler}>
              {topbarSecondaryAction.label}
            </button>
            <button className="secondary-action" type="button" onClick={resetDemo}>
              Reset demo
            </button>
            <button className="icon-action" type="button" onClick={logout}>
              Log out
            </button>
          </div>
        </header>

        <section className="hero-metrics" aria-label="Workspace summary">
          {workspaceMetrics.map(([label, value, note]) => (
            <article key={label}>
              <span>{label}</span>
              <strong>{value}</strong>
              <small>{note}</small>
            </article>
          ))}
        </section>

        <section className="app-grid">
          <section className="primary-panel" aria-label="Primary demo panel">
            <div className="panel-head">
              <div>
                <p className="app-kicker">{config.kicker}</p>
                <h2>{config.title}</h2>
              </div>
              {config.view === "calendar" && (
                <div className="segmented-control" aria-label="Calendar view">
                  <button className="active" type="button">
                    Week
                  </button>
                  <button type="button">Grid</button>
                  <button type="button">List</button>
                </div>
              )}
            </div>

            {config.view === "workbench" && (
              <div className="growth-workbench">
                <section className="strategy-brief">
                  <div>
                    <span>Input</span>
                    <strong>{campaignInput.offer}</strong>
                    <p>
                      Goal: {campaignInput.goal} for {campaignInput.business} within a {campaignInput.audience}.
                    </p>
                  </div>
                  <div>
                    <span>AI strategy</span>
                    <strong>Turn one offer into channel-specific customer actions.</strong>
                    <p>
                      TikTok earns attention, Instagram captures DMs, Facebook builds local trust,
                      Xiaohongshu creates searchable Chinese discovery, and Google Local captures high-intent visits.
                    </p>
                  </div>
                </section>

                <form className="campaign-builder" onSubmit={regeneratePlan}>
                  <label>
                    Type
                    <select
                      value={campaignInput.businessType}
                      onChange={(event) => applyBusinessType(event.target.value)}
                    >
                      {businessOptions.map((option) => (
                        <option value={option.value} key={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Offer
                    <input value={campaignInput.offer} readOnly />
                  </label>
                  <label>
                    Goal
                    <input value={campaignInput.goal} readOnly />
                  </label>
                  <label>
                    Audience
                    <input value={campaignInput.audience} readOnly />
                  </label>
                  <button className="primary-action" type="submit">
                    Regenerate weekly plan
                  </button>
                </form>

                <div className="channel-tabs" role="tablist" aria-label="Channel plans">
                  {plans.map((plan, index) => (
                    <button
                      className={safeSelectedChannel === index ? "active" : ""}
                      type="button"
                      role="tab"
                      aria-selected={safeSelectedChannel === index}
                      key={plan.name}
                      onClick={() => setSelectedChannel(index)}
                    >
                      <span>{plan.name}</span>
                      <small>{plan.kpi}</small>
                      <em>{plan.status}</em>
                    </button>
                  ))}
                </div>

                {!channel && (
                  <section className="workflow-state-panel">
                    <span>{workflowStatus === "error" ? "Workflow error" : "Loading workflow"}</span>
                    <h3>{workflowStatus === "error" ? "Publishing status could not load." : "Loading backend records."}</h3>
                    <p>
                      {workflowError ||
                        "LocalPilot is loading campaign, draft, media, channel, and approval records from the backend."}
                    </p>
                    <button className="secondary-action" type="button" onClick={() => reloadWorkflow()}>
                      Reload workflow
                    </button>
                  </section>
                )}

                {channel && (
                  <section className={`channel-breakdown ${channel.tone}`}>
                    <div className="channel-preview">
                      <img src={channel.asset} alt={`${channel.name} generated campaign preview`} />
                      <div className="phone-frame">
                        <span>{channel.name}</span>
                        <strong>{channel.nativeCreative.cover}</strong>
                        <p>{channel.nativeCreative.hook}</p>
                        <small>{channel.nativeCreative.cta}</small>
                      </div>
                    </div>

                    <div className="channel-detail">
                      <div className="channel-heading">
                        <div>
                          <span>{channel.format}</span>
                          <h3>{channel.name}: {channel.role}</h3>
                        </div>
                        <button
                          className="primary-action"
                          type="button"
                          disabled={approvalPending === channel.id || channel.status === "Approved"}
                          onClick={() => approvePlan(safeSelectedChannel)}
                        >
                          Approve exact draft
                        </button>
                        {channel.approvalSnapshot?.draftVersionId && !channel.publishJob?.id && (
                          <button
                            className="secondary-action"
                            type="button"
                            disabled={publishPending === channel.id}
                            onClick={() => queuePublishJob(safeSelectedChannel)}
                          >
                            Queue fake publish
                          </button>
                        )}
                        <button className="secondary-action" type="button" onClick={() => requestChanges(safeSelectedChannel)}>
                          Request changes
                        </button>
                        {publishPending === channel.id && <small className="inline-pending">Queueing fake publish...</small>}
                        {approvalPending === channel.id && <small className="inline-pending">Freezing snapshot...</small>}
                      </div>

                    <dl className="creative-spec">
                      <div>
                        <dt>Post angle</dt>
                        <dd>{channel.postAngle}</dd>
                      </div>
                      <div>
                        <dt>Hook</dt>
                        <dd>{channel.nativeCreative.hook}</dd>
                      </div>
                      <div>
                        <dt>Caption</dt>
                        <dd>{channel.nativeCreative.caption}</dd>
                      </div>
                      <div>
                        <dt>CTA</dt>
                        <dd>{channel.nativeCreative.cta}</dd>
                      </div>
                      <div>
                        <dt>KPI</dt>
                        <dd>{channel.kpi}</dd>
                      </div>
                    </dl>

                    <div className="delivery-meta-grid">
                      <article>
                        <span>Publishing mode</span>
                        <strong>{channel.publishingMode}</strong>
                        <small>{channel.scheduleSlot}</small>
                      </article>
                      <article>
                        <span>Assets included</span>
                        <ul>
                          {channel.assets.map((asset) => (
                            <li key={asset}>{asset}</li>
                          ))}
                        </ul>
                      </article>
                      <article>
                        <span>Tracking events</span>
                        <ul>
                          {channel.trackingEvents.map((eventName) => (
                            <li key={eventName}>{eventName}</li>
                          ))}
                        </ul>
                      </article>
                    </div>

                    <div className="why-row">
                      <article>
                        <span>Why this should work</span>
                        <p>{channel.whyItWorks}</p>
                      </article>
                      <article>
                        <span>Owner action and risk check</span>
                        <p>{channel.ownerAction}</p>
                        <small>{channel.riskNote}</small>
                      </article>
                    </div>

                    <ul className="publish-checklist">
                      {channel.checklist.map((item, itemIndex) => (
                        <li key={item.text}>
                          <button
                            className={item.done ? "done" : ""}
                            type="button"
                            onClick={() => toggleChecklist(safeSelectedChannel, itemIndex)}
                          >
                            {item.text}
                          </button>
                        </li>
                      ))}
                    </ul>
                      <ApprovalSnapshot snapshot={channel.approvalSnapshot} />
                    </div>
                  </section>
                )}

                <section className="publish-timeline-grid" aria-label="Per-platform fake publish timelines">
                  {plans.map((plan, index) => (
                    <div className="publish-timeline-stack" key={`${plan.id || plan.name}-timeline`}>
                      <PublishTimeline
                        fallbackStatus={planLifecycleStatus(plan)}
                        job={plan.publishJob}
                        platform={plan.name}
                      />
                      {safeSelectedChannel === index && canRetryPublishJob(plan.publishJob) && (
                        <RetryPublishControl
                          job={plan.publishJob}
                          platform={plan.name}
                          onRetryAccepted={(nextJob) => acceptRetriedJob(nextJob, plan.name)}
                        />
                      )}
                    </div>
                  ))}
                </section>

                <div className="feature-spotlight" aria-label="LocalPilot standout features">
                  {localpilotDifferentiators.map(({ title, proof }) => (
                    <article key={title}>
                      <strong>{title}</strong>
                      <p>{proof}</p>
                    </article>
                  ))}
                </div>

                <section className="delivery-package" aria-label="Ready-to-deliver campaign package">
                  <div className="package-summary">
                    <div>
                      <span>Delivery package</span>
                      <h3>{packageReadiness}% ready for owner review</h3>
                      <p>
                        {approvedCount}/{plans.length} channels approved and {checklistDone}/{checklistTotal} owner tasks complete.
                      </p>
                    </div>
                    <button className="primary-action" type="button" onClick={exportPackage}>
                      Save package
                    </button>
                  </div>
                  <div className="package-columns">
                    <article>
                      <span>What the customer gets</span>
                      <ul>
                        <li>Backend-owned Facebook and TikTok drafts with captions and CTAs.</li>
                        <li>Server media refs, connected channel refs, and publishing mode.</li>
                        <li>Approval status and frozen snapshots returned by the workflow API.</li>
                      </ul>
                    </article>
                    <article>
                      <span>Local ROI handoff</span>
                      <ul>
                        <li>Calls and map clicks attached to Google Local and Facebook.</li>
                        <li>DM keyword tracking attached to Instagram.</li>
                        <li>Saves and profile visits attached to Xiaohongshu.</li>
                      </ul>
                    </article>
                    <article>
                      <span>Competitor watcher</span>
                      <ul>
                        <li>Nearby owner-led offers are outperforming menu-only posts.</li>
                        <li>Price anchoring and short owner intros are the strongest patterns.</li>
                        <li>Next action: request a 10-second owner intro before final export.</li>
                      </ul>
                    </article>
                  </div>
                </section>
              </div>
            )}

            {config.view === "calendar" && (
              <div className="calendar-workbench">
                <section className="calendar-intro">
                  <div>
                    <p className="app-kicker">This week</p>
                    <h2>Approve the posts that are ready to go live</h2>
                    <p>
                      Pick a slot, inspect the angle, and approve or request edits. The calendar should
                      help the owner decide what happens next, not show every possible thing at once.
                    </p>
                  </div>
                  <div className="calendar-intro-chip">
                    <span>Current focus</span>
                    <strong>{pendingPlans.length} approvals pending</strong>
                    <small>{packageReadiness}% package readiness</small>
                  </div>
                </section>

                <div className="calendar-board">
                  {plans.map((plan, index) => (
                    <button
                      className={`schedule-card ${plan.tone} ${safeSelectedPost === index ? "active" : ""}`}
                      type="button"
                      key={plan.name}
                      onClick={() => setSelectedPost(index)}
                    >
                      <span>{plan.scheduleSlot}</span>
                      <strong>{plan.name}</strong>
                      <small>{plan.nativeCreative.cover}</small>
                      <em>{plan.status}</em>
                    </button>
                  ))}
                </div>

                {selectedPlan ? (
                  <article className="selected-post selected-post--calendar">
                    <div className="selected-post-copy">
                      <span className="status-pill">{selectedPlan.status}</span>
                      <h3>
                        {selectedPlan.name}: {selectedPlan.publishingMode}
                      </h3>
                      <p>{selectedPlan.nativeCreative.caption}</p>
                      <div className="calendar-actions">
                        <button
                          type="button"
                          disabled={approvalPending === selectedPlan.id || selectedPlan.status === "Approved"}
                          onClick={() => approvePlan(safeSelectedPost)}
                        >
                          Approve exact draft
                        </button>
                        {selectedPlan.approvalSnapshot?.draftVersionId && !selectedPlan.publishJob?.id && (
                          <button
                            type="button"
                            disabled={publishPending === selectedPlan.id}
                            onClick={() => queuePublishJob(safeSelectedPost)}
                          >
                            Queue fake publish
                          </button>
                        )}
                        <button type="button" onClick={() => requestChanges(safeSelectedPost)}>
                          Request edit
                        </button>
                      </div>
                      <div className="selected-checklist">
                        <span>Before publishing</span>
                        <ul>
                          {selectedPlan.checklist.map((item) => (
                            <li key={item.text} className={item.done ? "done" : ""}>
                              {item.text}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <ApprovalSnapshot snapshot={selectedPlan.approvalSnapshot} />
                      <PublishTimeline
                        fallbackStatus={planLifecycleStatus(selectedPlan)}
                        job={selectedPlan.publishJob}
                        platform={selectedPlan.name}
                      />
                      {canRetryPublishJob(selectedPlan.publishJob) && (
                        <RetryPublishControl
                          job={selectedPlan.publishJob}
                          platform={selectedPlan.name}
                          onRetryAccepted={(nextJob) => acceptRetriedJob(nextJob, selectedPlan.name)}
                        />
                      )}
                    </div>
                    <img src={selectedPlan.asset} alt="Selected campaign preview" />
                  </article>
                ) : (
                  <section className="workflow-state-panel">
                    <span>{workflowStatus === "error" ? "Workflow error" : "Loading workflow"}</span>
                    <h3>{workflowStatus === "error" ? "Publishing status could not load." : "Loading backend records."}</h3>
                    <p>
                      {workflowError ||
                        "LocalPilot is loading campaign, draft, media, channel, and approval records from the backend."}
                    </p>
                    <button className="secondary-action" type="button" onClick={() => reloadWorkflow()}>
                      Reload workflow
                    </button>
                  </section>
                )}
              </div>
            )}

            {config.view === "ai" && (
              <div className="ai-studio">
                <section className="ai-command-grid">
                  {aiStudioTasks.map(([action, title, body]) => (
                    <button type="button" key={title} onClick={() => runAiTask(title)}>
                      <span>{action}</span>
                      <strong>{title}</strong>
                      <small>{body}</small>
                    </button>
                  ))}
                </section>
                <div className="ai-thread">
                  <article>
                    <span>AI Studio</span>
                    <p>
                      Build a week of posts for {campaignInput.business} using the offer "{campaignInput.offer}".
                      Make each channel native and track local business outcomes.
                    </p>
                  </article>
                  <article className="ai-answer">
                    <span>LocalPilot AI</span>
                    <p>{aiResponse}</p>
                  </article>
                </div>
                <div className="ai-output-list">
                  {plans.map((plan) => (
                    <article key={`${plan.name}-ai`}>
                      <span>{plan.name}</span>
                      <strong>{plan.nativeCreative.hook}</strong>
                      <p>{plan.nativeCreative.caption}</p>
                    </article>
                  ))}
                </div>
                <form className="ai-prompt" onSubmit={submitPrompt}>
                  <input name="prompt" type="text" placeholder="Ask AI Studio to create, refine, analyze, or schedule..." />
                  <button className="primary-action" type="submit">
                    Generate
                  </button>
                </form>
              </div>
            )}

            {config.view === "month" && (
              <div className="month-grid" aria-label="Calendar overview">
                {plans.map((plan) => (
                  <div key={`${plan.name}-month`}>
                    <span>{plan.scheduleSlot}</span>
                    <strong>{plan.name}</strong>
                    <small>{plan.publishingMode}</small>
                  </div>
                ))}
              </div>
            )}

            {config.view === "inbox" && (
              <div className="inbox-workspace">
                <div className="inbox-list">
                  {inboxThreads.map((thread, index) => (
                    <article className={safeSelectedInbox === index ? "active" : ""} key={thread.source}>
                      <button type="button" onClick={() => setSelectedInbox(index)}>
                        <span>{thread.source}</span>
                        <strong>{thread.customer}</strong>
                        <small>{thread.intent}</small>
                      </button>
                    </article>
                  ))}
                </div>
                <section className="inbox-detail">
                  <span>{inboxThreads[safeSelectedInbox].source}</span>
                  <h3>{inboxThreads[safeSelectedInbox].intent}</h3>
                  <p>{inboxThreads[safeSelectedInbox].message}</p>
                  <div>
                    <strong>Suggested reply</strong>
                    <p>{inboxThreads[safeSelectedInbox].draft}</p>
                  </div>
                  <button type="button" onClick={() => showAppToast(`${inboxThreads[safeSelectedInbox].action} saved.`)}>
                    {inboxThreads[safeSelectedInbox].action}
                  </button>
                </section>
              </div>
            )}

            {config.view === "analytics" && (
              <div className="analytics-workspace">
                <section className="roi-signal-grid">
                  {localRoiSignals.map(([value, label, body]) => (
                    <article key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                      <p>{body}</p>
                    </article>
                  ))}
                </section>
                <section className="roi-explain-panel">
                  <div>
                    <span>Best signal</span>
                    <h3>Owner-led content is creating higher local intent.</h3>
                    <p>
                      LocalPilot connects the content plan to business actions: calls from Facebook and Google,
                      DMs from Instagram, saves from Xiaohongshu, and coupon scans from TikTok.
                    </p>
                  </div>
                  <div className="analytics-channel-list">
                    {plans.map((plan) => (
                      <article key={`${plan.name}-roi`}>
                        <strong>{plan.name}</strong>
                        <span>{plan.kpi}</span>
                        <button type="button" onClick={() => showAppToast(`${plan.name} ROI note added to report.`)}>
                          Add note
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
              </div>
            )}

            {!config.view && (
              <div className="module-workflow">
                <section className="module-brief">
                  <div>
                    <span>{moduleWorkflows[activeModule]?.focus || config.title}</span>
                    <h3>{config.title}</h3>
                    <p>{moduleWorkflows[activeModule]?.summary || "This module uses fake demo data for customer review."}</p>
                  </div>
                  <button className="primary-action" type="button" onClick={() => showAppToast(`${activeModule} demo action saved.`)}>
                    Run demo action
                  </button>
                </section>

                <div className="module-cards">
                  {config.cards.map(([title, body]) => (
                    <article className="module-card" key={title}>
                      <span>Capability</span>
                      <strong>{title}</strong>
                      <p>{body}</p>
                    </article>
                  ))}
                </div>

                <div className="module-steps" aria-label={`${activeModule} workflow`}>
                  {(moduleWorkflows[activeModule]?.steps || []).map(([status, title, action]) => (
                    <article key={`${status}-${title}`}>
                      <span>{status}</span>
                      <strong>{title}</strong>
                      <p>{action}</p>
                      <button type="button" onClick={() => showAppToast(`${title} marked in ${activeModule}.`)}>
                        Mark
                      </button>
                    </article>
                  ))}
                </div>
              </div>
            )}
          </section>

          <aside className="insights-panel" aria-label="Insights and approvals">
            <section className="insight-card readiness-card">
              <div className="panel-head compact-head">
                <h2>Package readiness</h2>
                <span>{packageReadiness}%</span>
              </div>
              <div className="readiness-meter" aria-label={`Package readiness ${packageReadiness}%`}>
                <i style={{ width: `${packageReadiness}%` }} />
              </div>
              <p>
                {approvedCount}/{plans.length} channels approved. Complete checklist items, then save the assisted publishing package.
              </p>
            </section>
            <section className="insight-card">
              <div className="panel-head compact-head">
                <h2>What needs attention</h2>
                <span>{pendingPlans.length} items</span>
              </div>
              <ul className="recommendation-list">
                {pendingPlans.slice(0, 3).map((plan) => (
                  <li key={plan.name}>
                    {plan.name} is still pending. Review the {plan.kpi.toLowerCase()} angle before publishing.
                  </li>
                ))}
              </ul>
            </section>
            <section className="insight-card">
              <div className="panel-head compact-head">
                <h2>Approval queue</h2>
                <span>{pendingPlans.length} pending</span>
              </div>
              <div className="approval-list">
                {plans.map((plan, index) =>
                  plan.status === "Approved" ? null : (
                    <article key={plan.name}>
                      <strong>{plan.name} plan</strong>
                      <small>{plan.status} · KPI: {plan.kpi}</small>
                      <button
                        type="button"
                        disabled={approvalPending === plan.id}
                        onClick={() => approvePlan(index)}
                      >
                        Approve exact draft
                      </button>
                    </article>
                  ),
                )}
                {pendingPlans.length === 0 && (
                  <article>
                    <strong>All channels approved</strong>
                    <small>Ready to save the posting package</small>
                    <button type="button" onClick={exportPackage}>
                      Save
                    </button>
                  </article>
                )}
              </div>
            </section>
            <section className="insight-card roi-card">
              <h2>Local ROI loop</h2>
              <div className="mini-metrics">
                {[
                  ["28", "calls"],
                  ["17", "bookings"],
                  ["34", "DMs"],
                  ["76", "map clicks"],
                ].map(([value, label]) => (
                  <span key={label}>
                    <strong>{value}</strong> {label}
                  </span>
                ))}
              </div>
            </section>
          </aside>
        </section>
      </main>
      {appToast && <div className="app-toast">{appToast}</div>}
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <TranslationLayer />
      <AppRoutes />
    </LanguageProvider>
  );
}

createRoot(document.getElementById("root")).render(<App />);
