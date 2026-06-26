import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Link, useLocation, useNavigate } from "react-router-dom";
import "./styles.css";
import {
  applyPhase3IdeaVariant,
  approveDraftVersion,
  createPhase3ApprovalFeedback,
  createPhase3AiAssistantReply,
  createPhase3BulkVariations,
  createPhase3CompetitorSource,
  createPhase3ContentBatch,
  createPhase3ContentBatchFromReply,
  createPhase3ContentSource,
  createPhase3CreatorStyleVideoWorkflow,
  createPhase3IdeaVariants,
  createPhase3LanguageVariants,
  createPhase3MediaVariant,
  createPhase3ReviewNotification,
  createPhase3TemplateImport,
  createPhase3UgcVoiceoverPackage,
  crawlWebsite,
  devLogin,
  generatePhase3CreatorStyleVideo,
  googleLogin,
  confirmOnboardingProfile,
  loadAuthCapabilities,
  loadFacebookConnection,
  loadOnboardingProfile,
  loadPhase3Workspace,
  loadPublishJob,
  loadPublishingWorkflow,
  loadSession,
  logout as logoutSession,
  publishFacebookPost,
  queueFakePublish,
  recordPhase3ProofEvent,
  renderPhase3MediaAsset,
  updateOnboardingProfile,
  updatePhase3BrandKit,
  updatePhase3CalendarSlot,
  updatePhase3Creative,
  updatePhase3MediaAsset,
  updatePhase3MediaLayerLayout,
} from "./api/publishingClient.js";
import { ApprovalSnapshot } from "./components/ApprovalSnapshot.jsx";
import { PublishTimeline } from "./components/PublishTimeline.jsx";
import { RetryPublishControl } from "./components/RetryPublishControl.jsx";
import {
  RETRYABLE_PUBLISH_STATUSES,
  normalizeApprovalSnapshot,
  normalizePublishJob,
  normalizeWorkflow,
} from "./models/publishing.js";
import {
  loadGenerationCredits,
  loadGenerationJobs,
  loadGenerationModels,
  launchGenerationJob,
  retryGenerationJob,
} from "./api/generationClient.js";
import {
  normalizeCreditSummary,
  normalizeGenerationCatalog,
  normalizeGenerationJob,
  normalizeGenerationJobsList,
} from "./models/generation.js";
import { AppRoutes } from "./routes/AppRoutes.jsx";
import { clearDemoWorkspacePreferences, readPreference, writePreference } from "./storage/preferences.js";

import cafeOwner from "../assets/cafe-owner.png";
import clinic from "../assets/clinic.png";
import restaurant from "../assets/restaurant.png";
import salon from "../assets/salon.png";
import shop from "../assets/shop.png";

const LANGUAGE_STORAGE_KEY = "localpilot-language";
const referencePreviewImages = [cafeOwner, restaurant, salon, clinic, shop];
const referencePreviewStyle = (image) => (image ? { "--reference-preview-image": `url(${image})` } : undefined);
const creatorAvatarPreviewImages = [cafeOwner, salon, salon, cafeOwner, salon, cafeOwner, salon, cafeOwner, salon, salon, cafeOwner, salon];
const creatorAvatarPreviewPositions = [
  "72% 34%",
  "24% 34%",
  "74% 38%",
  "66% 38%",
  "26% 30%",
  "70% 42%",
  "78% 34%",
  "62% 32%",
  "18% 36%",
  "70% 30%",
  "58% 40%",
  "82% 36%",
];
const creatorAvatarPreviewScales = ["1", "1", "-1", "1", "-1", "1", "1", "-1", "1", "-1", "1", "1"];
const MINIMAX_CAROUSEL_MODEL_ID = "genmodel_minimax_carousel_primary";
const CAROUSEL_PRESET_ID = "carousel_canonical_v1";
const CAROUSEL_ROLE_ORDER = ["cover", "problem", "proof", "offer", "cta"];

const creatorAvatarPreviewStyle = (index) => ({
  "--reference-preview-image": `url(${creatorAvatarPreviewImages[index % creatorAvatarPreviewImages.length]})`,
  "--reference-preview-position": creatorAvatarPreviewPositions[index % creatorAvatarPreviewPositions.length],
  "--reference-preview-scale-x": creatorAvatarPreviewScales[index % creatorAvatarPreviewScales.length],
});

const onboardingVoiceoverOptions = [
  ["Warm owner voice", "Warm owner voice"],
  ["Clear service narrator", "Clear service narrator"],
];

const onboardingAvatarOptions = [
  ["Owner-style avatar", "Owner-style avatar"],
  ["Service expert avatar", "Service expert avatar"],
];

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
  "Create New",
  "Auto Posting",
  "Ad Inspirations",
  "Content Library",
  "Content Calendar",
  "AI Studio",
  "Brand & Social Accounts",
  "Competitor Analysis",
  "Analytics",
  "Need help",
];

const moduleIcons = {
  "Create New": "+",
  "Auto Posting": "➤",
  "Ad Inspirations": "◐",
  "Content Library": "▰",
  "Content Calendar": "▦",
  "AI Studio": "◈",
  "Brand & Social Accounts": "▣",
  "Competitor Analysis": "▥",
  Analytics: "▤",
  "Need help": "?",
};

const moduleSlug = (module) => module.toLowerCase().replace(/[^a-z0-9]+/g, "-");

const moduleAliases = {
  home: "Content Library",
  dashboard: "Content Library",
  "brand-kit": "Brand & Social Accounts",
  "brand-and-social-accounts": "Brand & Social Accounts",
  "ai-generator": "Create New",
  "ai-studio": "AI Studio",
  "generation": "AI Studio",
  "creative-editor": "Content Library",
  "content-library": "Content Library",
  publish: "Content Library",
  calendar: "Content Calendar",
  "content-calendar": "Content Calendar",
  analytics: "Analytics",
  "proof-loop": "Analytics",
  discover: "Competitor Analysis",
  "competitor-ideas": "Competitor Analysis",
  "competitor-analysis": "Competitor Analysis",
  approvals: "Content Library",
  "approval-queue": "Content Library",
  settings: "Brand & Social Accounts",
  "connected-accounts": "Brand & Social Accounts",
  "need-help": "Need help",
  help: "Need help",
};

const moduleFromSlug = (slug) => {
  const normalized = String(slug || "").toLowerCase();
  const normalizedSlug = moduleSlug(normalized);
  return (
    modules.find((module) => moduleSlug(module) === normalizedSlug || module.toLowerCase() === normalized) ||
    moduleAliases[normalized] ||
    moduleAliases[normalizedSlug]
  );
};

const moduleDetails = {
  "Create New": {
    kicker: "Create your next post",
    title: "Create Your Next Post",
    view: "create",
  },
  "Auto Posting": {
    kicker: "Owner-approved autoplan",
    title: "Weekly local autoplan after approval",
    summary: "Schedule a week of content without autonomous publishing.",
    view: "autopost",
  },
  "Ad Inspirations": {
    kicker: "Inspirations",
    title: "Inspirations",
    view: "inspirations",
  },
  "Content Library": {
    kicker: "Library",
    title: "Content Library",
    view: "library",
  },
  "Content Calendar": {
    kicker: "Scheduler",
    title: "Content Calendar",
    summary: "Pick the next slot, review the copy, and keep the week moving.",
    view: "calendar",
  },
  "AI Studio": {
    kicker: "Generation workspace",
    title: "AI Studio",
    summary: "Choose a model, see the cost, and launch work you can actually track.",
    view: "generation",
  },
  "Approval Queue": {
    kicker: "Owner approval",
    title: "Review and sign-off",
    view: "approvals",
  },
  "Brand & Social Accounts": {
    kicker: "Brand and social accounts",
    title: "Brand & Social Accounts",
    view: "accounts",
  },
  "Competitor Analysis": {
    kicker: "Idea labs",
    title: "Competitor analysis",
    view: "ideas",
  },
  Analytics: {
    kicker: "Measurable response",
    title: "Analytics",
    view: "analytics",
  },
  "Need help": {
    kicker: "Support",
    title: "Need help?",
    view: "help",
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

const createFormatCards = [
  {
    id: "image",
    title: "Image",
    format: "Static post",
    summary: "A branded square or portrait social image for offers, tips, and proof snippets.",
    preview: restaurant,
  },
  {
    id: "ugc",
    title: "Creator Style Video",
    format: "AI actor UGC",
    summary: "Predis-style UGC idea, tone, actor, scene, generate, publish, and schedule flow.",
    preview: cafeOwner,
  },
  {
    id: "short-ad-video",
    title: "Short Ad Video",
    format: "15 second vertical",
    summary: "A short-video concept for Facebook Reels, TikTok assisted packages, or Stories.",
    preview: salon,
  },
  {
    id: "carousel",
    title: "Carousel",
    format: "Multi-slide explainer",
    summary: "A style preset, aspect ratio, and brand confirmation before generation.",
    preview: shop,
  },
  {
    id: "faceless-video",
    title: "Faceless Video",
    format: "Narrated service clip",
    summary: "A script-first video with no owner filming requirement for busy local teams.",
    preview: clinic,
  },
  {
    id: "product-photo-shoot",
    title: "Product Photo Shoot",
    format: "Product/service image set",
    summary: "Turn a product, storefront, or job-site photo into branded content variants.",
    preview: restaurant,
  },
];

const createMethods = [
  ["write-idea", "Write Your Idea", "Describe the offer, service, product, or community angle."],
  ["store-csv", "Link store/upload CSV", "Use website, store, menu, catalog, or CSV details as source context."],
  ["product-url", "Enter Product URL", "Analyze a product/service page into a local social brief."],
  ["product-image", "Upload product image", "Start from a product, job-site, or before/after photo."],
];

const carouselStylePresets = [
  ["storytelling", "Storytelling", "Problem, local context, fix, proof, CTA."],
  ["promotional", "Promotional", "Offer-first carousel with deadline and owner approval."],
  ["motivational", "Motivational", "Helpful reminder with local seasonal urgency."],
  ["exploratory", "Exploratory", "Educational carousel that explains options without hard claims."],
];

const aspectRatioOptions = ["1:1", "9:16", "4:5", "2:3"];
const inspirationFilterChips = [
  "All",
  "< 8 sec",
  ">= 8 sec",
  "Beauty",
  "Fashion",
  "Health and Wellness",
  "Home and Living",
  "Food and Beverage",
  "Consumer Electronic",
];

const inspirationSections = [
  {
    title: "Trending collection",
    tone: "trending",
    viewAllLabel: "View all trending collection",
    categories: inspirationFilterChips,
    items: [
      {
        title: "Compact service hook",
        badge: "7s",
        format: "9:16",
        prompt: "Create a fast local service hook with a visual product reveal and owner-safe CTA.",
        preview: shop,
      },
      {
        title: "Beauty testimonial prompt",
        badge: "8s",
        format: "9:16",
        prompt: "Turn a testimonial-style beauty clip into a local proof post with approval language.",
        preview: salon,
      },
      {
        title: "Health expert explainer",
        badge: "9s",
        format: "9:16",
        prompt: "Create a short expert-style explainer that stays compliant and avoids medical claims.",
        preview: clinic,
      },
      {
        title: "Home service reveal",
        badge: "7s",
        format: "9:16",
        prompt: "Create a home service reveal with a simple before/after structure and local CTA.",
        preview: restaurant,
      },
      {
        title: "Founder product walk-up",
        badge: "16s",
        format: "9:16",
        prompt: "Create a founder-led product walk-up for a small business promotion.",
        preview: cafeOwner,
      },
      {
        title: "Consumer electronic demo",
        badge: "9s",
        format: "9:16",
        prompt: "Create a consumer electronic demo with clear benefit framing and no fake claims.",
        preview: shop,
      },
    ],
  },
  {
    title: "UGC Ads",
    tone: "ugc",
    viewAllLabel: "View all ugc ads",
    categories: inspirationFilterChips,
    items: [
      {
        title: "Owner explains the seasonal problem",
        badge: "18s",
        format: "UGC video",
        prompt: "Turn an owner explainer into a same-week appointment post with a proof-safe CTA.",
        preview: cafeOwner,
      },
      {
        title: "Customer myth vs local reality",
        badge: "9:16",
        format: "Voiceover",
        prompt: "Create a myth-busting local service video with an owner approval step.",
        preview: salon,
      },
      {
        title: "Before the next weather swing",
        badge: "15s",
        format: "Reel/TikTok",
        prompt: "Create a short vertical video for urgent but claim-safe seasonal service demand.",
        preview: clinic,
      },
      {
        title: "Technician shows one quick fix",
        badge: "23s",
        format: "How-to",
        prompt: "Create a practical service explainer that earns trust without overpromising results.",
        preview: shop,
      },
      {
        title: "Owner asks a customer question",
        badge: "19s",
        format: "Interview",
        prompt: "Turn a common customer question into a founder-led short video with a safe CTA.",
        preview: restaurant,
      },
      {
        title: "Day-in-the-life service visit",
        badge: "27s",
        format: "Behind scenes",
        prompt: "Create a behind-the-scenes local trust clip with an owner review checkpoint.",
        preview: cafeOwner,
      },
    ],
  },
  {
    title: "Image Ads",
    tone: "image",
    viewAllLabel: "View all image ads",
    categories: ["All", "Beauty", "Health and Wellness", "Food and Beverage", "Fashion", "Pet Care and Pet Products", "Fitness", "Real Estate", "Travel"],
    items: [
      {
        title: "Local checklist card",
        badge: "1:1",
        format: "Image",
        prompt: "Create a checklist-style Facebook image post for homeowners comparing service options.",
        preview: shop,
      },
      {
        title: "Proof-backed offer",
        badge: "4:5",
        format: "Image",
        prompt: "Create an offer card that mentions observable proof signals but avoids exact ROI claims.",
        preview: restaurant,
      },
      {
        title: "Neighborhood service map",
        badge: "2:3",
        format: "Carousel",
        prompt: "Create a local service-area carousel with map-click and call-tap proof hooks.",
        preview: cafeOwner,
      },
      {
        title: "Seasonal reminder card",
        badge: "1:1",
        format: "Image",
        prompt: "Create a seasonal reminder image that drives calls without using fake urgency.",
        preview: clinic,
      },
      {
        title: "Review-safe proof card",
        badge: "4:5",
        format: "Image",
        prompt: "Create a review-inspired proof card that stays inside approved claims.",
        preview: salon,
      },
      {
        title: "Owner tip carousel",
        badge: "1:1",
        format: "Carousel",
        prompt: "Create a short educational carousel with owner voice and a local service CTA.",
        preview: shop,
      },
    ],
  },
];

const contentTypeFilters = ["All", "Image", "Video", "Carousel"];
const libraryCreatedFromOptions = ["All sources", "AI Generator", "Inspirations", "Source URL", "Image upload"];
const publishPlatformOptions = ["Facebook", "Facebook Reel", "TikTok", "Google Business Profile", "Assisted Package"];
const publishPostTypeOptions = ["Feed post", "Reel/Short", "Carousel", "Assisted handoff"];
const calendarViews = ["Weekly", "Monthly"];
const calendarLegend = ["Published", "Scheduled", "Failed", "Rejected", "In Review"];
const calendarWeekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

const brandAccountTabs = ["Social Platforms", "Brand Details", "Integrations", "Exports"];
const brandDetailSections = ["Business identity", "Style", "Content settings"];

const socialPlatformRows = [
  { provider: "Instagram", accountType: "Business or Creator accounts", icon: "◎", tone: "instagram", watch: true },
  { provider: "Facebook", accountType: "Page", icon: "f", tone: "facebook", watch: true },
  { provider: "Linkedin", accountType: "Page or Profile", icon: "in", tone: "linkedin", watch: true },
  { provider: "Google Business Profile", accountType: "Profile", icon: "G", tone: "google", watch: false },
  { provider: "TikTok", accountType: "Profile", icon: "♪", tone: "tiktok", watch: false },
  { provider: "Pinterest", accountType: "Boards", icon: "P", tone: "pinterest", watch: false },
  { provider: "Twitter", accountType: "Profile", icon: "𝕏", tone: "twitter", watch: true },
  { provider: "Youtube", accountType: "Channel", icon: "▶", tone: "youtube", watch: false },
];

const socialPlatformFaqs = {
  Instagram: [
    "I am trying to Link Instagram but a Facebook Popup Opens up?",
    "I don't have a Facebook page. How can I link Instagram?",
    "I can't see my Instagram Account inside the Facebook Popup.",
    "I have an Instagram creator account. Will it work?",
    "After I link, the loader keeps spinning. What can I do?",
  ],
  TikTok: ["Will my video get published automatically to TikTok?"],
  Facebook: [
    "Which Page permissions does LocalPilot request?",
    "Can I choose a different Page after connecting?",
    "Will LocalPilot publish without owner approval?",
  ],
};

const defaultSocialFaqs = [
  "What permissions are required to connect this account?",
  "Can I schedule posts after this account is connected?",
  "Will LocalPilot publish automatically?",
];

const socialConnectionChoices = {
  Instagram: [
    {
      title: "Professional",
      subtitle: "(via Facebook)",
      badge: "HARD",
      badgeTone: "hard",
      icon: "◎",
      companion: "f",
    },
    {
      title: "Professional",
      subtitle: "(via Instagram)",
      badge: "EASY",
      badgeTone: "easy",
      note: "NEW",
      icon: "◎",
    },
  ],
  TikTok: [
    {
      title: "Profile",
      subtitle: "(via TikTok OAuth)",
      badge: "EASY",
      badgeTone: "easy",
      icon: "♪",
    },
  ],
};

const integrationTrustCards = [
  {
    icon: "✽",
    title: "Used by over 20,000+",
    detail: "Shopify / Woocommerce store owners",
  },
  {
    icon: "★",
    title: "Rated 4.8",
    detail: "by over 3000 businesses",
  },
  {
    icon: "✓",
    title: "Verified by",
    detail: "Shopify, WooCommerce and SquareSpace",
  },
];

const ecommerceConnectors = [
  { name: "Shopify", icon: "S", tone: "shopify" },
  { name: "Wix", icon: "WIX", tone: "wix" },
  { name: "Squarespace", icon: "SQ", tone: "squarespace" },
  { name: "WooComm...", icon: "W", tone: "woocommerce" },
];

const brandExportRows = [
  {
    id: "founder-ugc-export",
    title: "Create a UGC video for an on-camera founder exp...",
    dimension: "Portrait (720×1264)",
    status: "Processing complete",
    preview: cafeOwner,
  },
  {
    id: "mini-split-export",
    title: "Midea 9,000 BTU Mini Split AC/Heating System",
    dimension: "Portrait (720×1264)",
    status: "Processing complete",
    preview: shop,
  },
];

const analyticsEmptyStates = [
  ["Posting activity", "No live provider feed yet", "Connect official accounts to ingest post activity."],
  ["Post engagement", "Waiting for published posts", "Comments, saves, shares, and reactions will appear here."],
  ["Follower growth", "Early-state account", "Growth charts unlock after provider analytics ingestion."],
];

const analyticsAccountTabs = [
  { label: "Instagram", icon: "◎", active: false },
  { label: "Aurora Heating & Cooling", icon: "f", active: true },
  { label: "LinkedIn", icon: "in", active: false },
];

const analyticsMetricCards = [
  { label: "New posts", value: "2", dateRange: "21 May - 21 Jun", icon: "◒", tone: "blue" },
  { label: "Followers", value: "0", dateRange: "21 May - 21 Jun", icon: "●●", tone: "green" },
  { label: "Engagement", value: "0", dateRange: "21 May - 21 Jun", icon: "♥", tone: "orange" },
];

const analyticsChartDates = ["21 May", "26 May", "30 May", "04 Jun", "09 Jun", "13 Jun", "18 Jun"];

const helpActions = [
  ["Get help", "Open a non-sending support checklist for setup questions."],
  ["Send a message", "Draft a message locally; nothing is sent until the owner confirms."],
  ["FAQs", "Explain OAuth, assisted channels, proof hooks, and owner approval."],
  ["Brand Elements", "Show where logos, fonts, colors, and approved phrases live."],
  ["Service status", "Demo status only; production status page comes later."],
  ["Chat support", "Placeholder for field-sales walkthrough support."],
  ["Book demo", "Local callback CTA for sales follow-up."],
];

const schedule = [
  ["Mon 9:00", "TikTok hook", "Lunch special trend angle", "Approved", "green"],
  ["Tue 12:30", "Instagram Reel", "Visual story + offer CTA", "Needs review", "coral"],
  ["Wed 6:00", "Facebook post", "Community update", "Scheduled", "blue"],
  ["Thu 8:00", "Xiaohongshu note", "Searchable Chinese content", "Draft", "red"],
  ["Fri 10:00", "Story reminder", "Coupon scan push", "Ready", "green"],
];

const aiStudioTasks = [
  ["Generate", "Weekly post batch", "Create posts, carousels, and reels from one local offer."],
  ["Brand", "Apply brand kit", "Use local voice, colors, approved phrases, and audience rules."],
  ["Schedule", "Fill calendar", "Place the week across Facebook, Instagram, TikTok, and Google."],
  ["Measure", "Attach proof hooks", "Add QR, short link, call tap, DM keyword, and coupon events."],
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

const brandKitCards = [
  ["Business", "Aurora Heating & Cooling", "Home services in Washtenaw County, MI"],
  ["Tone", "Trusted, prompt, local", "Helpful expert, never pushy or generic"],
  ["Colors", "Deep navy, service blue, warm amber", "Applied to cards, carousels, and proof reports"],
  ["Approved words", "same-week, local team, honest recommendations", "Used by the generator before every draft"],
  ["Avoid", "guaranteed savings, miracle fixes, scare tactics", "Risk guardrails before owner approval"],
  ["Examples", "5 past posts + 3 customer reviews", "Used as the brand voice calibration seed"],
];

const creativeFormats = [
  {
    format: "Static post",
    description: "Predis parity: generated branded post with caption, hashtags, CTA, and scheduling slot.",
  },
  {
    format: "Carousel",
    description: "Five-slide outline with cover, problem, proof, offer, and action slide.",
  },
  {
    format: "Reel / TikTok script",
    description: "Hook, shot list, voiceover, caption, disclosure note, and proof hook.",
  },
  {
    format: "Story reminder",
    description: "Short follow-up with DM keyword and coupon/QR action.",
  },
];

const competitorIdeas = [
  {
    source: "Nearby HVAC Page",
    theme: "Heat-wave readiness",
    hook: "Before the first 85 degree day, check this one thing.",
    timing: "Monday 7:30 AM",
    hashtags: "#annarborhomes #hvactips #michiganweather",
  },
  {
    source: "Local restaurant pattern",
    theme: "Owner-led specials",
    hook: "The owner explains why this week's special sells out early.",
    timing: "Wednesday 11:00 AM",
    hashtags: "#localbusiness #lunchspecial #mainstreet",
  },
  {
    source: "Predis parity demo",
    theme: "Best-performing format",
    hook: "Carousel checklist beats generic captions for service education.",
    timing: "Thursday 6:00 PM",
    hashtags: "#smallbusinessmarketing #localproof #servicebusiness",
  },
];

const proofEvents = [
  ["Short link clicks", "44", "People opened the post-specific offer link."],
  ["QR scans", "19", "In-store or printed assets were scanned."],
  ["Call taps", "28", "Mobile visitors tapped to call from Facebook or Google."],
  ["Direction taps", "31", "High-intent local visitors requested directions."],
  ["DM keywords", "17", "Instagram/TikTok replies used the tracked keyword."],
  ["Owner-confirmed mentions", "6", "The owner heard customers mention the post."],
];

const predisParityChannels = [
  ["Facebook", "Live OAuth adapter", "Approved Page posts can publish live when Meta credentials are configured."],
  ["TikTok", "Assisted short-video package", "Script, caption, disclosure, and upload-ready notes are generated."],
  ["Instagram", "Assisted Reel/carousel package", "DM keyword, carousel outline, and caption are ready for owner posting."],
  ["Google Business Profile", "Assisted local update", "Call and direction proof hooks are attached before publishing."],
  ["LinkedIn / X / Pinterest", "Parity placeholder", "Shown in the product map so the Predis-style surface is recognizable without diluting MVP adapters."],
];

const emptyPhase3Workspace = {
  brandKit: {},
  contentBatches: [],
  contentSources: [],
  aiAssistantReplies: [],
  generatedCreatives: [],
  calendarSlots: [],
  competitorSources: [],
  competitorIdeas: [],
  proofEvents: [],
  creativeTemplates: [],
  importedTemplates: [],
  approvalReviewLinks: [],
  approvalFeedback: [],
  reviewNotifications: [],
  assetLibraryItems: [],
  performanceSnapshots: [],
  analyticsInsights: [],
  creatorStyleWorkflows: [],
  creatorStyleOptions: {
    styles: [],
    actors: [],
    templates: [],
  },
  analyticsSummary: {},
};

const defaultCreatorStyleForm = {
  prompt:
    "Create an avatar video explaining how Aurora Heating & Cooling helps Southeast Michigan homeowners save money with energy-efficient Midea systems and expert rebate assistance. Authentic, friendly.",
  goal: "save money with energy-efficient HVAC systems",
  selectedIdeaId: "",
  styleId: "motivational",
  actorId: "",
  templateId: "",
  aspectRatio: "9:16",
};

const creatorAspectRatioOptions = ["9:16", "16:9"];

const creatorWorkflowSteps = [
  { id: "prompt", label: "Idea", title: "Create UGC Video", subtitle: "Describe the UGC Video you want to create." },
  { id: "idea", label: "Idea", title: "Select an idea", subtitle: "Choose the generated angle you want to turn into a creator-style video." },
  { id: "style", label: "Style", title: "Configure your UGC Video", subtitle: "Customize your UGC Video settings to match your brand style." },
  { id: "actor", label: "Avatar", title: "Choose your favorite avatar", subtitle: "Pick your favorite AI actor." },
  { id: "template", label: "Subtitle", title: "Pick Subtitle style", subtitle: "Choose how subtitles will show in the UGC Video." },
  { id: "review", label: "Review", title: "Review your script", subtitle: "This is what your creator will say. Edit via prompt below." },
  { id: "confirm", label: "Confirm", title: "Review and confirm your details", subtitle: "Make sure everything looks right before generating your UGC Video." },
  { id: "generated", label: "Publish", title: "Generated creative", subtitle: "Review the creative, media asset, UGC package, and calendar handoff." },
];

const creatorTemplatePreviewSamples = [
  { lead: "A PERSON WALKED", accent: "SLOWLY DOWN THE" },
  { lead: "A PERSON WALKED", accent: "PERSON WALKED" },
  { lead: "A PERSON WALKED", accent: "EMPTY STREET" },
  { lead: "A PERSON WALKED", accent: "SLOWLY DOWN THE" },
  { lead: "EMPTY STREET", accent: "PERSON WALKED" },
  { lead: "A PERSON WALKED", accent: "EMPTY STREET" },
  { lead: "A PERSON", accent: "WALKED SLOWLY" },
  { lead: "EMPTY", accent: "STREET" },
  { lead: "SLOWLY DOWN", accent: "THE STREET" },
  { lead: "A PERSON WALKED", accent: "EMPTY STREET" },
];

const fallbackCreatorActorChoices = [
  {
    id: "local-owner",
    name: "Local owner",
    persona: "approachable small-business owner",
    badge: "Owner voice",
  },
  {
    id: "field-expert",
    name: "Field expert",
    persona: "hands-on technician or service specialist",
    badge: "Expert",
  },
  {
    id: "community-guide",
    name: "Community guide",
    persona: "local neighbor recommending a practical next step",
    badge: "Community",
  },
  {
    id: "studio-host",
    name: "Studio host",
    persona: "polished host for premium product/service offers",
    badge: "Studio",
  },
  {
    id: "service-coach",
    name: "Service coach",
    persona: "calm explainer who helps customers choose the next step",
    badge: "Coach",
  },
  {
    id: "neighborhood-pro",
    name: "Neighborhood pro",
    persona: "local professional with neighborly credibility",
    badge: "Local pro",
  },
  {
    id: "front-desk-guide",
    name: "Front desk guide",
    persona: "helpful scheduler who makes booking feel easy",
    badge: "Scheduler",
  },
  {
    id: "premium-advisor",
    name: "Premium advisor",
    persona: "trust-first advisor for higher-value purchases",
    badge: "Advisor",
  },
  {
    id: "modern-founder",
    name: "Modern founder",
    persona: "design-aware founder explaining premium product decisions",
    badge: "Founder",
  },
  {
    id: "wellness-host",
    name: "Wellness host",
    persona: "friendly expert for beauty, wellness, and lifestyle offers",
    badge: "Host",
  },
  {
    id: "retail-specialist",
    name: "Retail specialist",
    persona: "in-store product explainer with confident but approachable tone",
    badge: "Retail",
  },
  {
    id: "service-mentor",
    name: "Service mentor",
    persona: "seasoned operator who explains what premium service really means",
    badge: "Mentor",
  },
];

const fallbackCreatorTemplateChoices = [
  {
    id: "hook-proof-cta",
    title: "Hook / proof / CTA",
    format: "9:16 creator video",
    summary: "Hook in 3 seconds, one proof moment, one direct CTA.",
  },
  {
    id: "problem-solution",
    title: "Problem / solution",
    format: "9:16 explainer",
    summary: "Show the pain, explain the fix, then invite a call or booking.",
  },
  {
    id: "offer-walkthrough",
    title: "Offer walkthrough",
    format: "9:16 short ad",
    summary: "A compact promo format for fancy product or premium service offers.",
  },
  {
    id: "subtitle-punch",
    title: "Subtitle punch",
    format: "9:16 caption-led video",
    summary: "Large kinetic subtitles, short beats, and a bold closing CTA.",
  },
  {
    id: "premium-comparison",
    title: "Premium comparison",
    format: "9:16 comparison explainer",
    summary: "Compare cheap vs premium choices without unsupported claims.",
  },
  {
    id: "owner-note",
    title: "Owner note",
    format: "9:16 founder-style clip",
    summary: "A founder-style recommendation that feels personal and approval-ready.",
  },
  {
    id: "caption-flash",
    title: "Caption flash",
    format: "9:16 fast-caption reel",
    summary: "Rapid subtitle beats with a quick product or service payoff.",
  },
  {
    id: "center-punch",
    title: "Center punch",
    format: "9:16 centered subtitle layout",
    summary: "Bold centered subtitles with a clean mid-frame actor layout.",
  },
  {
    id: "bottom-caption",
    title: "Bottom caption",
    format: "9:16 creator explainer",
    summary: "Traditional lower subtitle track with clean readability.",
  },
  {
    id: "quote-overlay",
    title: "Quote overlay",
    format: "9:16 testimonial style",
    summary: "Use quote-style subtitles to turn a recommendation into social proof.",
  },
  {
    id: "staggered-words",
    title: "Staggered words",
    format: "9:16 motion subtitle layout",
    summary: "Stagger words across rows for a more animated subtitle feel.",
  },
];

const creatorScriptDurationOptions = [
  { id: "8s", label: "$ Rewrite for 8s", estimate: "7.2 seconds" },
  { id: "16s", label: "$$ Rewrite for 16s", estimate: "15.6 seconds" },
  { id: "24s", label: "$$$ Rewrite for 24s", estimate: "23.8 seconds" },
];

const describeDisplayItem = (item) => {
  if (typeof item === "string") {
    return item;
  }
  if (typeof item === "number" || typeof item === "boolean") {
    return String(item);
  }
  if (!item || typeof item !== "object") {
    return "";
  }
  if (item.secondRange || item.shot || item.caption) {
    return [item.secondRange, item.shot || item.caption].filter(Boolean).join(": ");
  }
  if (item.title || item.label || item.name || item.text) {
    return item.title || item.label || item.name || item.text;
  }
  return Object.entries(item)
    .slice(0, 3)
    .map(([key, value]) => `${key}: ${describeDisplayItem(value) || "set"}`)
    .join(" · ");
};

const displayItemKey = (prefix, item, index) => `${prefix}-${index}-${describeDisplayItem(item) || "item"}`;

const textFromUnknown = (value, fallback = "") => {
  if (Array.isArray(value)) {
    return value
      .map((item) => textFromUnknown(item, ""))
      .filter(Boolean)
      .join(" ");
  }
  if (value === null || value === undefined) {
    return fallback;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (typeof value === "object") {
    return describeDisplayItem(value) || fallback;
  }
  return String(value);
};

const safeText = (value, fallback = "") => textFromUnknown(value, fallback);

const safeChecklistText = (value, fallback = "Pending") => safeText(value, fallback);

const stableNodeKey = (value, fallback = "item", index = 0) => {
  if (value === undefined || value === null || value === "") {
    return `${fallback}-${index}`;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return `${value}`;
  }
  if (typeof value === "object") {
    if (typeof value.id === "string" || typeof value.id === "number" || typeof value.id === "boolean") {
      return `${value.id}`;
    }
    return `${fallback}-${index}`;
  }
  return `${value}-${index}`;
};

const mediaAssetHighlights = (asset) => {
  const metadata = asset?.metadata || {};
  if (Array.isArray(metadata.scenes)) {
    return metadata.scenes.map(describeDisplayItem).filter(Boolean);
  }
  if (Array.isArray(metadata.slides)) {
    return metadata.slides.map(describeDisplayItem).filter(Boolean);
  }
  if (Array.isArray(metadata.placements)) {
    return metadata.placements.map(describeDisplayItem).filter(Boolean);
  }
  if (Array.isArray(metadata.editableLayers)) {
    return metadata.editableLayers.map((layer) => `Editable ${describeDisplayItem(layer).replace(/_/g, " ")}`);
  }
  return [];
};

const layerControlEditForAsset = (asset, control, creative) => {
  const layerId = control?.id || "layer";
  const title = safeText(creative?.title, "Same-week service opening");
  const caption = safeText(creative?.caption || asset?.prompt, "Local service reminder");
  const cta = safeText(creative?.cta, "Book now");
  if (layerId.includes("brand_color")) {
    return {
      value: "#f97316",
      placement: "brand system",
      style: "high_contrast_accent",
    };
  }
  if (layerId.includes("cta") || layerId.includes("phone")) {
    return {
      value: `${cta} · tracked proof link`,
      placement: "bottom safe zone",
      style: "primary_button",
    };
  }
  if (layerId.includes("headline") || layerId.includes("hook")) {
    return {
      value: `${title} this week`,
      placement: "top safe zone",
      style: "bold_hook",
    };
  }
  if (layerId.includes("caption") || layerId.includes("body") || layerId.includes("checklist")) {
    return {
      value: safeText(caption).slice(0, 120),
      placement: "middle content stack",
      style: "readable_body",
    };
  }
  if (layerId.includes("service") || layerId.includes("area")) {
    return {
      value: "Washtenaw County homeowners",
      placement: "local trust footer",
      style: "local_badge",
    };
  }
  return {
    value: `Owner-approved ${String(control?.label || layerId).toLowerCase()} edit`,
    placement: "canvas",
    style: "brand_safe",
  };
};

const formatCompactNumber = (value) => {
  const number = Number(value || 0);
  if (number >= 1000000) {
    return `${(number / 1000000).toFixed(1)}M`;
  }
  if (number >= 1000) {
    return `${(number / 1000).toFixed(1)}K`;
  }
  return String(number);
};

const formatCents = (value) => `$${Math.round(Number(value || 0) / 100).toLocaleString()}`;

const walkthroughSteps = [
  {
    title: "Start with Create New",
    module: "Create New",
    note: "Show format cards and source methods before generation.",
    channel: 0,
  },
  {
    title: "Review inspirations",
    module: "Ad Inspirations",
    note: "Recreate reference ideas as LocalPilot owner-approved campaigns.",
  },
  {
    title: "Open content library",
    module: "Content Library",
    note: "Show filters, cards, editor, publish gating, and approval controls.",
  },
  {
    title: "Review the calendar",
    module: "Content Calendar",
    note: "Approve or request edits from the scheduled post plan.",
    post: 1,
  },
  {
    title: "Check accounts",
    module: "Brand & Social Accounts",
    note: "Show brand details, social platforms, OAuth boundaries, and page picker.",
    post: 0,
  },
  {
    title: "Explain analytics",
    module: "Analytics",
    note: "Connect posts to lower-bound evidence, not exact offline ROI.",
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
    business: "Aurora Heating & Cooling",
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

const businessTypeAliases = {
  home_services: "hvac",
  hvac_service: "hvac",
};

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
  if (match?.value) {
    return match.value;
  }
  const normalizedName = String(businessName || "").toLowerCase();
  if (normalizedName.includes("hvac") || normalizedName.includes("heating") || normalizedName.includes("cooling")) {
    return "hvac";
  }
  return defaultCampaignInput.businessType;
};

const normalizeCampaignInput = (input = defaultCampaignInput) => {
  const aliasedType = businessTypeAliases[input?.businessType] || input?.businessType;
  const inferredType = aliasedType && businessTemplates[aliasedType]
    ? aliasedType
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
      typeof item === "string"
        ? { text: safeChecklistText(item, "Checklist item"), done: false }
        : { ...item, text: safeChecklistText(item?.text, "Checklist item"), done: false },
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
          typeof item === "string"
            ? { text: safeChecklistText(item, "Checklist item"), done: false }
            : { ...item, text: safeChecklistText(item?.text, "Checklist item"), done: Boolean(item.done) },
        )
      : base.checklist.map((item) =>
          typeof item === "string"
            ? { text: safeChecklistText(item, "Checklist item"), done: false }
            : { ...item, text: safeChecklistText(item?.text, "Checklist item"), done: Boolean(item.done) },
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
        hook: safeText(currentVersion?.caption, base.nativeCreative.hook),
        caption: safeText(currentVersion?.body, base.nativeCreative.caption),
        cover: safeText(currentVersion?.caption, base.nativeCreative.cover),
        cta: safeText(currentVersion?.cta, base.nativeCreative.cta),
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
    return moduleFromSlug(readPreference("localpilot-demo-active-module")) || "Content Library";
  } catch {
    return "Content Library";
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
  const [devLoginEnabled, setDevLoginEnabled] = useState(false);
  const [loginCapabilityLoading, setLoginCapabilityLoading] = useState(false);
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

  const [loginError, setLoginError] = useState("");

  const handleLoginSuccess = useCallback(() => {
    setLoginOpen(false);
    navigate("/app");
  }, [navigate]);

  const handleLoginError = useCallback((err) => {
    setLoginError(err?.message || "Login failed. Please try again.");
  }, []);

  const handleDevLogin = async () => {
    setLoginError("");
    try {
      await devLogin();
      handleLoginSuccess();
    } catch (err) {
      handleLoginError(err);
    }
  };

  useEffect(() => {
    if (!loginOpen || GOOGLE_CLIENT_ID) return undefined;

    let cancelled = false;
    setLoginError("");
    setDevLoginEnabled(false);
    setLoginCapabilityLoading(true);

    loadAuthCapabilities()
      .then((payload) => {
        if (!cancelled) {
          setDevLoginEnabled(Boolean(payload?.devLoginEnabled));
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setLoginError(err?.message || "Unable to load sign-in options.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoginCapabilityLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [loginOpen]);

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
        <Modal title="Log in to LocalPilot AI" eyebrow="Sign in" onClose={() => { setLoginOpen(false); setLoginError(""); }}>
          {loginError && <p className="modal-copy" style={{ color: "var(--red)" }}>{loginError}</p>}
          {GOOGLE_CLIENT_ID ? (
            <GoogleSignInButton onSuccess={handleLoginSuccess} onError={handleLoginError} />
          ) : loginCapabilityLoading ? (
            <p className="modal-copy">Checking sign-in options...</p>
          ) : devLoginEnabled ? (
            <>
              <p className="modal-copy">Development mode — backend dev login is enabled.</p>
              <button className="primary-button full" type="button" onClick={handleDevLogin}>
                Dev Login
              </button>
            </>
          ) : (
            <p className="modal-copy">Google sign-in is not configured in this environment.</p>
          )}
        </Modal>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function GoogleSignInButton({ onSuccess, onError }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const render = () => {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: async (response) => {
          try {
            await googleLogin(response.credential);
            onSuccess();
          } catch (err) {
            onError?.(err);
          }
        },
      });
      window.google.accounts.id.renderButton(containerRef.current, {
        theme: "outline",
        size: "large",
        text: "continue_with",
        shape: "rectangular",
        width: 320,
      });
    };

    if (window.google?.accounts?.id) {
      render();
      return;
    }

    const poll = setInterval(() => {
      if (window.google?.accounts?.id) {
        clearInterval(poll);
        render();
      }
    }, 150);
    return () => clearInterval(poll);
  }, [onSuccess, onError]);

  return <div ref={containerRef} style={{ display: "flex", justifyContent: "center", minHeight: 44 }} />;
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

const onboardingFieldRows = [
  [
    {
      key: "name",
      label: "Business name",
      type: "text",
      placeholder: "Business name",
    },
    {
      key: "industry",
      label: "Industry",
      type: "text",
      placeholder: "e.g. Restaurant, Salon, Retail",
    },
  ],
  [
    {
      key: "description",
      label: "Description",
      type: "textarea",
      placeholder: "Brief description (1-2 sentences)",
      fullWidth: true,
    },
  ],
  [
    {
      key: "logoUrl",
      label: "Logo URL",
      type: "url",
      placeholder: "https://example.com/logo.png",
    },
    {
      key: "fontFamily",
      label: "Font family",
      type: "text",
      placeholder: "e.g. Inter, Roboto",
    },
  ],
  [
    {
      key: "primaryColor",
      label: "Primary color",
      type: "color",
      placeholder: "#1f2937",
    },
    {
      key: "secondaryColor",
      label: "Secondary color",
      type: "color",
      placeholder: "#2563eb",
    },
  ],
  [
    {
      key: "accentColor",
      label: "Accent color",
      type: "color",
      placeholder: "#f97316",
    },
    {
      key: "language",
      label: "Language",
      type: "select",
      options: [
        ["en", "English"],
        ["zh", "Chinese"],
        ["es", "Spanish"],
      ],
    },
  ],
  [
    {
      key: "timezone",
      label: "Timezone",
      type: "text",
      placeholder: "e.g. America/Chicago",
    },
    {
      key: "tonality",
      label: "Tonality",
      type: "select",
      options: [
        ["formal", "Formal"],
        ["casual", "Casual"],
        ["playful", "Playful"],
        ["professional", "Professional"],
      ],
    },
  ],
  [
    {
      key: "voiceover",
      label: "Voiceover",
      type: "select",
      options: onboardingVoiceoverOptions,
      helpText: "Used in all voiceover videos.",
    },
    {
      key: "avatar",
      label: "Avatar",
      type: "select",
      options: onboardingAvatarOptions,
      helpText: "Used in UGC-style videos and avatar-led explainers.",
    },
  ],
  [
    {
      key: "targetAudience",
      label: "Target audience",
      type: "textarea",
      placeholder: "Describe your target customers",
      fullWidth: true,
    },
  ],
];

const defaultOnboardingProfile = {
  crawlUrl: "",
  name: "",
  description: "",
  industry: "",
  logoUrl: "",
  primaryColor: "#1f2937",
  secondaryColor: "#2563eb",
  accentColor: "#f97316",
  fontFamily: "",
  language: "en",
  timezone: "",
  tonality: "professional",
  voiceover: "Warm owner voice",
  avatar: "Owner-style avatar",
  targetAudience: "",
  status: "draft",
};

const normalizeOnboardingProfile = (profile) => ({
  ...defaultOnboardingProfile,
  ...(profile || {}),
  status: profile?.status || "draft",
});

const isValidOnboardingUrl = (value) => {
  try {
    const parsed = new URL(value);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
};

const normalizeColorInputValue = (value, fallback) =>
  /^#[0-9a-f]{6}$/i.test(safeText(value)) ? safeText(value) : fallback;

function OnboardingCard({ onConfirmed, onResolved, showToast }) {
  const [urlInput, setUrlInput] = useState("");
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [warning, setWarning] = useState("");
  const [onboardingStatus, setOnboardingStatus] = useState("idle");
  const [showReplaceWarning, setShowReplaceWarning] = useState(false);
  const [editedFields, setEditedFields] = useState({});
  const [pendingUrl, setPendingUrl] = useState("");

  const applyProfile = useCallback(
    (nextProfile, nextWarning = "") => {
      const normalized = normalizeOnboardingProfile(nextProfile);
      setProfile(normalized);
      setEditedFields({});
      setWarning(nextWarning);
      setUrlInput(normalized.crawlUrl || "");
      setOnboardingStatus(normalized.status === "confirmed" ? "confirmed" : "editing");
      onResolved?.(normalized);
      return normalized;
    },
    [onResolved],
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    loadOnboardingProfile()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        const nextProfile = applyProfile(payload?.profile);
        if (nextProfile.status === "confirmed") {
          onConfirmed?.(nextProfile);
        }
      })
      .catch((loadError) => {
        if (cancelled) {
          return;
        }
        if (loadError instanceof Error && /not found/i.test(loadError.message)) {
          setProfile(null);
          setEditedFields({});
          setOnboardingStatus("idle");
          onResolved?.(null);
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Onboarding profile could not load.");
        setProfile(null);
        setEditedFields({});
        setOnboardingStatus("idle");
        onResolved?.(null);
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [applyProfile, onConfirmed, onResolved]);

  const mergedProfile = normalizeOnboardingProfile({
    ...profile,
    ...editedFields,
    crawlUrl: editedFields.crawlUrl ?? profile?.crawlUrl ?? urlInput,
  });

  const handleFieldChange = (field, value) => {
    setEditedFields((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const handleCrawl = async (nextUrl) => {
    setLoading(true);
    setError("");
    setWarning("");
    setShowReplaceWarning(false);
    setPendingUrl("");
    setOnboardingStatus("crawling");
    try {
      const payload = await crawlWebsite(nextUrl);
      const nextProfile = applyProfile(payload?.profile, payload?.warning || "");
      setUrlInput(nextProfile.crawlUrl || nextUrl);
      if (payload?.warning) {
        showToast?.("Website crawl was partial. Fill in anything the parser missed.");
      } else {
        showToast?.("Website details loaded.");
      }
    } catch (crawlError) {
      setError(crawlError instanceof Error ? crawlError.message : "Website crawl failed.");
      setOnboardingStatus(profile ? "editing" : "idle");
    } finally {
      setLoading(false);
    }
  };

  const handleFetch = async () => {
    const normalizedUrl = urlInput.trim();
    if (!isValidOnboardingUrl(normalizedUrl)) {
      setError("Enter a valid http:// or https:// website URL.");
      return;
    }
    if (profile?.status === "draft" && profile.crawlUrl) {
      setPendingUrl(normalizedUrl);
      setShowReplaceWarning(true);
      return;
    }
    await handleCrawl(normalizedUrl);
  };

  const handleSaveChanges = async () => {
    if (!profile || !Object.keys(editedFields).length) {
      showToast?.("No draft changes to save.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const payload = await updateOnboardingProfile(editedFields);
      applyProfile(payload?.profile, warning);
      showToast?.("Onboarding draft saved.");
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Draft save failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!profile) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      if (Object.keys(editedFields).length) {
        const updatedPayload = await updateOnboardingProfile(editedFields);
        applyProfile(updatedPayload?.profile, warning);
      }
      const confirmedPayload = await confirmOnboardingProfile();
      const confirmedProfile = applyProfile(confirmedPayload?.profile);
      showToast?.("Brand profile confirmed.");
      onConfirmed?.(confirmedProfile);
    } catch (confirmError) {
      setError(confirmError instanceof Error ? confirmError.message : "Profile confirmation failed.");
    } finally {
      setLoading(false);
    }
  };

  const canSave = Boolean(profile) && Boolean(Object.keys(editedFields).length) && !loading;
  const canConfirm = Boolean(profile) && !loading;
  const showForm = Boolean(profile) && onboardingStatus !== "confirmed";

  return (
    <section className="onboarding-card" aria-label="Website onboarding">
      <div className="onboarding-card-head">
        <p className="eyebrow">Smart onboarding</p>
        <h2>Fetch your website and confirm your brand profile</h2>
        <p>
          Paste your homepage URL, review the draft, then confirm once everything looks right. Until
          then, the profile stays in draft and does not change generation.
        </p>
      </div>

      <div className="onboarding-url-input">
        <label className="onboarding-field onboarding-field-full">
          Website URL
          <input
            type="url"
            placeholder="https://yourbusiness.com"
            value={urlInput}
            onChange={(event) => {
              setUrlInput(event.target.value);
              setError("");
            }}
          />
        </label>
        <button className="primary-action" type="button" onClick={handleFetch} disabled={loading}>
          {profile?.crawlUrl ? "Re-fetch" : "Fetch"}
        </button>
      </div>

      {loading && (
        <div className="onboarding-spinner" role="status" aria-live="polite">
          <span aria-label="Loading" />
          <p>{onboardingStatus === "crawling" ? "Analyzing your website..." : "Loading your onboarding draft..."}</p>
        </div>
      )}

      {warning && (
        <div className="onboarding-warning" role="status">
          We couldn't fully analyze your website. Fill in the missing fields manually.
        </div>
      )}

      {error && (
        <div className="onboarding-warning onboarding-warning-error" role="alert">
          {error}
        </div>
      )}

      {showForm && (
        <>
          <div className="onboarding-status-row">
            <span className="status-pill">{safeText(profile?.status, "draft")}</span>
            <small>Review everything on one card, save if needed, then confirm at the bottom.</small>
          </div>
          <div className="onboarding-form">
            {onboardingFieldRows.flat().map((field) => {
              const value = mergedProfile[field.key] || "";
              const className = `onboarding-field${field.fullWidth ? " onboarding-field-full" : ""}`;
              if (field.type === "textarea") {
                return (
                  <label className={className} key={field.key}>
                    {field.label}
                    <textarea
                      rows={4}
                      placeholder={field.placeholder}
                      value={value}
                      onChange={(event) => handleFieldChange(field.key, event.target.value)}
                    />
                    {field.helpText ? <small>{field.helpText}</small> : null}
                  </label>
                );
              }
              if (field.type === "select") {
                return (
                  <label className={className} key={field.key}>
                    {field.label}
                    <select value={value} onChange={(event) => handleFieldChange(field.key, event.target.value)}>
                      {field.options.map(([optionValue, optionLabel]) => (
                        <option value={optionValue} key={optionValue}>
                          {optionLabel}
                        </option>
                      ))}
                    </select>
                    {field.helpText ? <small>{field.helpText}</small> : null}
                  </label>
                );
              }
              if (field.type === "color") {
                return (
                  <label className={`${className} onboarding-color-field`} key={field.key}>
                    {field.label}
                    <div className="onboarding-color-control">
                      <input
                        type="color"
                        value={normalizeColorInputValue(value, field.placeholder)}
                        onChange={(event) => handleFieldChange(field.key, event.target.value)}
                      />
                      <input
                        type="text"
                        placeholder={field.placeholder}
                        value={value}
                        onChange={(event) => handleFieldChange(field.key, event.target.value)}
                      />
                    </div>
                    {field.helpText ? <small>{field.helpText}</small> : null}
                  </label>
                );
              }
              return (
                <label className={className} key={field.key}>
                  {field.label}
                  <input
                    type={field.type}
                    placeholder={field.placeholder}
                    value={value}
                    onChange={(event) => handleFieldChange(field.key, event.target.value)}
                  />
                  {field.helpText ? <small>{field.helpText}</small> : null}
                </label>
              );
            })}
          </div>

          <div className="onboarding-actions">
            <button className="secondary-action" type="button" onClick={handleSaveChanges} disabled={!canSave}>
              Save changes
            </button>
            <button className="primary-action" type="button" onClick={handleConfirm} disabled={!canConfirm}>
              Confirm profile
            </button>
          </div>
        </>
      )}

      {showReplaceWarning && (
        <Modal
          eyebrow="Replace draft"
          title="Replace your current onboarding draft?"
          onClose={() => {
            setShowReplaceWarning(false);
            setPendingUrl("");
          }}
        >
          <div className="onboarding-modal-copy">
            <p>This will replace your current profile draft with fresh website crawl data.</p>
            <div className="onboarding-actions">
              <button
                className="secondary-action"
                type="button"
                onClick={() => {
                  setShowReplaceWarning(false);
                  setPendingUrl("");
                }}
              >
                Keep current draft
              </button>
              <button className="primary-action" type="button" onClick={() => handleCrawl(pendingUrl)}>
                Replace draft
              </button>
            </div>
          </div>
        </Modal>
      )}
    </section>
  );
}

export function AppDemo() {
  const navigate = useNavigate();
  const location = useLocation();
  const [session, setSession] = useState(null);
  const [authStatus, setAuthStatus] = useState("loading");
  const [onboardingProfile, setOnboardingProfile] = useState(null);
  const [onboardingResolved, setOnboardingResolved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadSession()
      .then((data) => {
        if (!cancelled) {
          setSession(data);
          setAuthStatus("authenticated");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAuthStatus("unauthenticated");
          navigate("/");
        }
      });
    return () => { cancelled = true; };
  }, [navigate]);
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
  const [phase3Workspace, setPhase3Workspace] = useState(emptyPhase3Workspace);
  const [phase3Status, setPhase3Status] = useState("loading");
  const [phase3Error, setPhase3Error] = useState("");
  const [approvalPending, setApprovalPending] = useState("");
  const [approvalFeedbackPending, setApprovalFeedbackPending] = useState("");
  const [reviewNotificationPending, setReviewNotificationPending] = useState("");
  const [publishPending, setPublishPending] = useState("");
  const [facebookConnection, setFacebookConnection] = useState({
    configured: false,
    connectedPages: [],
    scopes: [],
    redirectUri: "",
  });
  const [facebookConnectionStatus, setFacebookConnectionStatus] = useState("loading");
  const [facebookPublishForm, setFacebookPublishForm] = useState({
    pageId: "1243605852158721",
    publishMode: "publish_now",
    scheduledPublishTime: "",
  });
  const [competitorSourceForm, setCompetitorSourceForm] = useState({
    label: "Local competitor page",
    url: "",
  });
  const [contentSourceForm, setContentSourceForm] = useState({
    label: "Aurora tune-up offer page",
    url: "https://auroraheatcool.example/ac-tune-up",
  });
  const [contentImageForm, setContentImageForm] = useState({
    label: "Aurora service photo",
    fileName: "",
    mimeType: "",
    imageDataUrl: "",
  });
  const [contentSourcePending, setContentSourcePending] = useState(false);
  const [contentImagePending, setContentImagePending] = useState(false);
  const [sourceGenerationPending, setSourceGenerationPending] = useState("");
  const [assistantPrompt, setAssistantPrompt] = useState("Give me a 3-post content calendar for same-week AC tune-ups");
  const [assistantReplyPending, setAssistantReplyPending] = useState("");
  const [competitorAnalysisPending, setCompetitorAnalysisPending] = useState(false);
  const [mediaAssetPending, setMediaAssetPending] = useState("");
  const [ideaVariantPending, setIdeaVariantPending] = useState("");
  const [bulkVariationPending, setBulkVariationPending] = useState(false);
  const [languageVariantPending, setLanguageVariantPending] = useState(false);
  const [ugcPackagePending, setUgcPackagePending] = useState(false);
  const [activeCreateFormat, setActiveCreateFormat] = useState("");
  const [calendarDrawerOpen, setCalendarDrawerOpen] = useState(false);
  const [activeCreateMethod, setActiveCreateMethod] = useState("write-idea");
  const [creatorStyleForm, setCreatorStyleForm] = useState(defaultCreatorStyleForm);
  const [creatorStylePending, setCreatorStylePending] = useState("");
  const [creatorWorkflowOpen, setCreatorWorkflowOpen] = useState(false);
  const [creatorWorkflowStep, setCreatorWorkflowStep] = useState("prompt");
  const [creatorIdeaChatOpen, setCreatorIdeaChatOpen] = useState(false);
  const [creatorIdeaChatInput, setCreatorIdeaChatInput] = useState(defaultCreatorStyleForm.goal);
  const [creatorIdeaChatResults, setCreatorIdeaChatResults] = useState([]);
  const [creatorScriptDuration, setCreatorScriptDuration] = useState("8s");
  const [creatorScriptRewritePrompt, setCreatorScriptRewritePrompt] = useState("");
  const [carouselStyle, setCarouselStyle] = useState("storytelling");
  const [carouselAspectRatio, setCarouselAspectRatio] = useState("1:1");
  const [carouselSourceMode, setCarouselSourceMode] = useState("idea");
  const [carouselIdeaText, setCarouselIdeaText] = useState("Turn one timely local offer into a five-slide owner-ready carousel.");
  const [carouselSourceUrl, setCarouselSourceUrl] = useState("https://www.nike.com/");
  const [selectedCarouselSlideId, setSelectedCarouselSlideId] = useState("");
  const [carouselSlideDraft, setCarouselSlideDraft] = useState({ headline: "", body: "", ctaLabel: "" });
  const [activeInspirationCategory, setActiveInspirationCategory] = useState("All");
  const [activeInspirationCollection, setActiveInspirationCollection] = useState("");
  const [pendingInspirationCollection, setPendingInspirationCollection] = useState("");
  const [waitNudgeOpen, setWaitNudgeOpen] = useState(false);
  const [libraryFilters, setLibraryFilters] = useState({
    type: "All",
    search: "",
    date: "This month",
    tags: "",
    users: "All users",
    createdFrom: "All sources",
    archived: false,
  });
  const [libraryDetailCreativeId, setLibraryDetailCreativeId] = useState("");
  const [publishDraft, setPublishDraft] = useState({
    creativeId: "",
    platform: "Facebook",
    postType: "Feed post",
    step: "platform",
    scheduleDay: 22,
    scheduleHour: "05",
    scheduleMinute: "15",
    scheduleMeridiem: "PM",
    aiSuggestedTime: false,
    approvalMember: false,
    confirmed: false,
  });
  const [calendarView, setCalendarView] = useState("Monthly");
  const [selectedTimezone, setSelectedTimezone] = useState("America/Detroit");
  const [selectedCalendarSlotId, setSelectedCalendarSlotId] = useState("");
  const [activeBrandAccountTab, setActiveBrandAccountTab] = useState("Social Platforms");
  const [activeBrandDetailSection, setActiveBrandDetailSection] = useState("Content settings");
  const [socialActionDialog, setSocialActionDialog] = useState(null);
  const [helpFlyoutOpen, setHelpFlyoutOpen] = useState(false);
  const [selectedFacebookPageId, setSelectedFacebookPageId] = useState("");
  const [helpDraft, setHelpDraft] = useState("");
  const [activeHelpAction, setActiveHelpAction] = useState(helpActions[0]?.[0] || "FAQs");
  const [cookingCreativeId, setCookingCreativeId] = useState("");
  const [queuedPublishJobs, setQueuedPublishJobs] = useState({});
  const [aiResponse, setAiResponse] = useState(
    "I will create platform-native posts, reserve Xiaohongshu for searchable recommendations, and track calls, DMs, coupon scans, bookings, and map clicks.",
  );
  const [appToast, setAppToast] = useState("");
  const [genCatalog, setGenCatalog] = useState([]);
  const [genCredits, setGenCredits] = useState({ accountId: "", balance: 0, reserved: 0, available: 0 });
  const [genJobs, setGenJobs] = useState([]);
  const [genSelectedModel, setGenSelectedModel] = useState("");
  const [genPrompt, setGenPrompt] = useState("");
  const [genLaunchPending, setGenLaunchPending] = useState(false);
  const [genRetryPending, setGenRetryPending] = useState("");
  const [genDetailJobId, setGenDetailJobId] = useState("");
  const [genStatus, setGenStatus] = useState("idle");
  const campaignInput = workflowCampaignInput(workflow);
  const phase3Creatives = Array.isArray(phase3Workspace.generatedCreatives)
    ? phase3Workspace.generatedCreatives
    : [];
  const phase3BrandKit = phase3Workspace.brandKit || {};
  const phase3ContentSources = Array.isArray(phase3Workspace.contentSources)
    ? phase3Workspace.contentSources
    : [];
  const phase3AssistantReplies = Array.isArray(phase3Workspace.aiAssistantReplies)
    ? phase3Workspace.aiAssistantReplies
    : [];
  const phase3Ideas = Array.isArray(phase3Workspace.competitorIdeas)
    ? phase3Workspace.competitorIdeas
    : [];
  const phase3CompetitorSources = Array.isArray(phase3Workspace.competitorSources)
    ? phase3Workspace.competitorSources
    : [];
  const phase3ProofEvents = Array.isArray(phase3Workspace.proofEvents)
    ? phase3Workspace.proofEvents
    : [];
  const phase3CalendarSlots = Array.isArray(phase3Workspace.calendarSlots)
    ? phase3Workspace.calendarSlots
    : [];
  const phase3CreativeTemplates = Array.isArray(phase3Workspace.creativeTemplates)
    ? phase3Workspace.creativeTemplates
    : [];
  const phase3ImportedTemplates = Array.isArray(phase3Workspace.importedTemplates)
    ? phase3Workspace.importedTemplates
    : [];
  const phase3ApprovalReviewLinks = Array.isArray(phase3Workspace.approvalReviewLinks)
    ? phase3Workspace.approvalReviewLinks
    : [];
  const phase3ApprovalFeedback = Array.isArray(phase3Workspace.approvalFeedback)
    ? phase3Workspace.approvalFeedback
    : [];
  const phase3ReviewNotifications = Array.isArray(phase3Workspace.reviewNotifications)
    ? phase3Workspace.reviewNotifications
    : [];
  const phase3AssetLibraryItems = Array.isArray(phase3Workspace.assetLibraryItems)
    ? phase3Workspace.assetLibraryItems
    : [];
  const phase3PerformanceSnapshots = Array.isArray(phase3Workspace.performanceSnapshots)
    ? phase3Workspace.performanceSnapshots
    : [];
  const phase3AnalyticsInsights = Array.isArray(phase3Workspace.analyticsInsights)
    ? phase3Workspace.analyticsInsights
    : [];
  const phase3AnalyticsSummary = phase3Workspace.analyticsSummary || {};
  const phase3Usage = phase3Workspace.usage || {};
  const creatorStyleWorkflows = Array.isArray(phase3Workspace.creatorStyleWorkflows)
    ? phase3Workspace.creatorStyleWorkflows
    : [];
  const creatorStyleOptions = phase3Workspace.creatorStyleOptions || {};
  const creatorStyleStyles = Array.isArray(creatorStyleOptions.styles) ? creatorStyleOptions.styles : [];
  const creatorStyleActors = Array.isArray(creatorStyleOptions.actors) ? creatorStyleOptions.actors : [];
  const creatorStyleTemplates = Array.isArray(creatorStyleOptions.templates) ? creatorStyleOptions.templates : [];
  const mergeCreatorOptions = (preferredOptions, fallbackOptions) => {
    const byId = new Map();
    fallbackOptions.forEach((option) => byId.set(option.id, option));
    preferredOptions.forEach((option) => byId.set(option.id, { ...(byId.get(option.id) || {}), ...option }));
    return Array.from(byId.values());
  };
  const creatorStyleStyleChoices = creatorStyleStyles.length
    ? creatorStyleStyles
    : [
        {
          id: "motivational",
          label: "Motivational",
          summary: "Direct-to-camera encouragement with a clear reason to act now.",
        },
      ];
  const creatorStyleActorChoices = mergeCreatorOptions(creatorStyleActors, fallbackCreatorActorChoices);
  const creatorStyleTemplateChoices = mergeCreatorOptions(creatorStyleTemplates, fallbackCreatorTemplateChoices);
  const selectedCreatorWorkflow =
    creatorStyleWorkflows.find(
      (workflow) =>
        workflow.prompt === creatorStyleForm.prompt &&
        workflow.goal === creatorStyleForm.goal &&
        workflow.status !== "archived",
    ) ||
    creatorStyleWorkflows[0] ||
    null;
  const selectedCreatorIdeas = selectedCreatorWorkflow?.ideas || [];
  const selectedCreatorIdea =
    selectedCreatorIdeas.find((idea) => idea.id === creatorStyleForm.selectedIdeaId) ||
    selectedCreatorIdeas.find((idea) => idea.id === selectedCreatorWorkflow?.selectedIdeaId) ||
    selectedCreatorIdeas[0] ||
    null;
  const selectedCreatorCreative = selectedCreatorWorkflow?.creativeId
    ? phase3Creatives.find((creative) => creative.id === selectedCreatorWorkflow.creativeId)
    : null;
  const selectedCreatorCalendarSlot = selectedCreatorCreative
    ? phase3CalendarSlots.find((slot) => slot.creativeId === selectedCreatorCreative.id)
    : null;
  const selectedCreatorMediaAsset =
    selectedCreatorCreative?.mediaAssets?.find((asset) => asset.assetType === "creator_style_video_storyboard") ||
    selectedCreatorCreative?.mediaAssets?.[0] ||
    null;
  const selectedCreatorPackage = selectedCreatorCreative?.ugcVoiceoverPackages?.[0] || null;
  const selectedCreatorStyle =
    creatorStyleStyleChoices.find((style) => style.id === creatorStyleForm.styleId) ||
    creatorStyleStyleChoices[0] ||
    null;
  const selectedCreatorActor =
    creatorStyleActorChoices.find((actor) => actor.id === creatorStyleForm.actorId) || null;
  const selectedCreatorTemplate =
    creatorStyleTemplateChoices.find((template) => template.id === creatorStyleForm.templateId) || null;
  const selectedCreatorScriptDuration =
    creatorScriptDurationOptions.find((duration) => duration.id === creatorScriptDuration) ||
    creatorScriptDurationOptions[0];
  const creatorReviewScript = [
    selectedCreatorIdea?.hook || creatorStyleForm.prompt,
    selectedCreatorIdea?.angle,
    "Book your expert consultation today.",
  ]
    .filter(Boolean)
    .join(" ");
  const creatorVisibleWorkflowSteps = creatorWorkflowSteps.filter((step) => step.id !== "generated");
  const rawCreatorWorkflowStepIndex = Math.max(
    0,
    creatorWorkflowSteps.findIndex((step) => step.id === creatorWorkflowStep),
  );
  const creatorWorkflowStepIndex =
    creatorWorkflowStep === "generated"
      ? creatorVisibleWorkflowSteps.length - 1
      : Math.max(0, creatorVisibleWorkflowSteps.findIndex((step) => step.id === creatorWorkflowStep));
  const activeCreatorWorkflowStep = creatorWorkflowSteps[rawCreatorWorkflowStepIndex] || creatorWorkflowSteps[0];
  const creatorCanContinue =
    creatorWorkflowStep === "prompt"
      ? Boolean(creatorStyleForm.prompt.trim() && creatorStyleForm.goal.trim())
      : creatorWorkflowStep === "idea"
      ? Boolean(selectedCreatorIdea)
      : creatorWorkflowStep === "style"
      ? Boolean(selectedCreatorStyle && creatorStyleForm.aspectRatio)
      : creatorWorkflowStep === "actor"
      ? Boolean(selectedCreatorActor)
      : creatorWorkflowStep === "template"
      ? Boolean(selectedCreatorTemplate)
      : creatorWorkflowStep === "review"
      ? Boolean(selectedCreatorIdea && selectedCreatorStyle && selectedCreatorActor && selectedCreatorTemplate)
      : creatorWorkflowStep === "confirm"
      ? Boolean(selectedCreatorIdea && selectedCreatorStyle && selectedCreatorActor && selectedCreatorTemplate)
      : true;
  const selectedHelpAction =
    helpActions.find(([title]) => title === activeHelpAction) ||
    helpActions[0] || ["FAQs", "Find answers about generation, publishing, and account setup."];
  const onboardingRequired = !onboardingResolved || onboardingProfile?.status !== "confirmed";
  const phase3CreativesByPlatform = useMemo(
    () =>
      phase3Creatives.reduce((byPlatform, creative) => {
        byPlatform[creative.platform] = creative;
        return byPlatform;
      }, {}),
    [phase3Creatives],
  );
  const approvalReviewLinksByCreativeId = useMemo(
    () =>
      phase3ApprovalReviewLinks.reduce((byCreative, link) => {
        byCreative[link.creativeId] = link;
        return byCreative;
      }, {}),
    [phase3ApprovalReviewLinks],
  );
  const approvalFeedbackByCreativeId = useMemo(
    () =>
      phase3ApprovalFeedback.reduce((byCreative, feedback) => {
        byCreative[feedback.creativeId] = [...(byCreative[feedback.creativeId] || []), feedback];
        return byCreative;
      }, {}),
    [phase3ApprovalFeedback],
  );
  const reviewNotificationsByCreativeId = useMemo(
    () =>
      phase3ReviewNotifications.reduce((byCreative, notification) => {
        byCreative[notification.creativeId] = [
          ...(byCreative[notification.creativeId] || []),
          notification,
        ];
        return byCreative;
      }, {}),
    [phase3ReviewNotifications],
  );
  const phase3CreativeForPlan = (plan, index) =>
    phase3CreativesByPlatform[plan?.platform] || phase3Creatives[index] || null;
  const brandKitDisplayCards = phase3BrandKit.id
    ? [
        ["Business", campaignInput.business, phase3BrandKit.voice?.audience || campaignInput.audience],
        ["Tone", phase3BrandKit.voice?.tone || "trusted, prompt, local", phase3BrandKit.voice?.promise || "Helpful local expert"],
        ["Colors", (phase3BrandKit.colors || []).join(", "), "Applied to cards, carousels, and proof reports"],
        ["Approved words", (phase3BrandKit.approvedTerms || []).join(", "), "Used by the generator before every draft"],
        ["Avoid", (phase3BrandKit.avoidTerms || []).join(", "), "Risk guardrails before owner approval"],
        ["Examples", `${(phase3BrandKit.examples || []).length} saved examples`, "Used as the brand voice calibration seed"],
      ]
    : brandKitCards;
  const proofEventDisplayCards = proofEvents.map(([label, fallbackValue, body]) => {
    const normalized = label.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
    const value = phase3ProofEvents
      .filter((event) => event.eventType === normalized || event.label === label)
      .reduce((total, event) => total + Number(event.value || 0), 0);
    return [label, String(Number(fallbackValue) + value), body, normalized];
  });
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
  const selectedPhase3Creative = phase3Creatives[clampIndex(safeSelectedPost, phase3Creatives)] || phase3Creatives[0];
  const selectedPhase3Slot = selectedPhase3Creative
    ? phase3CalendarSlots.find((slot) => slot.creativeId === selectedPhase3Creative.id)
    : null;
  const activeCalendarSlot =
    phase3CalendarSlots.find((slot) => slot.id === selectedCalendarSlotId) ||
    selectedPhase3Slot ||
    phase3CalendarSlots[0] ||
    null;
  const selectedPhase3MediaAssets = Array.isArray(selectedPhase3Creative?.mediaAssets)
    ? selectedPhase3Creative.mediaAssets
    : [];
  const selectedPhase3LanguageVariants = Array.isArray(selectedPhase3Creative?.languageVariants)
    ? selectedPhase3Creative.languageVariants
    : [];
  const selectedPhase3BulkVariants = Array.isArray(selectedPhase3Creative?.bulkVariants)
    ? selectedPhase3Creative.bulkVariants
    : [];
  const selectedPhase3UgcPackages = Array.isArray(selectedPhase3Creative?.ugcVoiceoverPackages)
    ? selectedPhase3Creative.ugcVoiceoverPackages
    : [];
  const isCarouselEditor = selectedPhase3Creative?.editorMode === "carousel_slide_edit";
  const selectedCarouselAssets = selectedPhase3MediaAssets.filter((asset) => asset?.metadata?.carouselSlide);
  const activeCarouselAsset =
    selectedCarouselAssets.find((asset) => asset.id === selectedCarouselSlideId) ||
    selectedCarouselAssets[0] ||
    null;
  const activeCarouselPayload = activeCarouselAsset?.metadata?.composedPayload || {};
  const creativePreviewImage = (creative, index = 0) => {
    const mediaAsset = creative?.mediaAssets?.[0];
    return (
      creative?.previewDataUrl ||
      mediaAsset?.metadata?.composedPayload?.thumbnailRender ||
      mediaAsset?.previewDataUrl ||
      mediaAsset?.renderedOutputs?.[0]?.previewDataUrl ||
      referencePreviewImages[index % referencePreviewImages.length]
    );
  };
  const filteredLibraryCreatives = useMemo(() => {
    const search = libraryFilters.search.trim().toLowerCase();
    const tagSearch = libraryFilters.tags.trim().toLowerCase();
    return phase3Creatives.filter((creative) => {
      const blob = [
        creative.title,
        creative.caption,
        creative.platform,
        creative.format,
        creative.status,
        ...(creative.hashtags || []),
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const mediaBlob = (creative.mediaAssets || [])
        .map((asset) => `${asset.assetType || ""} ${asset.format || ""} ${asset.aspectRatio || ""}`)
        .join(" ")
        .toLowerCase();
      const typeBlob = `${blob} ${mediaBlob}`;
      const matchesType =
        libraryFilters.type === "All" ||
        (libraryFilters.type === "Image" && /image|static|square|post/.test(typeBlob)) ||
        (libraryFilters.type === "Video" && /video|reel|storyboard|ugc|tiktok/.test(typeBlob)) ||
        (libraryFilters.type === "Carousel" && /carousel/.test(typeBlob));
      const matchesSearch = !search || blob.includes(search);
      const matchesTags = !tagSearch || blob.includes(tagSearch);
      const matchesArchive = libraryFilters.archived || creative.status !== "archived";
      return matchesType && matchesSearch && matchesTags && matchesArchive;
    });
  }, [libraryFilters, phase3Creatives]);
  const libraryDetailCreative =
    phase3Creatives.find((creative) => creative.id === libraryDetailCreativeId) || null;
  const libraryDetailIndex = libraryDetailCreative
    ? Math.max(0, phase3Creatives.findIndex((creative) => creative.id === libraryDetailCreative.id))
    : 0;
  const libraryDetailMediaAsset = libraryDetailCreative?.mediaAssets?.[0] || null;
  const libraryDetailPreviewImage = creativePreviewImage(libraryDetailCreative, libraryDetailIndex);
  const libraryDetailPrompt =
    libraryDetailMediaAsset?.metadata?.prompt ||
    libraryDetailMediaAsset?.metadata?.inputPrompt ||
    libraryDetailCreative?.sourcePrompt ||
    creatorStyleForm.prompt ||
    campaignInput.offer;
  const publishCreative =
    phase3Creatives.find((creative) => creative.id === publishDraft.creativeId) ||
    selectedPhase3Creative ||
    phase3Creatives[0] ||
    null;
  const publishMediaBlob = [
    publishCreative?.format,
    ...(publishCreative?.mediaAssets || []).map((asset) => `${asset.assetType} ${asset.format}`),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  const publishIsVideo = /video|reel|storyboard|ugc|tiktok/.test(publishMediaBlob);
  const publishUnsupported =
    publishDraft.platform === "Facebook" && publishDraft.postType === "Feed post" && publishIsVideo;
  const publishMissingAccount =
    publishDraft.platform.startsWith("Facebook") && facebookConnection.connectedPages.length === 0;
  const publishAssisted =
    publishDraft.platform === "Assisted Package" ||
    publishDraft.platform === "TikTok" ||
    publishDraft.platform === "Google Business Profile";
  const publishCanContinue = Boolean(publishCreative) && !publishUnsupported;
  const selectedFacebookPage =
    facebookConnection.connectedPages.find((page) => page.pageId === selectedFacebookPageId) ||
    facebookConnection.connectedPages[0] ||
    null;
  const pagePickerPages = facebookConnection.connectedPages.length
    ? facebookConnection.connectedPages
    : [
        {
          pageId: "demo-page-aurora",
          name: "Aurora Heating & Cooling",
          category: "Local service",
          tasks: ["CREATE_CONTENT", "MANAGE", "ANALYZE"],
        },
        {
          pageId: "demo-page-maintenance",
          name: "Aurora Maintenance Tips",
          category: "Community page",
          tasks: ["CREATE_CONTENT", "ANALYZE"],
        },
      ];
  const activeSocialPlatform =
    socialPlatformRows.find((platform) => platform.provider === socialActionDialog?.provider) || null;
  const activeSocialFaqs =
    activeSocialPlatform ? socialPlatformFaqs[activeSocialPlatform.provider] || defaultSocialFaqs : [];
  const activeSocialConnectionChoices =
    activeSocialPlatform
      ? socialConnectionChoices[activeSocialPlatform.provider] || [
          {
            title: activeSocialPlatform.accountType,
            subtitle: "(official OAuth)",
            badge: "SAFE",
            badgeTone: "safe",
            icon: activeSocialPlatform.icon,
          },
        ]
      : [];
  const config = moduleDetails[activeModule] || moduleDetails["Content Library"];
  const createFlowTitle =
    {
      image: "Create Image",
      ugc: "Create Creator Style Video",
      "short-ad-video": "Create Short Ad Video",
      carousel: "Configure your Carousel",
      "faceless-video": "Create Faceless Video",
      "product-photo-shoot": "Create Product Photo Shoot",
    }[activeCreateFormat] || config.title;
  const pageTitle = config.view === "create" && activeCreateFormat ? createFlowTitle : config.title;
  const pageSubtitle =
    config.view === "create"
      ? activeCreateFormat === "ugc"
        ? "Describe the video, generate ideas, choose style, actor, template, then generate and schedule."
        : activeCreateFormat
        ? "Choose the content source and confirm the setup before generation."
        : "Choose a media type to get started."
      : "";
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
    activeModule === "Content Calendar"
      ? { label: "Approve exact draft", handler: () => approvePlan(safeSelectedPost) }
      : { label: "Create New", handler: () => selectModule("Create New") };
  const topbarSecondaryAction =
    activeModule === "Content Calendar"
      ? { label: "Save package", handler: () => exportPackage() }
      : { label: "Review calendar", handler: () => selectModule("Content Calendar") };
  const workspaceMetrics =
    activeModule === "Content Calendar"
      ? [
          ["Pending approvals", String(pendingPlans.length), "Need a decision before publishing"],
          ["Selected slot", selectedPlan?.name || "—", selectedPlan?.scheduleSlot || "Choose a slot"],
          ["Package readiness", `${packageReadiness}%`, `${approvedCount}/${plans.length || 0} approved`],
          ["Proof events", "6 types", "Calls, bookings, DMs, coupons, maps"],
        ]
      : [
          ["Business input", "1", campaignInput.offer],
          ["Native outputs", String(plans.length), plans.length ? "Facebook and TikTok backend drafts" : "Loading workflow"],
          ["Proof hooks", "6", "Calls, bookings, DMs, scans, coupons, maps"],
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

  const reloadPhase3Workspace = useCallback(async ({ silent = false } = {}) => {
    if (!silent) {
      setPhase3Status("loading");
    }
    setPhase3Error("");
    try {
      const workspace = await loadPhase3Workspace();
      setPhase3Workspace({
        ...emptyPhase3Workspace,
        ...workspace,
      });
      setPhase3Status("ready");
      return workspace;
    } catch (error) {
      setPhase3Status("error");
      setPhase3Error(error instanceof Error ? error.message : "Phase 3 workspace could not load.");
      return null;
    }
  }, []);

  const handleOnboardingResolved = useCallback((nextProfile) => {
    setOnboardingProfile(nextProfile);
    setOnboardingResolved(true);
  }, []);

  const handleOnboardingConfirmed = useCallback(async (nextProfile) => {
    setOnboardingProfile(nextProfile);
    setOnboardingResolved(true);
    await reloadPhase3Workspace({ silent: true });
  }, [reloadPhase3Workspace]);

  const reloadFacebookConnection = async () => {
    setFacebookConnectionStatus("loading");
    try {
      const payload = await loadFacebookConnection();
      const connectedPages = Array.isArray(payload?.connectedPages) ? payload.connectedPages : [];
      setFacebookConnection({
        configured: Boolean(payload?.configured),
        connectedPages,
        scopes: Array.isArray(payload?.scopes) ? payload.scopes : [],
        redirectUri: payload?.redirectUri || "",
      });
      if (connectedPages[0]?.pageId) {
        updateFacebookPublishForm("pageId", connectedPages[0].pageId);
        setSelectedFacebookPageId(connectedPages[0].pageId);
      }
      setFacebookConnectionStatus("ready");
    } catch {
      setFacebookConnectionStatus("error");
    }
  };

  const reloadGenerationWorkspace = async () => {
    setGenStatus("loading");
    try {
      const [catalogPayload, creditsPayload, jobsPayload] = await Promise.all([
        loadGenerationModels(),
        loadGenerationCredits(),
        loadGenerationJobs(),
      ]);
      const catalog = normalizeGenerationCatalog(catalogPayload);
      setGenCatalog(catalog.models);
      setGenCredits(normalizeCreditSummary(creditsPayload?.credits));
      setGenJobs(normalizeGenerationJobsList(jobsPayload));
      if (!genSelectedModel && catalog.models.length) {
        const defaultModel = catalog.models.find((model) => model.id === MINIMAX_CAROUSEL_MODEL_ID) || catalog.models[0];
        setGenSelectedModel(defaultModel.id);
      }
      setGenStatus("ready");
    } catch {
      setGenStatus("error");
    }
  };

  const openCarouselEditor = async (creativeId) => {
    if (!creativeId) return;
    const refreshedWorkspace = await reloadPhase3Workspace({ silent: true });
    const refreshedCreatives = Array.isArray(refreshedWorkspace?.generatedCreatives)
      ? refreshedWorkspace.generatedCreatives
      : phase3Creatives;
    const creativeIndex = refreshedCreatives.findIndex((creative) => creative.id === creativeId);
    if (creativeIndex >= 0) {
      setSelectedPost(creativeIndex);
      setLibraryDetailCreativeId(creativeId);
    }
    selectModule("Content Library");
    showAppToast("Carousel package opened in Creative Editor.");
  };

  const openVideoEditor = async (creativeId) => {
    if (!creativeId) return;
    const refreshedWorkspace = await reloadPhase3Workspace({ silent: true });
    const refreshedCreatives = Array.isArray(refreshedWorkspace?.generatedCreatives)
      ? refreshedWorkspace.generatedCreatives
      : phase3Creatives;
    const creativeIndex = refreshedCreatives.findIndex((creative) => creative.id === creativeId);
    if (creativeIndex >= 0) {
      setSelectedPost(creativeIndex);
      setLibraryDetailCreativeId(creativeId);
    }
    selectModule("Content Library");
    showAppToast("Video opened in Creative Editor.");
  };

  const handleCarouselLaunch = async () => {
    if (!carouselModel) {
      showAppToast("Carousel model is not available.");
      return;
    }
    if (!carouselBrandReady) {
      showAppToast("Finish the brand kit before generating a carousel.");
      return;
    }
    if (!carouselSourceValue) {
      showAppToast(carouselSourceMode === "url" ? "Paste one public URL first." : "Write one idea first.");
      return;
    }
    if (!carouselUrlValidity) {
      showAppToast("Enter one valid public URL.");
      return;
    }
    if (carouselCreditCost > genCredits.available) {
      showAppToast("Not enough credits for this carousel run.");
      return;
    }
    setGenLaunchPending(true);
    try {
      const payload = await launchGenerationJob({
        modelId: carouselModel.id,
        prompt: carouselSourceValue,
        workflowType: "carousel",
        carouselPresetId: CAROUSEL_PRESET_ID,
        sourceKind: carouselSourceMode,
        sourceText: carouselSourceMode === "idea" ? carouselSourceValue : "",
        sourceUrl: carouselSourceMode === "url" ? carouselSourceValue : "",
        slideRoles: CAROUSEL_ROLE_ORDER,
        settings: {
          aspectRatio: "3:4",
        },
      });
      const newJob = normalizeGenerationJob(payload?.job);
      setGenSelectedModel(carouselModel.id);
      setGenJobs((prev) => [newJob, ...prev.filter((job) => job.id !== newJob.id)]);
      setGenDetailJobId(newJob.id);
      await reloadGenerationWorkspace();
      showAppToast("Carousel generation launched on the normal credit ledger.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Carousel launch failed.");
    } finally {
      setGenLaunchPending(false);
    }
  };

  const handleGenLaunch = async () => {
    if (!genSelectedModel || !genPrompt.trim()) return;
    setGenLaunchPending(true);
    try {
      const result = await launchGenerationJob({
        modelId: genSelectedModel,
        prompt: genPrompt.trim(),
        settings: {},
      });
      const newJob = normalizeGenerationJob(result?.job);
      setGenJobs((prev) => [newJob, ...prev]);
      setGenPrompt("");
      await reloadGenerationWorkspace();
      showAppToast("Generation job launched.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Launch failed.");
    } finally {
      setGenLaunchPending(false);
    }
  };

  const handleGenRetry = async (jobId) => {
    setGenRetryPending(jobId);
    try {
      await retryGenerationJob(jobId);
      await reloadGenerationWorkspace();
      showAppToast("Retry launched.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Retry failed.");
    } finally {
      setGenRetryPending("");
    }
  };

  const genActiveModel = genCatalog.find((m) => m.id === genSelectedModel) || null;
  const genEstimatedCost = genActiveModel ? genActiveModel.creditCost : 0;
  const genInsufficientCredits = genEstimatedCost > genCredits.available;
  const genSucceededJobs = genJobs.filter((j) => j.status === "succeeded");
  const genActiveJobs = genJobs.filter((j) => j.status === "queued" || j.status === "running");
  const carouselModel = genCatalog.find((model) => model.id === MINIMAX_CAROUSEL_MODEL_ID) || genCatalog.find((model) => model.capability === "image") || null;
  const carouselJobs = genJobs.filter((job) => job.workflowType === "carousel");
  const carouselActiveJobs = carouselJobs.filter((job) => job.status === "queued" || job.status === "running");
  const latestCarouselJob = carouselJobs[0] || null;
  const carouselCreditCost = carouselModel ? carouselModel.creditCost : 0;
  const carouselBrandReady = Boolean(phase3BrandKit?.id);
  const carouselSourceValue = carouselSourceMode === "url" ? carouselSourceUrl.trim() : carouselIdeaText.trim();
  const carouselUrlValidity = (() => {
    if (carouselSourceMode !== "url") return true;
    try {
      const candidate = new URL(carouselSourceUrl.trim());
      const hostname = (candidate.hostname || "").toLowerCase();
      return ["http:", "https:"].includes(candidate.protocol) && hostname && !["localhost", "127.0.0.1"].includes(hostname);
    } catch {
      return false;
    }
  })();
  const carouselLaunchBlocked =
    genLaunchPending ||
    !carouselModel ||
    !carouselBrandReady ||
    !carouselSourceValue ||
    !carouselUrlValidity ||
    carouselCreditCost > genCredits.available ||
    carouselActiveJobs.length > 0;

  const carouselStageLabel = (job) => {
    if (!job) return "No carousel generated yet";
    if (job.status === "failed") return "Failed";
    if (job.status === "succeeded") return "Ready in editor";
    if (job.carouselStage === "packaging") return "Packaging";
    if (job.carouselStage === "generating_slides") return `Generating slides ${job.completedSlides || 0}/5`;
    return "Planning";
  };

  useEffect(() => {
    reloadWorkflow();
    reloadPhase3Workspace();
    reloadFacebookConnection();
    reloadGenerationWorkspace();
  }, []);

  useEffect(() => {
    if (!genCatalog.length) return;
    if (genSelectedModel && genCatalog.some((model) => model.id === genSelectedModel)) return;
    const nextModel = genCatalog.find((model) => model.id === MINIMAX_CAROUSEL_MODEL_ID) || genCatalog[0];
    if (nextModel?.id) {
      setGenSelectedModel(nextModel.id);
    }
  }, [genCatalog, genSelectedModel]);

  useEffect(() => {
    if (!selectedCarouselAssets.length) {
      setSelectedCarouselSlideId("");
      return;
    }
    if (selectedCarouselAssets.some((asset) => asset.id === selectedCarouselSlideId)) return;
    setSelectedCarouselSlideId(selectedCarouselAssets[0].id);
  }, [selectedCarouselAssets, selectedCarouselSlideId]);

  useEffect(() => {
    const composed = activeCarouselAsset?.metadata?.composedPayload;
    if (!composed) return;
    setCarouselSlideDraft({
      headline: composed.headline || "",
      body: composed.body || "",
      ctaLabel: composed.ctaLabel || "",
    });
  }, [activeCarouselAsset?.id]);

  useEffect(() => {
    if (!carouselActiveJobs.length) return undefined;
    const timer = window.setTimeout(() => {
      reloadGenerationWorkspace();
      reloadPhase3Workspace({ silent: true });
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [carouselActiveJobs.length]);

  useEffect(() => {
    const queryModule = moduleFromSlug(new URLSearchParams(location.search).get("module"));
    if (queryModule && queryModule !== activeModule) {
      setActiveModule(queryModule);
    }
    const params = new URLSearchParams(location.search);
    if (params.get("facebookConnected") === "1") {
      reloadWorkflow({ silent: true });
      reloadFacebookConnection();
      setAppToast("Facebook Page connected. You can publish approved Facebook drafts live.");
    }
  }, [activeModule, location.search]);

  useEffect(() => {
    if (!brandAccountTabs.includes(activeBrandAccountTab)) {
      setActiveBrandAccountTab("Brand Details");
    }
  }, [activeBrandAccountTab]);

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

  useEffect(() => {
    if (!genActiveJobs.length) return;
    let backoffMs = 3000;
    const maxBackoffMs = 30000;
    let intervalId;
    let timeoutId;

    const poll = () => {
      reloadGenerationWorkspace();
      backoffMs = Math.min(backoffMs * 2, maxBackoffMs);
      timeoutId = window.setTimeout(poll, backoffMs);
    };

    timeoutId = window.setTimeout(poll, backoffMs);

    return () => {
      if (intervalId) window.clearInterval(intervalId);
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [genActiveJobs.length]);

  const showAppToast = (message) => {
    setAppToast(message);
    window.setTimeout(() => setAppToast(""), 2200);
  };

  const startCooking = (creativeId = "pending") => {
    setCookingCreativeId(creativeId);
    window.setTimeout(() => {
      setCookingCreativeId((current) => (current === creativeId ? "" : current));
    }, 1800);
  };

  const updateLibraryFilter = (field, value) => {
    setLibraryFilters((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const applyCreatorStylePayload = (payload) => {
    if (payload?.workspace) {
      setPhase3Workspace({
        ...emptyPhase3Workspace,
        ...payload.workspace,
      });
    }
    if (payload?.workflow) {
      setCreatorStyleForm((current) => ({
        ...current,
        prompt: payload.workflow.prompt || current.prompt,
        goal: payload.workflow.goal || current.goal,
        selectedIdeaId: payload.workflow.selectedIdeaId || payload.workflow.ideas?.[0]?.id || current.selectedIdeaId,
        styleId: payload.workflow.styleId || current.styleId,
        actorId: payload.workflow.status === "generated_ready" ? payload.workflow.actor?.id || current.actorId : current.actorId,
        templateId:
          payload.workflow.status === "generated_ready" ? payload.workflow.template?.id || current.templateId : current.templateId,
      }));
    }
  };

  const generateCreatorStyleIdeas = async (overrides = {}) => {
    const nextForm = {
      ...creatorStyleForm,
      ...overrides,
    };
    setCreatorStylePending("ideas");
    try {
      const payload = await createPhase3CreatorStyleVideoWorkflow({
        prompt: nextForm.prompt,
        goal: nextForm.goal,
        styleId: nextForm.styleId,
        actorId: nextForm.actorId,
        templateId: nextForm.templateId,
        aspectRatio: nextForm.aspectRatio,
      });
      applyCreatorStylePayload(payload);
      if (payload?.workflow?.ideas?.length) {
        setCreatorWorkflowStep("idea");
      }
      showAppToast(`${payload?.workflow?.ideas?.length || 0} creator-style ideas generated.`);
      return payload?.workflow || null;
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Creator-style ideas could not be generated.");
      return null;
    } finally {
      setCreatorStylePending("");
    }
  };

  const generateCreatorStyleVideo = async () => {
    setCreatorStylePending("generate");
    startCooking("creator-style-video");
    try {
      let workflow =
        creatorStyleWorkflows.find(
          (item) => item.prompt === creatorStyleForm.prompt && item.goal === creatorStyleForm.goal,
        ) || selectedCreatorWorkflow;
    if (!workflow?.id) {
        const ideasPayload = await createPhase3CreatorStyleVideoWorkflow({
          prompt: creatorStyleForm.prompt,
          goal: creatorStyleForm.goal,
          styleId: creatorStyleForm.styleId,
          actorId: creatorStyleForm.actorId,
          templateId: creatorStyleForm.templateId,
          aspectRatio: creatorStyleForm.aspectRatio,
        });
        applyCreatorStylePayload(ideasPayload);
        workflow = ideasPayload?.workflow;
      }
      if (!workflow?.id) {
        showAppToast("Generate ideas before creating the creator-style video.");
        return;
      }
      const payload = await generatePhase3CreatorStyleVideo(workflow.id, {
        prompt: creatorStyleForm.prompt,
        goal: creatorStyleForm.goal,
        selectedIdeaId: creatorStyleForm.selectedIdeaId || workflow.selectedIdeaId || workflow.ideas?.[0]?.id,
        styleId: creatorStyleForm.styleId,
        actorId: creatorStyleForm.actorId,
        templateId: creatorStyleForm.templateId,
        aspectRatio: creatorStyleForm.aspectRatio,
      });
      applyCreatorStylePayload(payload);
      setCreatorWorkflowStep("generated");
      setAiResponse(
        `${payload?.creative?.title || "Creator-style video"} is storyboard-ready with actor, scenes, UGC package, and calendar slot.`,
      );
      showAppToast("Creator-style video generated into backend workspace.");
      return payload;
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Creator-style video generation failed.");
      return null;
    } finally {
      setCreatorStylePending("");
    }
  };

  const openCreatorSchedule = () => {
    if (!selectedCreatorCreative?.id) {
      showAppToast("Generate the creator-style video before scheduling it.");
      return;
    }
    if (selectedCreatorCalendarSlot?.id) {
      setSelectedCalendarSlotId(selectedCreatorCalendarSlot.id);
    }
    setCreatorWorkflowOpen(false);
    selectModule("Content Calendar");
    setCalendarDrawerOpen(true);
    showAppToast("Creator-style video schedule opened in Content Calendar.");
  };

  const applyCreatorWorkflowOption = (value, options, fallback) =>
    options.some((option) => option.id === value) ? value : fallback;

  const openCreatorWorkflow = (step = "prompt") => {
    setCreatorStyleForm((current) => ({
      ...current,
      prompt: safeText(current.prompt, defaultCreatorStyleForm.prompt),
      goal: safeText(current.goal, defaultCreatorStyleForm.goal),
      selectedIdeaId: "",
      styleId: applyCreatorWorkflowOption(current.styleId, creatorStyleStyleChoices, defaultCreatorStyleForm.styleId),
      actorId: applyCreatorWorkflowOption(current.actorId, creatorStyleActorChoices, ""),
      templateId: applyCreatorWorkflowOption(current.templateId, creatorStyleTemplateChoices, ""),
      aspectRatio: creatorAspectRatioOptions.includes(current.aspectRatio) ? current.aspectRatio : defaultCreatorStyleForm.aspectRatio,
    }));
    setCreatorIdeaChatResults([]);
    setCreatorIdeaChatInput("");
    setCreatorIdeaChatOpen(false);
    setCreatorScriptRewritePrompt("");
    setCreatorStylePending("");
    setCreatorWorkflowStep(step);
    setCreatorWorkflowOpen(true);
  };

  const openCreatorIdeaChat = () => {
    setCreatorIdeaChatInput("");
    setCreatorIdeaChatResults([]);
    setCreatorIdeaChatOpen(true);
  };

  const closeCreatorIdeaChat = () => {
    if (creatorStylePending !== "ideas") {
      setCreatorIdeaChatOpen(false);
    }
  };

  const submitCreatorIdeaChat = async (event) => {
    event.preventDefault();
    const nextGoal = creatorIdeaChatInput.trim() || creatorStyleForm.goal || "lead more sales";
    setCreatorStyleForm((current) => ({
      ...current,
      goal: nextGoal,
    }));
    const workflow = await generateCreatorStyleIdeas({ goal: nextGoal });
    if (workflow?.ideas?.length) {
      setCreatorIdeaChatResults(workflow.ideas.slice(0, 2));
    }
  };

  const useCreatorIdeaPrompt = (idea) => {
    const prompt = [idea?.hook, idea?.angle].filter(Boolean).join(" ");
    setCreatorStyleForm((current) => ({
      ...current,
      prompt: prompt || current.prompt,
      selectedIdeaId: idea?.id || current.selectedIdeaId,
    }));
    setCreatorIdeaChatOpen(false);
    setCreatorWorkflowStep("style");
  };

  const applyCreatorScriptRewrite = () => {
    const rewritePrompt = creatorScriptRewritePrompt.trim();
    if (!rewritePrompt) {
      showAppToast("Describe the script change before applying a rewrite.");
      return;
    }
    setCreatorStyleForm((current) => ({
      ...current,
      prompt: `${current.prompt}\nRewrite request: ${rewritePrompt}`,
    }));
    setCreatorScriptRewritePrompt("");
    showAppToast("Script rewrite request added to the generation prompt.");
  };

  const stepCreatorWorkflowBack = () => {
    if (rawCreatorWorkflowStepIndex <= 0) {
      closeCreatorWorkflow();
      return;
    }
    const previousStep = creatorWorkflowSteps[rawCreatorWorkflowStepIndex - 1];
    setCreatorWorkflowStep(previousStep?.id || "prompt");
  };

  const continueCreatorWorkflow = async () => {
    if (!creatorCanContinue) {
      if (creatorWorkflowStep === "prompt") {
        showAppToast("Write a video idea and goal before continuing.");
      } else if (creatorWorkflowStep === "actor") {
        showAppToast("Select an AI actor before continuing.");
      } else if (creatorWorkflowStep === "template") {
        showAppToast("Select a scene/template before continuing.");
      } else {
        showAppToast("Complete this creator workflow step before continuing.");
      }
      return;
    }

    if (creatorWorkflowStep === "prompt") {
      if (!selectedCreatorIdeas.length) {
        const workflow = await generateCreatorStyleIdeas();
        if (!workflow?.ideas?.length) {
          return;
        }
      } else {
        setCreatorWorkflowStep("idea");
      }
      return;
    }

    if (creatorWorkflowStep === "confirm") {
      await generateCreatorStyleVideo();
      return;
    }

    const nextStep = creatorWorkflowSteps[rawCreatorWorkflowStepIndex + 1];
    if (nextStep?.id) {
      setCreatorWorkflowStep(nextStep.id);
    }
  };

  const submitCreateFlow = async () => {
    if (!activeCreateFormat) {
      showAppToast("Choose a format before generating.");
      return;
    }
    if (activeCreateFormat === "carousel") {
      setGenSelectedModel(carouselModel?.id || MINIMAX_CAROUSEL_MODEL_ID);
      selectModule("AI Studio");
      showAppToast("Carousel creation continues in AI Studio.");
      return;
    }
    if (activeCreateFormat === "ugc") {
      openCreatorWorkflow("prompt");
      return;
    }
    const format = createFormatCards.find((item) => item.id === activeCreateFormat) || createFormatCards[0];
    const method = createMethods.find(([id]) => id === activeCreateMethod) || createMethods[0];
    const promptParts = [
      `${format.title} ${format.format}`,
      `Source method: ${method[1]}`,
      activeCreateFormat === "carousel" ? `Carousel: ${carouselStyle}, ${carouselAspectRatio}` : "",
      `Offer: ${campaignInput.offer}`,
      `Goal: ${campaignInput.goal}`,
    ].filter(Boolean);
    startCooking("create-flow");
    try {
      const result = await createPhase3ContentBatch({
        sourcePrompt: promptParts.join(" | "),
        objective: campaignInput.goal,
      });
      await reloadPhase3Workspace({ silent: true });
      setAiResponse(
        `Created ${format.title} setup from ${method[1]}. Backend batch ${result?.batch?.id || ""} owns the generated records.`,
      );
      selectModule("Content Library");
      showAppToast(`${format.title} setup generated into Content Library.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Create flow generation failed.");
    }
  };

  const seedFromInspiration = async (item, sectionTitle) => {
    if (/UGC/i.test(sectionTitle) || /UGC|Voiceover/i.test(item.format || "")) {
      setCreatorStyleForm((current) => ({
        ...current,
        prompt: item.prompt,
        goal: campaignInput.goal,
        selectedIdeaId: "",
        styleId: "motivational",
        actorId: "",
        templateId: "",
        aspectRatio: "9:16",
      }));
      setActiveCreateFormat("ugc");
      selectModule("Create New");
      openCreatorWorkflow("prompt");
      showAppToast("Inspiration loaded into the creator-style video wizard.");
      return;
    }
    startCooking(`inspiration:${item.title}`);
    try {
      const result = await createPhase3ContentBatch({
        sourcePrompt: `${sectionTitle} inspiration: ${item.prompt}`,
        objective: campaignInput.goal,
      });
      await reloadPhase3Workspace({ silent: true });
      setAiResponse(
        `Recreated "${item.title}" as a LocalPilot local-business campaign. Backend batch ${result?.batch?.id || ""} keeps approval and proof hooks attached.`,
      );
      selectModule("Content Library");
      showAppToast("Inspiration recreated as a LocalPilot campaign.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Could not recreate inspiration.");
    }
  };

  const openLibraryDetail = (creative, index = 0) => {
    if (!creative?.id) {
      showAppToast("Choose a generated creative before previewing.");
      return;
    }
    setSelectedPost(index);
    setLibraryDetailCreativeId(creative.id);
  };

  const closeLibraryDetail = () => {
    setLibraryDetailCreativeId("");
  };

  const openPublishModal = (creative) => {
    if (!creative?.id) {
      showAppToast("Choose a generated creative before publishing.");
      return;
    }
    setLibraryDetailCreativeId("");
    setPublishDraft({
      creativeId: creative.id,
      platform: creative.platform === "facebook" ? "Facebook" : "Assisted Package",
      postType: /carousel/i.test(creative.format || "") ? "Carousel" : "Feed post",
      step: "platform",
      scheduleDay: 22,
      scheduleHour: "05",
      scheduleMinute: "15",
      scheduleMeridiem: "PM",
      aiSuggestedTime: false,
      approvalMember: false,
      confirmed: false,
    });
  };

  const updatePublishDraft = (field, value) => {
    setPublishDraft((current) => ({
      ...current,
      [field]: value,
      confirmed: false,
    }));
  };

  const closePublishModal = () => {
    setPublishDraft((current) => ({
      ...current,
      creativeId: "",
      step: "platform",
      confirmed: false,
    }));
  };

  const continuePublishSchedule = () => {
    if (!publishCanContinue) {
      showAppToast("Resolve the account or media compatibility warning before continuing.");
      return;
    }
    setPublishDraft((current) => ({
      ...current,
      step: "schedule",
      confirmed: false,
    }));
  };

  const schedulePublishPost = () => {
    setPublishDraft((current) => ({
      ...current,
      confirmed: true,
      step: "platform",
    }));
    showAppToast("Schedule confirmation saved as owner-approved weekly autoplan intent.");
    window.setTimeout(() => {
      closePublishModal();
      selectModule("Content Calendar");
    }, 650);
  };

  const saveSelectedFacebookPage = () => {
    const page =
      selectedFacebookPage ||
      pagePickerPages.find((item) => item.pageId === selectedFacebookPageId) ||
      pagePickerPages[0];
    if (!page) {
      showAppToast("Connect Facebook before saving a Page selection.");
      return;
    }
    updateFacebookPublishForm("pageId", page.pageId);
    showAppToast(`${page.name || "Facebook Page"} selected. Official publish still requires OAuth connection.`);
  };

  const submitHelpDraft = (event) => {
    event.preventDefault();
    const draft = helpDraft.trim();
    if (!draft) {
      showAppToast("Write a support message draft first.");
      return;
    }
    showAppToast("Message drafted locally. Nothing was sent.");
    setHelpDraft("");
  };

  const logout = async () => {
    try {
      await logoutSession();
    } catch {
      // best-effort
    }
    setSession(null);
    setAuthStatus("unauthenticated");
    navigate("/");
  };

  const selectModule = (module) => {
    const nextModule = moduleFromSlug(module) || module;
    setCalendarDrawerOpen(false);
    setHelpFlyoutOpen(false);
    setActiveModule(nextModule);
    navigate(`/app?module=${moduleSlug(nextModule)}`, { replace: true });
  };

  const openInspirationCollectionNudge = (sectionTitle) => {
    setPendingInspirationCollection(sectionTitle);
    setWaitNudgeOpen(true);
  };

  const continueInspirationAfterNudge = () => {
    const nextCollection = pendingInspirationCollection || "Trending collection";
    setActiveInspirationCollection(nextCollection);
    setActiveInspirationCategory("All");
    setPendingInspirationCollection("");
    setWaitNudgeOpen(false);
  };

  const closeInspirationNudge = () => {
    setPendingInspirationCollection("");
    setWaitNudgeOpen(false);
  };

  const downloadPostFromInspirationNudge = () => {
    setPendingInspirationCollection("");
    setWaitNudgeOpen(false);
    selectModule("Content Library");
    showAppToast("Content Library opened for download-ready posts.");
  };

  const toggleHelpFlyout = () => {
    setCalendarDrawerOpen(false);
    setHelpFlyoutOpen((current) => !current);
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
    selectModule("Create New");
    setSelectedPost(0);
    setSelectedChannel(0);
    setSelectedInbox(0);
    setSelectedWalkthrough(0);
    setQueuedPublishJobs({});
    await reloadWorkflow();
    await reloadPhase3Workspace();
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

  const approveSafeDrafts = async () => {
    const approvablePlans = plans.filter(
      (plan) => plan?.id && plan.currentVersion?.id && plan.status !== "Approved",
    );
    if (!approvablePlans.length) {
      showAppToast("All available drafts are already approved.");
      return;
    }

    setApprovalPending("batch");
    try {
      for (const plan of approvablePlans) {
        await approveDraftVersion(plan.id, {
          draftVersionId: plan.currentVersion.id,
          confirmation: "APPROVE_EXACT_VERSION",
          approver: {
            name: session?.name || "Karen Li",
            email: session?.email || "karen@example.com",
          },
          mediaRefs: plan.mediaRefs.map((media) => media.mediaAssetId),
        });
      }
      await reloadWorkflow({ silent: true });
      showAppToast(`${approvablePlans.length} exact draft versions approved for owner sign-off.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Approve-all failed.");
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

  const updateFacebookPublishForm = (field, value) => {
    setFacebookPublishForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateCompetitorSourceForm = (field, value) => {
    setCompetitorSourceForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateContentSourceForm = (field, value) => {
    setContentSourceForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateContentImageForm = (field, value) => {
    setContentImageForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const updateCreatorStyleForm = (field, value) => {
    setCreatorStyleForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const selectCreateFormat = (formatId) => {
    setActiveCreateFormat(formatId);
    if (formatId === "ugc") {
      openCreatorWorkflow("prompt");
    } else {
      setCreatorWorkflowOpen(false);
    }
  };

  const closeCreatorWorkflow = () => {
    setCreatorWorkflowOpen(false);
  };

  const openHelpAction = (title, body) => {
    setActiveHelpAction(title);
    setHelpDraft((current) => current || `Question about ${title}: ${body}`);
    showAppToast(`${title} loaded in the support panel.`);
  };

  const readContentImageFile = (event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    if (!file.type.startsWith("image/")) {
      showAppToast("Choose an image file for the source image import.");
      return;
    }
    if (file.size > 900_000) {
      showAppToast("Choose an image under 900 KB for this local demo import.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setContentImageForm((current) => ({
        ...current,
        fileName: file.name,
        mimeType: file.type,
        imageDataUrl: String(reader.result || ""),
      }));
    };
    reader.onerror = () => {
      showAppToast("Could not read that image file.");
    };
    reader.readAsDataURL(file);
  };

  const importContentSource = async (event) => {
    event.preventDefault();
    setContentSourcePending(true);
    try {
      const payload = await createPhase3ContentSource(contentSourceForm);
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      setContentSourceForm((current) => ({
        ...current,
        url: "",
      }));
      setAiResponse(
        `Imported source URL "${payload?.source?.label || "source page"}". I extracted a local offer brief, audience, proof point, and post angles for generation.`,
      );
      showAppToast("Source URL imported into the AI Generator.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Source URL import failed.");
    } finally {
      setContentSourcePending(false);
    }
  };

  const importContentImage = async (event) => {
    event.preventDefault();
    if (!contentImageForm.imageDataUrl) {
      showAppToast("Choose a source image before importing.");
      return;
    }
    setContentImagePending(true);
    try {
      const payload = await createPhase3ContentSource({
        sourceType: "image",
        ...contentImageForm,
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      setContentImageForm((current) => ({
        ...current,
        fileName: "",
        mimeType: "",
        imageDataUrl: "",
      }));
      event.currentTarget.reset();
      setAiResponse(
        `Imported source image "${payload?.source?.label || "source image"}". I extracted a visual brief, local proof point, and post angles for generation.`,
      );
      showAppToast("Source image imported into the AI Generator.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Source image import failed.");
    } finally {
      setContentImagePending(false);
    }
  };

  const generateFromContentSource = async (source) => {
    setSourceGenerationPending(source.id);
    startCooking(source.id);
    try {
      const brief = source.brief || {};
      const sourcePrompt = [
        brief.summary,
        brief.offer ? `Offer: ${brief.offer}` : "",
        brief.proofPoint ? `Proof: ${brief.proofPoint}` : "",
      ]
        .filter(Boolean)
        .join(" ");
      const result = await createPhase3ContentBatch({
        sourcePrompt: sourcePrompt || source.label,
        objective: campaignInput.goal,
      });
      await reloadPhase3Workspace({ silent: true });
      const sourceKind = source.sourceType === "image" ? "source image" : "source URL";
      setAiResponse(
        `Generated backend batch ${result?.batch?.id || ""} from ${sourceKind} "${source.label}". The calendar now has platform-native posts seeded from the imported brief.`,
      );
      showAppToast(`Generated a weekly batch from the imported ${sourceKind}.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Source-based generation failed.");
    } finally {
      setSourceGenerationPending("");
    }
  };

  const analyzeCompetitorSource = async (event) => {
    event.preventDefault();
    setCompetitorAnalysisPending(true);
    try {
      const payload = await createPhase3CompetitorSource(competitorSourceForm);
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      setCompetitorSourceForm((current) => ({
        ...current,
        url: "",
      }));
      showAppToast(`${payload?.ideas?.length || 0} competitor ideas generated from saved source.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Competitor analysis failed.");
    } finally {
      setCompetitorAnalysisPending(false);
    }
  };

  const connectFacebook = () => {
    if (!facebookConnection.configured) {
      showAppToast("Facebook OAuth is not configured. Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET on the backend.");
      return;
    }
    window.location.href = `/api/v1/facebook/oauth/start?returnTo=${encodeURIComponent(window.location.href)}`;
  };

  const openSocialDialog = (provider, mode) => {
    setSocialActionDialog({ provider, mode });
  };

  const closeSocialDialog = () => {
    setSocialActionDialog(null);
  };

  const handleSocialAdd = (platform) => {
    if (platform.provider === "Facebook") {
      connectFacebook();
      return;
    }
    openSocialDialog(platform.provider, "add");
  };

  const handleSocialConnectionChoice = (choice) => {
    showAppToast(`${socialActionDialog?.provider || "Account"} ${choice.title} connection path selected for demo setup.`);
    closeSocialDialog();
  };

  const publishFacebookLive = async (index) => {
    const plan = plans[index];
    if (plan?.platform !== "facebook") {
      showAppToast("Live publishing is available for Facebook drafts first.");
      return;
    }
    if (!plan?.approvalId || !plan.approvalSnapshot?.draftVersionId) {
      showAppToast("Approve this exact Facebook draft before publishing live.");
      return;
    }
    if (plan.publishJob?.id) {
      showAppToast(`${plan.name} publish timeline is already loaded.`);
      return;
    }

    const pageId = facebookPublishForm.pageId.trim();
    if (!facebookConnection.connectedPages.length) {
      showAppToast("Connect Facebook before publishing live.");
      return;
    }
    if (!pageId) {
      showAppToast("Choose a connected Facebook Page before publishing.");
      return;
    }

    const payload = {
      pageId,
      publishMode: facebookPublishForm.publishMode,
    };
    if (facebookPublishForm.publishMode === "schedule") {
      const scheduledAt = Math.floor(new Date(facebookPublishForm.scheduledPublishTime).getTime() / 1000);
      if (!Number.isFinite(scheduledAt)) {
        showAppToast("Choose a valid scheduled publish time.");
        return;
      }
      payload.scheduledPublishTime = String(scheduledAt);
    }

    setPublishPending(plan.id);
    try {
      const queued = await publishFacebookPost(plan.approvalId, payload);
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
      showAppToast("Facebook live publish completed. Post result is in the timeline.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Facebook live publish failed.");
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

  const addApprovalFeedback = async (index, feedbackType = "approval_note") => {
    const plan = plans[index];
    const creative = phase3CreativeForPlan(plan, index);
    if (!creative?.id) {
      showAppToast("Approval feedback needs a Phase 3 generated creative first.");
      return;
    }
    const isChangeRequest = feedbackType === "change_request";
    const pendingKey = `${creative.id}:${feedbackType}`;
    setApprovalFeedbackPending(pendingKey);
    try {
      const payload = await createPhase3ApprovalFeedback({
        creativeId: creative.id,
        feedbackType,
        authorName: isChangeRequest ? "Karen Li" : "LocalPilot reviewer",
        authorRole: isChangeRequest ? "owner" : "internal",
        body: isChangeRequest
          ? `${plan?.name || creative.platform} change request: revise the copy before final approval and keep claim-safe language.`
          : `${plan?.name || creative.platform} approval note: owner confirmed the CTA, proof hook, and schedule are ready for review.`,
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(
        isChangeRequest
          ? `${plan?.name || "Draft"} change request saved to the review link.`
          : `${plan?.name || "Draft"} approval note saved to the review link.`,
      );
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Approval feedback could not be saved.");
    } finally {
      setApprovalFeedbackPending("");
    }
  };

  const requestChanges = async (index) => {
    await addApprovalFeedback(index, "change_request");
  };

  const sendReviewNotification = async (index) => {
    const plan = plans[index];
    const creative = phase3CreativeForPlan(plan, index);
    if (!creative?.id) {
      showAppToast("Review notification needs a Phase 3 generated creative first.");
      return;
    }
    setReviewNotificationPending(creative.id);
    try {
      const payload = await createPhase3ReviewNotification({
        creativeId: creative.id,
        recipientName: "Karen Li",
        recipientContact: "karen@example.com",
        channel: "email",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`Review link sent to ${payload?.notification?.recipientContact || "client"}.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Review notification could not be sent.");
    } finally {
      setReviewNotificationPending("");
    }
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

  const submitPrompt = async (event) => {
    event.preventDefault();
    const prompt = new FormData(event.currentTarget).get("prompt")?.trim();
    startCooking("prompt");
    try {
      const result = await createPhase3ContentBatch({
        sourcePrompt: prompt || campaignInput.offer,
        objective: campaignInput.goal,
      });
      await reloadPhase3Workspace({ silent: true });
      setAiResponse(
        `Generated backend batch ${result?.batch?.id || ""} from "${prompt || campaignInput.offer}". I added branded post, carousel, reel script, schedule slots, approval notes, and proof hooks.`,
      );
      event.currentTarget.reset();
      showAppToast("AI Generator saved a backend weekly batch.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "AI batch generation failed.");
    }
  };

  const askAiAssistant = async (prompt) => {
    const normalizedPrompt = (prompt || assistantPrompt || "").trim();
    if (!normalizedPrompt) {
      showAppToast("Ask the AI Assistant for post ideas or a calendar outline first.");
      return;
    }
    setAssistantReplyPending("reply");
    try {
      const payload = await createPhase3AiAssistantReply({ prompt: normalizedPrompt });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      setAiResponse(payload?.reply?.replyText || "AI Assistant reply saved.");
      showAppToast("AI Assistant reply saved to backend.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "AI Assistant reply failed.");
    } finally {
      setAssistantReplyPending("");
    }
  };

  const submitAssistantPrompt = async (event) => {
    event.preventDefault();
    await askAiAssistant(assistantPrompt);
  };

  const createPostsFromAssistantReply = async (reply) => {
    if (!reply?.id) {
      showAppToast("Choose a saved AI Assistant reply first.");
      return;
    }
    setAssistantReplyPending(reply.id);
    startCooking(reply.id);
    try {
      const payload = await createPhase3ContentBatchFromReply(reply.id);
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      setAiResponse(
        `Created backend batch ${payload?.batch?.id || ""} from AI Assistant reply "${reply.prompt}".`,
      );
      showAppToast("Created posts from the AI Assistant reply.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Could not create posts from assistant reply.");
    } finally {
      setAssistantReplyPending("");
    }
  };

  const saveBrandKitCalibration = async () => {
    try {
      const nextVoice = {
        ...(phase3BrandKit.voice || {}),
        lastCalibration: "Applied to latest Predis-style weekly batch",
      };
      const payload = await updatePhase3BrandKit({
        voice: nextVoice,
        website: phase3BrandKit.website || "https://auroraheatcool.example",
        socialHandle: phase3BrandKit.socialHandle || "@auroraheatcool",
        hashtags: phase3BrandKit.hashtags || ["#AnnArbor", "#HVAC", "#LocalService"],
        typography: {
          ...(phase3BrandKit.typography || {}),
          title: phase3BrandKit.typography?.title || "Fraunces-style bold service headline",
          subtitle: phase3BrandKit.typography?.subtitle || "Readable sans caption for local offers",
        },
        logos: {
          ...(phase3BrandKit.logos || {}),
          light: phase3BrandKit.logos?.light || phase3BrandKit.logoRef || "localpilot-brand/aurora/logo.svg",
          dark: phase3BrandKit.logos?.dark || "localpilot-brand/aurora/logo-dark.svg",
        },
        integrations: phase3BrandKit.integrations || [
          { name: "Website URL", status: "available_demo" },
          { name: "CSV upload", status: "available_demo" },
          { name: "Odoo", status: "planned_localpilot_priority" },
        ],
        approvedTerms: phase3BrandKit.approvedTerms || ["same-week", "local team"],
      });
      setPhase3Workspace((current) => ({
        ...current,
        brandKit: payload?.brandKit || current.brandKit,
      }));
      showAppToast("Brand kit calibration saved to backend.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Brand kit save failed.");
    }
  };

  const generateIdeaLabVariants = async () => {
    if (!selectedPhase3Creative?.id) {
      showAppToast("Generate a backend creative before running Idea Lab scoring.");
      return;
    }
    setIdeaVariantPending("generate");
    try {
      const payload = await createPhase3IdeaVariants(selectedPhase3Creative.id, {
        objective: campaignInput.goal,
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${payload?.variants?.length || 0} AI-scored Idea Lab variants generated.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Idea Lab scoring failed.");
    } finally {
      setIdeaVariantPending("");
    }
  };

  const applyIdeaLabVariant = async (variant) => {
    if (!variant?.id) {
      showAppToast("Choose an Idea Lab variant before applying it.");
      return;
    }
    setIdeaVariantPending(variant.id);
    try {
      const payload = await applyPhase3IdeaVariant(variant.id);
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${variant.variantLabel || "Idea Lab variant"} applied to the backend creative.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Idea Lab variant apply failed.");
    } finally {
      setIdeaVariantPending("");
    }
  };

  const generateBulkVariations = async () => {
    if (!selectedPhase3Creative?.id) {
      showAppToast("Generate a backend creative before creating bulk variations.");
      return;
    }
    setBulkVariationPending(true);
    try {
      const payload = await createPhase3BulkVariations(selectedPhase3Creative.id, {
        objective: campaignInput.goal,
        count: 5,
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${payload?.variants?.length || 0} bulk creative variations generated.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Bulk creative variation generation failed.");
    } finally {
      setBulkVariationPending(false);
    }
  };

  const generateUgcVoiceoverPackage = async () => {
    if (!selectedPhase3Creative?.id) {
      showAppToast("Generate a backend creative before creating a UGC voiceover package.");
      return;
    }
    setUgcPackagePending(true);
    try {
      const payload = await createPhase3UgcVoiceoverPackage(selectedPhase3Creative.id, {
        packageLabel: "Owner explainer UGC package",
        language: "English",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${payload?.package?.packageLabel || "UGC voiceover package"} is storyboard-ready.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "UGC voiceover package generation failed.");
    } finally {
      setUgcPackagePending(false);
    }
  };

  const generateLanguageVariants = async () => {
    if (!selectedPhase3Creative?.id) {
      showAppToast("Generate a backend creative before creating multilingual variants.");
      return;
    }
    setLanguageVariantPending(true);
    try {
      const payload = await createPhase3LanguageVariants(selectedPhase3Creative.id, {
        targetLanguages: ["English", "Spanish", "Chinese"],
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${payload?.variants?.length || 0} multilingual creative variants generated.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Multilingual variant generation failed.");
    } finally {
      setLanguageVariantPending(false);
    }
  };

  const saveCreativeEdit = async () => {
    if (!selectedPhase3Creative?.id) {
      showAppToast("Generate a backend creative before saving editor changes.");
      return;
    }
    try {
      const payload = await updatePhase3Creative(selectedPhase3Creative.id, {
        title: `${safeText(selectedPhase3Creative?.title)} · edited`,
        caption: `${safeText(selectedPhase3Creative?.caption)} Owner-approved edit saved from Creative Editor.`,
        hashtags: [...(selectedPhase3Creative.hashtags || []), "#ownerapproved"],
        cta: safeText(selectedPhase3Creative?.cta),
        proofHook: safeText(selectedPhase3Creative?.proofHook),
        scheduleSlot: safeText(selectedPhase3Creative?.scheduleSlot, "Connected"),
        status: "needs_review",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast("Creative edit saved to backend.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Creative edit failed.");
    }
  };

  const saveCarouselSlideEdit = async () => {
    if (!activeCarouselAsset?.id) {
      showAppToast("Select a carousel slide before saving edits.");
      return;
    }
    const currentMetadata = activeCarouselAsset.metadata || {};
    const currentSlide = currentMetadata.carouselSlide || {};
    const nextComposedPayload = {
      ...(currentMetadata.composedPayload || {}),
      headline: carouselSlideDraft.headline,
      body: carouselSlideDraft.body,
      ctaLabel: carouselSlideDraft.ctaLabel,
      thumbnailRender: currentMetadata.composedPayload?.thumbnailRender || currentMetadata.composedPayload?.editorPreview || "",
      editorPreview: currentMetadata.composedPayload?.editorPreview || currentMetadata.composedPayload?.thumbnailRender || "",
    };
    setMediaAssetPending(activeCarouselAsset.id);
    try {
      const payload = await updatePhase3MediaAsset(activeCarouselAsset.id, {
        status: "edited_preview",
        metadata: {
          ...currentMetadata,
          composedPayload: nextComposedPayload,
          carouselSlide: {
            ...currentSlide,
            composedPayload: nextComposedPayload,
          },
        },
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast("Carousel slide edits saved to backend.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Carousel slide edit failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const saveMediaLayerEdit = async (asset) => {
    if (!asset?.id) {
      showAppToast("Select a generated media asset before saving a layer edit.");
      return;
    }
    setMediaAssetPending(asset.id);
    try {
      const payload = await updatePhase3MediaAsset(asset.id, {
        layerEdit: "Owner moved CTA above the proof hook and tightened safe-zone crop.",
        status: "edited_preview",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast("Media layer edit saved to backend.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Media layer edit failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const applyMediaLayerControl = async (asset, control) => {
    if (!asset?.id || !control?.id) {
      showAppToast("Select a generated media layer before applying a control edit.");
      return;
    }
    const pendingKey = `${asset.id}:layer:${control.id}`;
    const nextControl = layerControlEditForAsset(asset, control, selectedPhase3Creative);
    setMediaAssetPending(pendingKey);
    try {
      const payload = await updatePhase3MediaAsset(asset.id, {
        layerEdit: `${control.label || control.id} updated from layer controls.`,
        layerControl: {
          id: control.id,
          label: control.label || control.id,
          ...nextControl,
        },
        status: "edited_preview",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${control.label || "Layer"} control saved to backend.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Layer control edit failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const moveMediaLayer = async (asset, control, action = "move-down") => {
    if (!asset?.id || !control?.id) {
      showAppToast("Select a generated media layer before moving it.");
      return;
    }
    const pendingKey = `${asset.id}:layout:${control.id}`;
    const nextPlacement = action === "move-up" ? "top-center" : "bottom-center";
    setMediaAssetPending(pendingKey);
    try {
      const payload = await updatePhase3MediaLayerLayout(asset.id, {
        layerId: control.id,
        action,
        placement: nextPlacement,
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${control.label || "Layer"} layout moved in the backend editor.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Layer layout move failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const createMediaResizeVariant = async (asset) => {
    if (!asset?.id) {
      showAppToast("Select a generated media asset before creating a resize variant.");
      return;
    }
    setMediaAssetPending(`${asset.id}:variant`);
    try {
      const nextRatio = asset.aspectRatio === "9:16" ? "1:1" : "9:16";
      const payload = await createPhase3MediaVariant(asset.id, {
        aspectRatio: nextRatio,
        label: nextRatio === "9:16" ? "Story/Reel resize" : "Square feed resize",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`Resize variant created for ${nextRatio}.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Resize variant failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const renderMediaPreview = async (asset) => {
    if (!asset?.id) {
      showAppToast("Select a generated media asset before rendering a preview.");
      return;
    }
    setMediaAssetPending(`${asset.id}:render`);
    try {
      const payload = await renderPhase3MediaAsset(asset.id, {
        outputKind: "preview_svg",
        format: `${asset.format} customer preview`,
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast("Rendered preview artifact saved to backend.");
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Render preview failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const applyTemplateImport = async (template, assetLibraryItem = null) => {
    if (!selectedPhase3Creative?.id) {
      showAppToast("Select a backend creative before importing a template.");
      return;
    }
    if (!template?.id) {
      showAppToast("Select a template before importing.");
      return;
    }
    setMediaAssetPending(`template:${template.id}`);
    try {
      const payload = await createPhase3TemplateImport({
        creativeId: selectedPhase3Creative.id,
        templateId: template.id,
        assetLibraryItemId: assetLibraryItem?.id || "",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`${template.sourceProvider} template imported into Creative Editor.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Template import failed.");
    } finally {
      setMediaAssetPending("");
    }
  };

  const rescheduleSelectedCreative = async () => {
    if (!selectedPhase3Slot?.id) {
      showAppToast("Select a backend calendar slot before rescheduling.");
      return;
    }
    const nextSlot = selectedPhase3Slot.slotLabel === "Thursday 4:30 PM" ? "Saturday 10:00 AM" : "Thursday 4:30 PM";
    try {
      const payload = await updatePhase3CalendarSlot(selectedPhase3Slot.id, {
        slotLabel: nextSlot,
        status: "scheduled",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      }
      showAppToast(`Calendar slot moved to ${nextSlot}.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Calendar reschedule failed.");
    }
  };

  const recordProofEvent = async (label, creativeId = "") => {
    try {
      const payload = await recordPhase3ProofEvent({
        creativeId: creativeId || phase3Creatives[0]?.id,
        eventType: label.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "") || "manual_evidence",
        label,
        value: 1,
        source: "local_demo",
      });
      if (payload?.workspace) {
        setPhase3Workspace({
          ...emptyPhase3Workspace,
          ...payload.workspace,
        });
      } else {
        await reloadPhase3Workspace({ silent: true });
      }
      showAppToast(`${label} recorded as lower-bound proof evidence.`);
    } catch (error) {
      showAppToast(error instanceof Error ? error.message : "Proof event failed.");
    }
  };

  const activeInspirationSection =
    inspirationSections.find((section) => section.title === activeInspirationCollection) || null;

  if (authStatus === "loading") {
    return (
      <div className="app-shell" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
        <p>Loading…</p>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label="App navigation">
        <Link className="app-brand" to="/">
          <Brand />
        </Link>
        <div className="workspace-switcher">
          <span>Workspace</span>
          <strong>{session?.workspace || "Aurora demo brand"}</strong>
          <small>Logged-in reference clone</small>
        </div>
        <button className="sidebar-create-button" type="button" onClick={() => selectModule("Create New")}>
          <span>+</span>
          Create New
        </button>
        <nav className="app-nav" aria-label="Demo sections">
          {modules.map((module) => (
            <button
              className={`app-nav-item ${activeModule === module || (module === "Need help" && helpFlyoutOpen) ? "active" : ""}`}
              type="button"
              key={module}
              onClick={() => (module === "Need help" ? toggleHelpFlyout() : selectModule(module))}
            >
              <span aria-hidden="true">{moduleIcons[module] || "•"}</span>
              {module}
            </button>
          ))}
        </nav>
        {helpFlyoutOpen && (
          <section className="sidebar-help-flyout" aria-label="Need a hand quick help">
            <p>Need a hand?</p>
            <button
              type="button"
              onClick={() => {
                setActiveHelpAction("Chat support");
                showAppToast("Chat support selected. Main workspace stays open.");
              }}
            >
              <span aria-hidden="true">?</span>
              Chat Support
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveHelpAction("Book demo");
                showAppToast("Book a demo selected. No external send from this demo.");
              }}
            >
              <span aria-hidden="true">⌕</span>
              Book a Demo
            </button>
          </section>
        )}
        <div className="sidebar-card">
          <span>Trial account</span>
          <strong>{phase3Usage.planName || "Growth Demo"}</strong>
          <p>{phase3Usage.creditsUsed || 0}/{phase3Usage.monthlyCredits || 3200} credits used. Owner approval stays required before live publishing.</p>
          <button type="button" onClick={toggleHelpFlyout}>
            Need help
          </button>
        </div>
        <div className="sidebar-account">
          <span aria-hidden="true">H</span>
          <div>
            <strong>{campaignInput.business}</strong>
            <small>{session?.email || "huijiepan69@gmail.com"}</small>
          </div>
        </div>
      </aside>

      <main className={`app-main reference-workspace reference-${moduleSlug(activeModule)}`}>
        <header className="app-topbar">
          <div>
            <p className="app-kicker">Customer demo workspace</p>
            <h1>{onboardingRequired ? "Website onboarding" : config.title}</h1>
            <p className="topbar-summary">
              {onboardingRequired
                ? "Fetch your website, review the extracted brand draft, and confirm it before generation starts."
                : config.summary}
            </p>
          </div>
          <div className="topbar-actions">
            <LanguageToggle compact />
            {!onboardingRequired && (
              <>
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
              </>
            )}
            <button className="secondary-action" type="button" onClick={resetDemo}>
              Reset demo
            </button>
            <button className="icon-action" type="button" onClick={logout}>
              Log out
            </button>
          </div>
        </header>

        {onboardingRequired ? (
          <section className="onboarding-shell">
            <OnboardingCard
              onResolved={handleOnboardingResolved}
              onConfirmed={handleOnboardingConfirmed}
              showToast={showAppToast}
            />
          </section>
        ) : (
          <>
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
                <h2>{pageTitle}</h2>
                {pageSubtitle && <p className="panel-subtitle">{pageSubtitle}</p>}
              </div>
              {config.view === "library" && (
                <button
                  className="watermark-action"
                  type="button"
                  onClick={() => showAppToast("Remove Watermark is a LocalPilot usage-plan badge in this demo.")}
                >
                  Remove Watermark
                </button>
              )}
              {config.view === "calendar" && (
                <div className="segmented-control" aria-label="Calendar view">
                  <button type="button" onClick={() => showAppToast("Jumped to today's demo week.")}>
                    Today
                  </button>
                  {calendarViews.map((view) => (
                    <button
                      className={calendarView === view ? "active" : ""}
                      type="button"
                      key={view}
                      onClick={() => setCalendarView(view)}
                    >
                      {view}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {config.view === "create" && (
              <div className="create-workspace">
                <section className="create-hero">
                  <div>
                    <p className="app-kicker">Create Your Next Post</p>
                    <h2>Pick the format first, then choose the source method.</h2>
                    <p>
                      LocalPilot mirrors the logged-in Predis flow with six creation paths, then keeps
                      the result tied to owner approval, official account boundaries, and proof hooks.
                    </p>
                  </div>
                  <button className="primary-action" type="button" onClick={submitCreateFlow}>
                    {activeCreateFormat === "ugc" ? "Open creator workflow" : "Generate selected setup"}
                  </button>
                </section>
                {!activeCreateFormat && (
                  <section className="create-format-grid" aria-label="Create New format choices">
                    {createFormatCards.map((format) => (
                      <button
                        className={activeCreateFormat === format.id ? "active" : ""}
                        type="button"
                        key={format.id}
                        style={referencePreviewStyle(format.preview)}
                        onClick={() => selectCreateFormat(format.id)}
                      >
                        <span>{format.format}</span>
                        <strong>{format.title}</strong>
                        <small>{format.summary}</small>
                      </button>
                    ))}
                  </section>
                )}
                {activeCreateFormat === "image" && (
                  <section className="method-chooser" aria-label="Image and UGC creation methods">
                    <div>
                      <span>Creation method</span>
                      <h3>Create Image from a local source</h3>
                      <p>
                        These method choices map to safe source import flows. No login scraping, cookies,
                        or customer-pasted access tokens are used.
                      </p>
                    </div>
                    <div className="method-grid">
                      {createMethods.map(([id, title, body]) => (
                        <button
                          className={activeCreateMethod === id ? "active" : ""}
                          type="button"
                          key={id}
                          onClick={() => setActiveCreateMethod(id)}
                        >
                          <strong>{title}</strong>
                          <small>{body}</small>
                        </button>
                      ))}
                    </div>
                  </section>
                )}
                {activeCreateFormat === "ugc" && (
                  <section className="creator-workflow-launch" aria-label="Creator Style Video workflow launcher">
                    <span>Popup workflow</span>
                    <h3>Creator-style video opens in a focused modal.</h3>
                    <p>
                      Generate ideas, choose the script angle, style, AI actor, and subtitle style,
                      then create backend artifacts and hand off to Publish or Schedule Post.
                    </p>
                    <div className="creator-launch-steps">
                      {["Generate ideas", "Select idea", "Motivational style", "AI actor", "Subtitle style", "Generate", "Publish/Schedule"].map((step) => (
                        <span key={step}>{step}</span>
                      ))}
                    </div>
                    <button className="primary-action" type="button" onClick={() => openCreatorWorkflow("prompt")}>
                      Open workflow popup
                    </button>
                  </section>
                )}
                {activeCreateFormat === "carousel" && (
                  <section className="carousel-config-panel" aria-label="Carousel configuration">
                    <div>
                      <span>Carousel setup</span>
                      <h3>Open the canonical carousel flow in AI Studio.</h3>
                      <p>
                        Phase 11 uses one package-level carousel flow only: MiniMax default model, fixed 3:4,
                        five locked slides, and direct Creative Editor handoff.
                      </p>
                    </div>
                    <div className="carousel-style-grid carousel-canonical-grid">
                      <article className="carousel-canonical-card">
                        <strong>carousel_canonical_v1</strong>
                        <small>5 slides</small>
                        <p>cover -&gt; problem -&gt; proof -&gt; offer -&gt; CTA</p>
                        <em>Brand locked from saved kit · MiniMax default model · 3:4 portrait</em>
                      </article>
                    </div>
                    <article className="brand-confirmation-card">
                      <span>Brand linked</span>
                      <strong>{phase3BrandKit.voice?.tone || "trusted, prompt, local"}</strong>
                      <p>{(phase3BrandKit.approvedTerms || ["same-week", "local team"]).join(" · ")}</p>
                    </article>
                  </section>
                )}
                {activeCreateFormat && (
                  <div className="create-flow-footer">
                    <button className="secondary-action" type="button" onClick={() => setActiveCreateFormat("")}>
                      Back
                    </button>
                    <button className="primary-action" type="button" onClick={submitCreateFlow}>
                      {activeCreateFormat === "ugc" ? "Open workflow popup" : "Generate selected setup"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {config.view === "inspirations" && (
              <div className="inspiration-workspace">
                {!activeInspirationSection && (
                  <>
                    <section className="inspiration-page-head">
                      <h2>Inspirations</h2>
                    </section>
                    {inspirationSections.map((section) => (
                      <section className={`inspiration-section inspiration-${section.tone}`} key={section.title}>
                        <div className="inspiration-section-top">
                          <h3>{section.title}</h3>
                          <button
                            type="button"
                            onClick={() => openInspirationCollectionNudge(section.title)}
                          >
                            View all →
                          </button>
                        </div>
                        <div className="chip-row inspiration-chip-row" aria-label={`${section.title} categories`}>
                          {section.categories.map((category) => (
                            <button
                              className={activeInspirationCategory === category ? "active" : ""}
                              type="button"
                              key={category}
                              onClick={() => setActiveInspirationCategory(category)}
                            >
                              {category}
                            </button>
                          ))}
                        </div>
                        <div className="inspiration-grid">
                          {section.items.map((item) => (
                            <article key={`${section.title}-${item.title}`}>
                              <div className="inspiration-preview" style={referencePreviewStyle(item.preview)}>
                                <span>{item.format}</span>
                                <span>{item.badge}</span>
                              </div>
                              <button type="button" onClick={() => seedFromInspiration(item, section.title)}>
                                Recreate
                              </button>
                            </article>
                          ))}
                          <button
                            className="inspiration-view-all-overlay"
                            type="button"
                            onClick={() => openInspirationCollectionNudge(section.title)}
                          >
                            {section.viewAllLabel}
                          </button>
                        </div>
                      </section>
                    ))}
                  </>
                )}

                {activeInspirationSection && (
                  <section className="inspiration-collection-view">
                    <div className="inspiration-collection-head">
                      <button type="button" aria-label="Back to Inspirations" onClick={() => setActiveInspirationCollection("")}>
                        ←
                      </button>
                      <h2>{activeInspirationSection.title}</h2>
                      <label>
                        <span>⌕</span>
                        <input readOnly value={activeInspirationCategory === "All" ? "Travel inspirations" : `${activeInspirationCategory} inspirations`} />
                      </label>
                    </div>
                    <div className="chip-row inspiration-chip-row" aria-label={`${activeInspirationSection.title} filters`}>
                      {activeInspirationSection.categories.map((category) => (
                        <button
                          className={activeInspirationCategory === category ? "active" : ""}
                          type="button"
                          key={category}
                          onClick={() => setActiveInspirationCategory(category)}
                        >
                          {category}
                          {activeInspirationCategory === category && category !== "All" ? " ×" : ""}
                        </button>
                      ))}
                    </div>
                    <div className="inspiration-masonry">
                      {[...activeInspirationSection.items, ...inspirationSections.flatMap((section) => section.items).slice(0, 12)].map((item, index) => (
                        <article
                          className={index % 5 === 0 ? "tall" : index % 4 === 0 ? "short" : ""}
                          key={`${activeInspirationSection.title}-${item.title}-${index}`}
                        >
                          <div className="inspiration-preview" style={referencePreviewStyle(item.preview)}>
                            <span>{item.format}</span>
                            <span>{item.badge}</span>
                          </div>
                          <button type="button" onClick={() => seedFromInspiration(item, activeInspirationSection.title)}>
                            Recreate
                          </button>
                        </article>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            )}

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

                <section className="usage-credit-strip" aria-label="Predis-style usage summary">
                  <article>
                    <span>Plan</span>
                    <strong>{phase3Usage.planName || "Growth Demo"}</strong>
                    <p>{phase3Usage.creditsUsed || 0}/{phase3Usage.monthlyCredits || 3200} credits used</p>
                  </article>
                  <article>
                    <span>Brands</span>
                    <strong>{phase3Usage.brandsUsed || 1}/{phase3Usage.brandsLimit || 5}</strong>
                    <p>Brand kits for generation and publishing</p>
                  </article>
                  <article>
                    <span>Social accounts</span>
                    <strong>{phase3Usage.socialAccountsUsed || 0}/{phase3Usage.socialAccountsLimit || 10}</strong>
                    <p>Connected or assisted publishing channels</p>
                  </article>
                  <article>
                    <span>Competitor runs</span>
                    <strong>{phase3Usage.competitorRunsUsed || 0}/{phase3Usage.competitorRunsLimit || 60}</strong>
                    <p>Metered idea-lab analyses</p>
                  </article>
                </section>

                <section className="parity-channel-strip" aria-label="Predis parity channel map">
                  {predisParityChannels.map(([name, status, note]) => (
                    <article key={name}>
                      <span>{name}</span>
                      <strong>{status}</strong>
                      <p>{note}</p>
                    </article>
                  ))}
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
                        <strong>{safeText(channel.nativeCreative?.cover)}</strong>
                        <p>{safeText(channel.nativeCreative?.hook)}</p>
                        <small>{safeText(channel.nativeCreative?.cta)}</small>
                      </div>
                    </div>

                    <div className="channel-detail">
                      <div className="channel-heading">
                        <div>
                          <span>{channel.format}</span>
                        <h3>
                          {safeText(channel.name)}: {safeText(channel.role)}
                        </h3>
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
                        {channel.platform === "facebook" && channel.approvalSnapshot?.draftVersionId && !channel.publishJob?.id && (
                          <div className="facebook-live-publish" aria-label="Facebook live publish controls">
                            <label>
                              Connected Page
                              <select
                                value={facebookPublishForm.pageId}
                                onChange={(event) => updateFacebookPublishForm("pageId", event.target.value)}
                              >
                                {facebookConnection.connectedPages.length ? (
                                  facebookConnection.connectedPages.map((page) => (
                                    <option value={page.pageId} key={page.pageId}>
                                      {page.name || page.pageId}
                                    </option>
                                  ))
                                ) : (
                                  <option value={facebookPublishForm.pageId}>No Page connected</option>
                                )}
                              </select>
                            </label>
                            <label>
                              Mode
                              <select
                                value={facebookPublishForm.publishMode}
                                onChange={(event) => updateFacebookPublishForm("publishMode", event.target.value)}
                              >
                                <option value="publish_now">Publish now</option>
                                <option value="schedule">Schedule</option>
                              </select>
                            </label>
                            {facebookPublishForm.publishMode === "schedule" && (
                              <label>
                                Publish time
                                <input
                                  type="datetime-local"
                                  value={facebookPublishForm.scheduledPublishTime}
                                  onChange={(event) => updateFacebookPublishForm("scheduledPublishTime", event.target.value)}
                                />
                              </label>
                            )}
                            <button className="secondary-action" type="button" onClick={connectFacebook}>
                              {facebookConnection.connectedPages.length ? "Reconnect Facebook" : "Connect Facebook"}
                            </button>
                            <button
                              className="primary-action"
                              type="button"
                              disabled={publishPending === channel.id || !facebookConnection.connectedPages.length}
                              onClick={() => publishFacebookLive(safeSelectedChannel)}
                            >
                              Publish live
                            </button>
                          </div>
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
                        <dd>{safeText(channel.postAngle)}</dd>
                      </div>
                      <div>
                        <dt>Hook</dt>
                        <dd>{safeText(channel.nativeCreative?.hook)}</dd>
                      </div>
                      <div>
                        <dt>Caption</dt>
                        <dd>{safeText(channel.nativeCreative?.caption)}</dd>
                      </div>
                      <div>
                        <dt>CTA</dt>
                        <dd>{safeText(channel.nativeCreative?.cta)}</dd>
                      </div>
                      <div>
                        <dt>KPI</dt>
                        <dd>{safeText(channel.kpi)}</dd>
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
                          {channel.assets.map((asset, assetIndex) => (
                            <li key={displayItemKey(`${channel.id || channel.name}-asset`, asset, assetIndex)}>
                              {describeDisplayItem(asset)}
                            </li>
                          ))}
                        </ul>
                      </article>
                      <article>
                        <span>Tracking events</span>
                        <ul>
                          {channel.trackingEvents.map((eventName, eventIndex) => (
                            <li key={displayItemKey(`${channel.id || channel.name}-event`, eventName, eventIndex)}>
                              {describeDisplayItem(eventName)}
                            </li>
                          ))}
                        </ul>
                      </article>
                    </div>

                    <div className="why-row">
                      <article>
                        <span>Why this should work</span>
                        <p>{safeText(channel.whyItWorks)}</p>
                      </article>
                      <article>
                        <span>Owner action and risk check</span>
                        <p>{safeText(channel.ownerAction)}</p>
                        <small>{safeText(channel.riskNote)}</small>
                      </article>
                    </div>

                    <ul className="publish-checklist">
                      {channel.checklist.map((item, itemIndex) => (
                        <li key={stableNodeKey(item?.text, "channel-checklist-item", itemIndex)}>
                          <button
                            className={item.done ? "done" : ""}
                            type="button"
                            onClick={() => toggleChecklist(safeSelectedChannel, itemIndex)}
                          >
                            {safeChecklistText(item?.text)}
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

            {config.view === "brand" && (
              <div className="predis-surface">
                <section className="brand-kit-hero">
                  <div>
                    <p className="app-kicker">Brand kit</p>
                    <h2>{campaignInput.business} is ready for branded generation</h2>
                    <p>
                      This mirrors Predis brand management: business context, voice, colors, approved phrases,
                      and examples are applied before any post, carousel, or video script is generated.
                    </p>
                  </div>
                  <div className="brand-swatch-card">
                    <span>Palette</span>
                    <div className="brand-swatches" aria-label="Brand colors">
                      <i className="navy" />
                      <i className="blue" />
                      <i className="amber" />
                      <i className="paper" />
                    </div>
                    <strong>Trusted local service</strong>
                    <small>Server-owned profile, browser-safe preferences only</small>
                  </div>
                </section>
                <section className="brand-kit-grid">
                  {brandKitDisplayCards.map(([label, value, note]) => (
                    <article key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                      <p>{note}</p>
                    </article>
                  ))}
                </section>
                <section className="brand-voice-panel">
                  <div>
                    <span>Voice calibration</span>
                    <h3>Past posts and reviews become guardrails, not a generic prompt.</h3>
                    <p>
                      The demo keeps this deterministic for now, but the product seam is ready for LLM brand
                      voice learning from approved examples.
                    </p>
                  </div>
                  <button className="primary-action" type="button" onClick={saveBrandKitCalibration}>
                    Save backend calibration
                  </button>
                </section>
              </div>
            )}

            {config.view === "library" && (
              <div className="predis-surface">
                <section className="content-library-hero">
                  <div>
                    <p className="app-kicker">Content Library</p>
                    <h2>Central asset grid for generated posts, videos, and carousels.</h2>
                    <p>
                      Filter by type, source, tags, user, or archived state. Publishing stays gated
                      by media compatibility, connected accounts, and explicit owner approval.
                    </p>
                  </div>
                  <button className="primary-action" type="button" onClick={() => selectModule("Create New")}>
                    Create New
                  </button>
                </section>
                <section className="library-filter-panel" aria-label="Content Library filters">
                  <div className="type-tab-row" role="tablist" aria-label="Content type filters">
                    {contentTypeFilters.map((type) => (
                      <button
                        className={libraryFilters.type === type ? "active" : ""}
                        type="button"
                        role="tab"
                        aria-selected={libraryFilters.type === type}
                        key={type}
                        onClick={() => updateLibraryFilter("type", type)}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                  <label>
                    Search
                    <input
                      value={libraryFilters.search}
                      onChange={(event) => updateLibraryFilter("search", event.target.value)}
                      placeholder="Search captions, platform, or format"
                    />
                  </label>
                  <label>
                    Date
                    <select value={libraryFilters.date} onChange={(event) => updateLibraryFilter("date", event.target.value)}>
                      {["This week", "This month", "Last 90 days"].map((option) => (
                        <option key={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Tags
                    <input
                      value={libraryFilters.tags}
                      onChange={(event) => updateLibraryFilter("tags", event.target.value)}
                      placeholder="#local #offer"
                    />
                  </label>
                  <label>
                    Users
                    <select value={libraryFilters.users} onChange={(event) => updateLibraryFilter("users", event.target.value)}>
                      {["All users", "Karen Li", "LocalPilot AI"].map((option) => (
                        <option key={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Created from
                    <select
                      value={libraryFilters.createdFrom}
                      onChange={(event) => updateLibraryFilter("createdFrom", event.target.value)}
                    >
                      {libraryCreatedFromOptions.map((option) => (
                        <option key={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                  <label className="archive-toggle">
                    <input
                      type="checkbox"
                      checked={libraryFilters.archived}
                      onChange={(event) => updateLibraryFilter("archived", event.target.checked)}
                    />
                    Show archived
                  </label>
                </section>
                <section className="content-card-grid" aria-label="Filtered Content Library cards">
                  {(filteredLibraryCreatives.length ? filteredLibraryCreatives : phase3Creatives).slice(0, 8).map((creative, index) => {
                    const mediaAsset = creative.mediaAssets?.[0];
                    const previewImage = creativePreviewImage(creative, index);
                    const typeBlob = [
                      creative.format,
                      creative.platform,
                      creative.title,
                      creative.caption,
                      mediaAsset?.assetType,
                      mediaAsset?.format,
                      mediaAsset?.aspectRatio,
                    ]
                      .filter(Boolean)
                      .join(" ")
                      .toLowerCase();
                    const isVideoCard = /video|ugc|reel|storyboard|tiktok|9:16/.test(typeBlob);
                    const isCooking = cookingCreativeId === creative.id;
                    return (
                      <article
                        key={creative.id}
                        className={[
                          selectedPhase3Creative?.id === creative.id ? "active" : "",
                          isVideoCard ? "video-card" : "",
                        ]
                          .filter(Boolean)
                          .join(" ")}
                        style={referencePreviewStyle(previewImage)}
                      >
                        <div className="content-card-preview">
                          {isVideoCard && (
                            <>
                              <button
                                className="library-edit-pencil"
                                type="button"
                                aria-label={`Edit ${creative.title}`}
                                onClick={() => openLibraryDetail(creative, index)}
                              >
                                ✎
                              </button>
                              <button
                                className="library-play-button"
                                type="button"
                                aria-label={`Preview ${creative.title}`}
                                onClick={() => openLibraryDetail(creative, index)}
                              >
                                ▶
                              </button>
                            </>
                          )}
                          <span>{creative.format || mediaAsset?.format || "Local post"}</span>
                          <strong>{creative.platform?.replace(/_/g, " ") || "platform"}</strong>
                          <small>{mediaAsset?.aspectRatio || "1:1"} · {creative.status}</small>
                          {isCooking && (
                            <div className="cooking-overlay">
                              <strong>Great things take time — your content is cooking!</strong>
                              <small>Backend record creation remains authoritative.</small>
                            </div>
                          )}
                        </div>
                        <div>
                          <span>{(creative.hashtags || []).slice(0, 2).join(" ")}</span>
                          <strong>{safeText(creative.title)}</strong>
                          <p>{safeText(creative.caption)}</p>
                        </div>
                        <div className="library-card-actions">
                          <button type="button" onClick={() => setSelectedPost(index)}>
                            Edit
                          </button>
                          <button type="button" onClick={() => openPublishModal(creative)}>
                            Publish
                          </button>
                          <button type="button" onClick={() => showAppToast("Remove Watermark is a LocalPilot usage-plan badge in this demo.")}>
                            Remove Watermark
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </section>
                <section className="creative-editor-hero">
                  <div>
                    <p className="app-kicker">Creative editor</p>
                    <h2>Post, carousel, and reel previews from the same local idea</h2>
                    <p>
                      Predis parity means the customer sees generated creative formats, not just captions.
                      LocalPilot adds proof hooks and approval checks to every format.
                    </p>
                  </div>
                  <button className="primary-action" type="button" onClick={generateIdeaLabVariants} disabled={ideaVariantPending === "generate"}>
                    {ideaVariantPending === "generate" ? "Scoring variants..." : "Generate variants"}
                  </button>
                </section>
                <div className="creative-format-grid">
                  {creativeFormats.map((item) => (
                    <article key={item.format}>
                      <span>Format</span>
                      <strong>{item.format}</strong>
                      <p>{item.description}</p>
                    </article>
                  ))}
                </div>
                {selectedPlan && (
                  <section className={`creative-editor-card ${selectedPlan.tone}`}>
                    <div className="creative-canvas">
                      {isCarouselEditor && activeCarouselAsset ? (
                        <div className="carousel-editor-shell">
                          <aside className="carousel-slide-rail">
                            {selectedCarouselAssets.map((asset, index) => {
                              const slide = asset.metadata?.carouselSlide || {};
                              const preview = asset.metadata?.composedPayload?.thumbnailRender;
                              return (
                                <button
                                  type="button"
                                  key={asset.id}
                                  className={asset.id === activeCarouselAsset.id ? "active" : ""}
                                  onClick={() => setSelectedCarouselSlideId(asset.id)}
                                >
                                  <span>{index + 1}</span>
                                  {preview ? <img src={preview} alt={`${slide.role || "slide"} thumbnail`} /> : <strong>{slide.role || `Slide ${index + 1}`}</strong>}
                                  <small>{slide.role || `Slide ${index + 1}`}</small>
                                </button>
                              );
                            })}
                          </aside>
                          <div className="carousel-slide-canvas">
                            {activeCarouselPayload.editorPreview ? (
                              <img src={activeCarouselPayload.editorPreview} alt={`${activeCarouselPayload.layout?.role || "carousel"} preview`} />
                            ) : (
                              <img src={selectedPlan.asset} alt={`${selectedPlan.name} creative mockup`} />
                            )}
                            <div>
                              <span>{activeCarouselPayload.layout?.role || "carousel slide"}</span>
                              <strong>{safeText(activeCarouselPayload.headline, safeText(selectedPlan.nativeCreative?.cover))}</strong>
                              <p>{safeText(activeCarouselPayload.body, safeText(selectedPlan.nativeCreative?.hook))}</p>
                              {activeCarouselPayload.ctaLabel && <small>{activeCarouselPayload.ctaLabel}</small>}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <>
                          <img src={selectedPlan.asset} alt={`${selectedPlan.name} creative mockup`} />
                          <div>
                            <span>{selectedPlan.name}</span>
                            <strong>{safeText(selectedPlan.nativeCreative?.cover)}</strong>
                            <p>{safeText(selectedPlan.nativeCreative?.hook)}</p>
                          </div>
                        </>
                      )}
                    </div>
                    <div className="creative-fields">
                      {selectedPhase3Creative && (
                        <div className="backend-record-pill">
                          <span>Backend creative</span>
                          <strong>{selectedPhase3Creative.platform} · {selectedPhase3Creative.format}</strong>
                          <small>{selectedPhase3Creative.id}</small>
                        </div>
                      )}
                      {isCarouselEditor && activeCarouselAsset && (
                        <section className="carousel-slide-inspector" aria-label="Carousel slide inspector">
                          <div>
                            <span>Slide-locked Creative Editor</span>
                            <strong>Five slides stay in order with brand lock enabled</strong>
                            <p>
                              Edit headline, body, and CTA only. Aspect ratio, preset, logo placement,
                              slide count, and brand styling stay fixed for this package.
                            </p>
                          </div>
                          <label>
                            Headline
                            <input
                              type="text"
                              value={carouselSlideDraft.headline}
                              onChange={(event) => setCarouselSlideDraft((current) => ({ ...current, headline: event.target.value }))}
                            />
                          </label>
                          <label>
                            Body
                            <textarea
                              value={carouselSlideDraft.body}
                              onChange={(event) => setCarouselSlideDraft((current) => ({ ...current, body: event.target.value }))}
                            />
                          </label>
                          <label>
                            CTA
                            <input
                              type="text"
                              value={carouselSlideDraft.ctaLabel}
                              onChange={(event) => setCarouselSlideDraft((current) => ({ ...current, ctaLabel: event.target.value }))}
                            />
                          </label>
                          <div className="media-asset-actions carousel-inspector-actions">
                            <button
                              type="button"
                              disabled={mediaAssetPending === activeCarouselAsset.id}
                              onClick={saveCarouselSlideEdit}
                            >
                              {mediaAssetPending === activeCarouselAsset.id ? "Saving slide..." : "Save slide edits"}
                            </button>
                          </div>
                        </section>
                      )}
                      {!isCarouselEditor && (
                      <section className="idea-lab-panel" aria-label="Idea Lab AI scoring">
                        <div>
                          <span>Idea Labs</span>
                          <strong>AI-scored messaging variations</strong>
                          <p>
                            Generate multiple creative angles, score them against the campaign objective,
                            then apply the best-performing hook and CTA back to the backend creative.
                          </p>
                        </div>
                        <button
                          type="button"
                          disabled={ideaVariantPending === "generate"}
                          onClick={generateIdeaLabVariants}
                        >
                          {ideaVariantPending === "generate" ? "Scoring..." : "Generate AI-scored variants"}
                        </button>
                        <div className="idea-variant-grid" aria-label="Scored Idea Lab variants">
                          {(selectedPhase3Creative?.ideaVariants || []).slice(0, 4).map((variant) => (
                            <article className={variant.status === "applied" ? "applied" : ""} key={variant.id}>
                              <span>{variant.status}</span>
                              <strong>{variant.variantLabel}</strong>
                              <div className="idea-score">
                                <b>{variant.score}</b>
                                <small>AI score</small>
                              </div>
                              <p>{safeText(variant.hook)}</p>
                              <small>{variant.scoreBreakdown?.rationale}</small>
                              <button
                                type="button"
                                disabled={ideaVariantPending === variant.id}
                                onClick={() => applyIdeaLabVariant(variant)}
                              >
                                {ideaVariantPending === variant.id ? "Applying..." : "Apply winner"}
                              </button>
                            </article>
                          ))}
                        </div>
                      </section>
                      )}
                      {!isCarouselEditor && (
                      <section className="bulk-variation-panel" aria-label="Bulk creative variations">
                        <div>
                          <span>Bulk variations</span>
                          <strong>Test hooks, copy, and visuals</strong>
                          <p>
                            Predis-style bulk generation for customer demos: create multiple ready-to-test
                            directions from one approved local offer without changing the owner approval boundary.
                          </p>
                        </div>
                        <button
                          type="button"
                          disabled={bulkVariationPending}
                          onClick={generateBulkVariations}
                        >
                          {bulkVariationPending ? "Generating bulk..." : "Generate bulk variations"}
                        </button>
                        <div className="bulk-variation-grid" aria-label="Ready-to-test bulk variations">
                          {selectedPhase3BulkVariants.slice(0, 6).map((variant) => (
                            <article key={variant.id}>
                              <span>{variant.status}</span>
                              <strong>{variant.variantLabel}</strong>
                              <div className="idea-score">
                                <b>{variant.score}</b>
                                <small>test score</small>
                              </div>
                              <p>{safeText(variant.hook)}</p>
                              <small>{variant.format}</small>
                              <em>{variant.visualDirection}</em>
                            </article>
                          ))}
                        </div>
                      </section>
                      )}
                      {!isCarouselEditor && (
                      <section className="ugc-package-panel" aria-label="UGC voiceover packages">
                        <div>
                          <span>UGC voiceover</span>
                          <strong>Avatar-ready video package</strong>
                          <p>
                            Predis-style UGC/video-with-voiceover package adapted for owner-approved
                            local posts: avatar, script, scenes, captions, and export spec.
                          </p>
                        </div>
                        <button
                          type="button"
                          disabled={ugcPackagePending}
                          onClick={generateUgcVoiceoverPackage}
                        >
                          {ugcPackagePending ? "Building package..." : "Generate UGC voiceover package"}
                        </button>
                        <div className="ugc-package-grid" aria-label="Storyboard-ready UGC packages">
                          {selectedPhase3UgcPackages.slice(0, 3).map((ugcPackage) => (
                            <article key={ugcPackage.id}>
                              <span>{ugcPackage.status}</span>
                              <strong>{ugcPackage.packageLabel}</strong>
                              <p>
                                {ugcPackage.avatar?.type} · {ugcPackage.avatar?.ethnicity}
                              </p>
                              <small>
                                {ugcPackage.voiceover?.tone} · {ugcPackage.voiceover?.durationSeconds}s ·{" "}
                                {ugcPackage.voiceover?.language}
                              </small>
                              <ul>
                                {(ugcPackage.scenes || []).slice(0, 3).map((scene, index) => (
                                  <li key={displayItemKey(ugcPackage.id, scene, index)}>
                                    {describeDisplayItem(scene)}
                                  </li>
                                ))}
                              </ul>
                              <em>
                                {ugcPackage.exportSpec?.format} · {ugcPackage.exportSpec?.resolution} ·{" "}
                                {ugcPackage.exportSpec?.frameRate}
                              </em>
                            </article>
                          ))}
                        </div>
                      </section>
                      )}
                      {!isCarouselEditor && (
                      <section className="language-variant-panel" aria-label="Multilingual creative variants">
                        <div>
                          <span>Multilingual variants</span>
                          <strong>Switch output language in two clicks</strong>
                          <p>
                            Predis-style multilingual generation adapted for local organic posts:
                            keep the same offer, proof hook, and owner approval flow while creating localized copy.
                          </p>
                        </div>
                        <button
                          type="button"
                          disabled={languageVariantPending}
                          onClick={generateLanguageVariants}
                        >
                          {languageVariantPending ? "Localizing..." : "Generate multilingual variants"}
                        </button>
                        <div className="language-variant-grid" aria-label="Localized creative copy">
                          {selectedPhase3LanguageVariants.slice(0, 6).map((variant) => (
                            <article key={variant.id}>
                              <span>{variant.languageCode} · {variant.status}</span>
                              <strong>{variant.languageLabel}</strong>
                              <p>{variant.localizedTitle}</p>
                              <small>{variant.localizedCaption}</small>
                              <em>{variant.localizedCta}</em>
                              <small>{(variant.localizedHashtags || []).join(" ")}</small>
                            </article>
                          ))}
                        </div>
                      </section>
                      )}
                      {!isCarouselEditor && (
                      <section className="template-import-panel" aria-label="Template import and asset library">
                        <div>
                          <span>Template import</span>
                          <strong>Canva, Figma, Adobe-style templates</strong>
                          <p>
                            Predis-style template reuse with backend-owned imports, custom template refs,
                            and premium-safe asset choices.
                          </p>
                        </div>
                        {phase3ImportedTemplates.length > 0 && (
                          <div className="imported-template-strip" aria-label="Imported templates">
                            {phase3ImportedTemplates.slice(0, 3).map((item) => (
                              <small key={item.id}>
                                Imported {item.sourceProvider} · {item.status}
                              </small>
                            ))}
                          </div>
                        )}
                        <div className="template-card-grid">
                          {phase3CreativeTemplates.slice(0, 3).map((template, index) => {
                            const pairedAsset = phase3AssetLibraryItems[index % Math.max(phase3AssetLibraryItems.length, 1)];
                            return (
                              <article key={template.id}>
                                <span>{template.sourceProvider}</span>
                                <strong>{template.title}</strong>
                                <p>{template.format} · {template.aspectRatio} · {template.category}</p>
                                <small>{pairedAsset?.title || "No premium asset selected"}</small>
                                <em>{template.previewRef}</em>
                                <button
                                  type="button"
                                  disabled={mediaAssetPending === `template:${template.id}`}
                                  onClick={() => applyTemplateImport(template, pairedAsset)}
                                >
                                  {mediaAssetPending === `template:${template.id}` ? "Importing..." : "Import template"}
                                </button>
                              </article>
                            );
                          })}
                        </div>
                        <div className="asset-library-strip" aria-label="Premium asset library">
                          <span className="asset-library-heading">Premium asset library</span>
                          {phase3AssetLibraryItems.slice(0, 3).map((item) => (
                            <article key={item.id}>
                              <span>{item.kind}</span>
                              <strong>{item.title}</strong>
                              <small>{item.provider} · {item.license}</small>
                              <p>{item.fitNotes}</p>
                            </article>
                          ))}
                        </div>
                      </section>
                      )}
                      <section className="media-asset-panel" aria-label="Generated media assets">
                        <span>Generated media assets</span>
                        {selectedPhase3MediaAssets.length ? (
                          isCarouselEditor ? (
                            selectedCarouselAssets.map((asset, index) => (
                              <article key={asset.id} className="carousel-slide-asset-card">
                                <div>
                                  <strong>Slide {index + 1} · {asset.metadata?.carouselSlide?.role}</strong>
                                  <small>{asset.assetType} · {asset.aspectRatio} · {asset.status}</small>
                                </div>
                                {asset.metadata?.composedPayload?.thumbnailRender && (
                                  <img src={asset.metadata.composedPayload.thumbnailRender} alt={`${asset.metadata?.carouselSlide?.role || "carousel"} thumbnail`} />
                                )}
                                <p>{safeText(asset.metadata?.composedPayload?.headline)}</p>
                                <small>{safeText(asset.metadata?.composedPayload?.body)}</small>
                                <em>{safeText(asset.metadata?.composedPayload?.ctaLabel || "No CTA on this slide")}</em>
                              </article>
                            ))
                          ) : (
                          selectedPhase3MediaAssets.map((asset) => (
                            <article key={asset.id}>
                              <div>
                                <strong>{asset.format}</strong>
                                <small>{asset.assetType} · {asset.aspectRatio} · {asset.status}</small>
                              </div>
                              <p>{safeText(asset.prompt, asset.format || "Generated media asset")}</p>
                              <ul>
                                {mediaAssetHighlights(asset).slice(0, 3).map((item, index) => (
                                  <li key={displayItemKey(`${asset.id}-highlight`, item, index)}>
                                    {describeDisplayItem(item)}
                                  </li>
                                ))}
                              </ul>
                              {asset.metadata?.lastLayerEdit && (
                                <small>Last layer edit: {asset.metadata.lastLayerEdit}</small>
                              )}
                              {asset.metadata?.resizeVariant && (
                                <small>Resize variant from {asset.metadata.sourceAssetId}</small>
                              )}
                              {Array.isArray(asset.metadata?.layerControls) && asset.metadata.layerControls.length > 0 && (
                                <div className="layer-control-list" aria-label={`${asset.format} layer controls`}>
                                  <span>Layer controls</span>
                                  {asset.metadata.layerControls.slice(0, 4).map((control) => (
                                    <section key={control.id}>
                                      <div>
                                        <strong>{control.label}</strong>
                                        <small>
                                          {safeText(control.placement)} · {safeText(control.style)} · {safeText(control.status)}
                                        </small>
                                        {control.layout && (
                                          <small>
                                            Layer order {safeText(control.layout.order)} · x{safeText(control.layout.x)}% y
                                            {safeText(control.layout.y)}% · w{safeText(control.layout.width)}%
                                          </small>
                                        )}
                                        <em>{safeText(control.value)}</em>
                                      </div>
                                      <div className="layer-control-actions">
                                        <button
                                          type="button"
                                          disabled={mediaAssetPending === `${asset.id}:layout:${control.id}`}
                                          onClick={() => moveMediaLayer(asset, control)}
                                        >
                                          {mediaAssetPending === `${asset.id}:layout:${control.id}` ? "Moving..." : "Move layer"}
                                        </button>
                                        <button
                                          type="button"
                                          disabled={mediaAssetPending === `${asset.id}:layer:${control.id}`}
                                          onClick={() => applyMediaLayerControl(asset, control)}
                                        >
                                          {mediaAssetPending === `${asset.id}:layer:${control.id}` ? "Applying..." : "Apply layer edit"}
                                        </button>
                                      </div>
                                    </section>
                                  ))}
                                </div>
                              )}
                              {Array.isArray(asset.renderedOutputs) && asset.renderedOutputs.length > 0 && (
                                <div className="rendered-output-list">
                                  {asset.renderedOutputs.slice(0, 2).map((output) => (
                                    <section key={output.id}>
                                      {output.previewDataUrl && (
                                        <img src={output.previewDataUrl} alt={`${asset.format} rendered preview`} />
                                      )}
                                      <div>
                                        <strong>{output.format}</strong>
                                        <small>{output.outputKind} · {output.mimeType} · {output.status}</small>
                                        <em>{output.storageRef}</em>
                                      </div>
                                    </section>
                                  ))}
                                </div>
                              )}
                              <div className="media-asset-actions">
                                <button
                                  type="button"
                                  disabled={mediaAssetPending === asset.id}
                                  onClick={() => saveMediaLayerEdit(asset)}
                                >
                                  {mediaAssetPending === asset.id ? "Saving layer..." : "Save layer edit"}
                                </button>
                                <button
                                  type="button"
                                  disabled={mediaAssetPending === `${asset.id}:variant`}
                                  onClick={() => createMediaResizeVariant(asset)}
                                >
                                  {mediaAssetPending === `${asset.id}:variant` ? "Creating resize..." : "Create resize variant"}
                                </button>
                                <button
                                  type="button"
                                  disabled={mediaAssetPending === `${asset.id}:render`}
                                  onClick={() => renderMediaPreview(asset)}
                                >
                                  {mediaAssetPending === `${asset.id}:render` ? "Rendering..." : "Render preview"}
                                </button>
                              </div>
                              <em>{asset.storageRef}</em>
                            </article>
                          ))
                          )
                        ) : (
                          <p>Generate a backend weekly batch to create image, carousel, or video storyboard assets.</p>
                        )}
                      </section>
                      <label>
                        Caption
                        <textarea
                          readOnly
                          value={safeText(
                            selectedPhase3Creative?.caption,
                            safeText(selectedPlan.nativeCreative?.caption),
                          )}
                        />
                      </label>
                      <label>
                        Hashtags
                        <input
                          readOnly
                          value={(selectedPhase3Creative?.hashtags || ["#localbusiness", "#annarbor"]).join(" ")}
                        />
                      </label>
                      <label>
                        Proof hook
                        <input
                          readOnly
                          value={safeText(
                            selectedPhase3Creative?.proofHook,
                            `${safeText(selectedPlan.nativeCreative?.cta)} -> tracked link / QR / event`,
                          )}
                        />
                      </label>
                      <div className="calendar-actions">
                        <button type="button" onClick={() => approvePlan(safeSelectedPost)}>
                          Approve exact version
                        </button>
                        <button type="button" onClick={saveCreativeEdit}>
                          Save backend edit
                        </button>
                        <button type="button" onClick={() => requestChanges(safeSelectedPost)}>
                          Request rewrite
                        </button>
                      </div>
                    </div>
                  </section>
                )}
              </div>
            )}

            {config.view === "autopost" && (
              <div className="autopost-workspace">
                <section className="autopost-hero">
                  <div>
                    <p className="app-kicker">Auto Posting</p>
                    <h2>Weekly local autoplan, never autonomous publishing.</h2>
                    <p>
                      The logged-in reference flow upsells auto-posting after scheduling. LocalPilot
                      reframes that as a weekly plan that still requires owner approval before any official publish request.
                    </p>
                  </div>
                  <button className="primary-action" type="button" onClick={() => selectModule("Content Calendar")}>
                    Review schedule
                  </button>
                </section>
                <section className="autopost-grid">
                  {[
                    ["Plan cadence", "Weekly", "Generate a fresh local campaign batch from the active offer."],
                    ["Approval gate", "Required", "No live request is sent before exact owner sign-off."],
                    ["Facebook", "Official first", "OAuth Page publish remains the first production path."],
                    ["TikTok/GBP", "Assisted", "Unsupported channels become safe handoff packages."],
                  ].map(([label, value, note]) => (
                    <article key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                      <p>{note}</p>
                    </article>
                  ))}
                </section>
                <section className="autopost-timeline" aria-label="Owner-approved autoplan steps">
                  {[
                    "Generate weekly batch",
                    "Owner reviews exact posts",
                    "Compatible Facebook posts publish through OAuth",
                    "Assisted packages export for unsupported channels",
                    "Proof hooks collect lower-bound response evidence",
                  ].map((step, index) => (
                    <article key={step}>
                      <span>Step {index + 1}</span>
                      <strong>{step}</strong>
                    </article>
                  ))}
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

                <section className="calendar-toolbar" aria-label="Calendar controls">
                  <div className="calendar-month-nav" aria-label="Calendar month navigation">
                    <button type="button" onClick={() => showAppToast("Previous month is disabled in this seeded demo.")}>
                      ‹
                    </button>
                    <strong>June 2026</strong>
                    <button type="button" onClick={() => showAppToast("Next month is disabled in this seeded demo.")}>
                      ›
                    </button>
                  </div>
                </section>

                <div className="calendar-weekdays" aria-label="Calendar weekdays">
                  {calendarWeekdays.map((day) => (
                    <span key={day}>{day}</span>
                  ))}
                </div>

                <div className={`calendar-board calendar-board--${calendarView.toLowerCase()}`}>
                  {Array.from({ length: 42 }).map((_, index) => {
                    const dayLabel = index === 0 ? "31" : index <= 30 ? String(index) : String(index - 30);
                    const planIndexByCell = {
                      8: 0,
                      12: 1,
                      18: 2,
                      24: 3,
                      30: 4,
                    };
                    const planIndex = planIndexByCell[index];
                    const plan = typeof planIndex === "number" ? plans[planIndex % plans.length] : null;
                    const slot = plan ? phase3CalendarSlots[planIndex % Math.max(phase3CalendarSlots.length, 1)] : null;
                    const creativeForSlot =
                      slot?.creativeId
                        ? phase3Creatives.find((creative) => creative.id === slot.creativeId)
                        : phase3Creatives[planIndex % Math.max(phase3Creatives.length, 1)];
                    const calendarPreviewImage = creativeForSlot ? creativePreviewImage(creativeForSlot, planIndex) : "";
                    const scheduledTime =
                      planIndex === 0 ? "8:05 AM" : planIndex === 1 ? "5:15 PM" : slot?.slotLabel || "10:00 AM";
                    return (
                      <button
                        className={`calendar-day ${plan ? `has-post ${plan.tone}` : ""} ${safeSelectedPost === planIndex ? "active" : ""}`}
                        type="button"
                        key={`calendar-cell-${index}`}
                        onClick={() => {
                          if (plan) {
                            setSelectedPost(planIndex);
                            setCalendarDrawerOpen(true);
                            if (slot?.id) {
                              setSelectedCalendarSlotId(slot.id);
                            }
                          }
                        }}
                      >
                        <span>{dayLabel}</span>
                        {plan && (
                          <div className="calendar-post-card">
                            <div className="calendar-post-thumb" style={referencePreviewStyle(calendarPreviewImage)}>
                              <i>{creativeForSlot?.mediaAssets?.[0]?.aspectRatio || plan.nativeCreative.size}</i>
                              <strong>{creativeForSlot?.platform?.replace(/_/g, " ") || plan.name}</strong>
                            </div>
                            <small><b /> {scheduledTime}</small>
                            <em>f</em>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>

                <section className="calendar-footer" aria-label="Calendar legend and timezone">
                  <div className="calendar-legend" aria-label="Calendar status legend">
                    {calendarLegend.map((status) => (
                      <span key={status}>{status}</span>
                    ))}
                  </div>
                  <label>
                    Select Timezone
                    <select value={selectedTimezone} onChange={(event) => setSelectedTimezone(event.target.value)}>
                      {["America/Detroit", "Browser local", "America/New_York", "America/Chicago"].map((timezone) => (
                        <option key={timezone}>{timezone}</option>
                      ))}
                    </select>
                  </label>
                </section>

                {selectedPlan ? (
                  <article className="selected-post selected-post--calendar">
                    <div className="selected-post-copy">
                      <span className="status-pill">{safeText(selectedPlan.status)}</span>
                      <h3>
                        {safeText(selectedPlan.name)}: {safeText(selectedPlan.publishingMode)}
                      </h3>
                      <p>{safeText(selectedPlan.nativeCreative?.caption)}</p>
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
                        {selectedPlan.platform === "facebook" && selectedPlan.approvalSnapshot?.draftVersionId && !selectedPlan.publishJob?.id && (
                          <div className="facebook-live-publish facebook-live-publish--compact">
                            <select
                              value={facebookPublishForm.pageId}
                              onChange={(event) => updateFacebookPublishForm("pageId", event.target.value)}
                            >
                              {facebookConnection.connectedPages.length ? (
                                facebookConnection.connectedPages.map((page) => (
                                  <option value={page.pageId} key={page.pageId}>
                                    {page.name || page.pageId}
                                  </option>
                                ))
                              ) : (
                                <option value={facebookPublishForm.pageId}>No Page connected</option>
                              )}
                            </select>
                            <button type="button" onClick={connectFacebook}>
                              {facebookConnection.connectedPages.length ? "Reconnect Facebook" : "Connect Facebook"}
                            </button>
                            <button
                              type="button"
                              disabled={publishPending === selectedPlan.id || !facebookConnection.connectedPages.length}
                              onClick={() => publishFacebookLive(safeSelectedPost)}
                            >
                              Publish live
                            </button>
                          </div>
                        )}
                        <button type="button" onClick={() => requestChanges(safeSelectedPost)}>
                          Request edit
                        </button>
                        <button type="button" onClick={rescheduleSelectedCreative}>
                          Reschedule backend slot
                        </button>
                      </div>
                      <div className="selected-checklist">
                        <span>Before publishing</span>
                        <ul>
                          {selectedPlan.checklist.map((item, itemIndex) => (
                            <li
                              key={stableNodeKey(item?.text, "selected-plan-checklist-item", itemIndex)}
                              className={item.done ? "done" : ""}
                            >
                              {safeChecklistText(item?.text)}
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
                {calendarDrawerOpen && activeCalendarSlot && (
                  <aside className="calendar-detail-drawer" aria-label="Scheduled post detail drawer">
                    <button className="drawer-close" type="button" onClick={() => setCalendarDrawerOpen(false)}>
                      Close
                    </button>
                    <div>
                      <span>Scheduled post detail drawer · {calendarView}</span>
                      <h3>{activeCalendarSlot.platform?.replace(/_/g, " ") || selectedPlan?.name || "Scheduled post"}</h3>
                      <p>{activeCalendarSlot.slotLabel || selectedPlan?.scheduleSlot}</p>
                    </div>
                    <div className="drawer-preview-card">
                      <strong>{safeText(selectedPhase3Creative?.title, safeText(selectedPlan?.nativeCreative?.cover))}</strong>
                      <p>{safeText(selectedPhase3Creative?.caption, safeText(selectedPlan?.nativeCreative?.caption))}</p>
                      <small>{activeCalendarSlot.status || selectedPlan?.status} · {selectedTimezone}</small>
                    </div>
                    <div className="locked-state-copy">
                      <strong>Locked near publish</strong>
                      <p>Edits close to publish require discard or reschedule so the owner approves the exact final version.</p>
                    </div>
                    <div className="calendar-actions">
                      <button type="button" onClick={() => showAppToast("Demo slot discarded locally. Backend discard status is a production hardening item.")}>
                        Discard
                      </button>
                      <button type="button" onClick={rescheduleSelectedCreative}>
                        Reschedule
                      </button>
                    </div>
                  </aside>
                )}
              </div>
            )}

            {config.view === "approvals" && (
              <div className="predis-surface">
                <section className="approval-command-panel">
                  <div>
                    <p className="app-kicker">Approval queue</p>
                    <h2>{pendingPlans.length} drafts need owner review</h2>
                    <p>
                      This is the 1% better layer: automated posting is not trusted until the owner approves
                      the exact version that will be published.
                    </p>
                  </div>
                  <button
                    className="primary-action"
                    type="button"
                    disabled={approvalPending === "batch"}
                    onClick={approveSafeDrafts}
                  >
                    Approve all safe drafts
                  </button>
                </section>
                <section className="approval-queue-grid">
                  {plans.map((plan, index) => {
                    const reviewCreative = phase3CreativeForPlan(plan, index);
                    const reviewLink =
                      (reviewCreative && approvalReviewLinksByCreativeId[reviewCreative.id]) || reviewCreative?.reviewLink;
                    const reviewFeedback =
                      (reviewCreative && approvalFeedbackByCreativeId[reviewCreative.id]) || reviewCreative?.approvalFeedback || [];
                    const reviewNotifications =
                      (reviewCreative && reviewNotificationsByCreativeId[reviewCreative.id]) ||
                      reviewCreative?.reviewNotifications ||
                      [];
                    const lastNotification = reviewNotifications[0];
                    const feedbackPendingKey = reviewCreative ? `${reviewCreative.id}:approval_note` : "";
                    const changePendingKey = reviewCreative ? `${reviewCreative.id}:change_request` : "";
                    return (
                      <article key={`${plan.id || plan.name}-approval`} className={plan.status === "Approved" ? "approved" : ""}>
                        <div>
                          <span>{plan.name}</span>
                          <strong>{safeText(plan.nativeCreative?.hook)}</strong>
                          <p>{safeText(plan.nativeCreative?.caption)}</p>
                        </div>
                        <dl>
                          <div>
                            <dt>Status</dt>
                            <dd>{plan.status}</dd>
                          </div>
                          <div>
                            <dt>Version</dt>
                            <dd>v{plan.currentVersion?.versionNumber || 1}</dd>
                          </div>
                          <div>
                            <dt>Proof hook</dt>
                            <dd>{plan.trackingEvents.map(describeDisplayItem).filter(Boolean).join(", ")}</dd>
                          </div>
                        </dl>
                        <div className="approval-feedback-panel">
                          <span>Share review link</span>
                          <input readOnly value={reviewLink?.reviewUrl || "Generating review link from backend workspace"} />
                          <div className="approval-notification-strip">
                            <strong>{lastNotification ? "Review link sent" : "Not sent yet"}</strong>
                            <small>
                              {lastNotification
                                ? `${lastNotification.channel} · ${lastNotification.recipientContact} · ${lastNotification.status}`
                                : "Create a backend outbox record before asking the client to review."}
                            </small>
                          </div>
                          <div className="approval-feedback-list">
                            {reviewFeedback.slice(0, 2).map((feedback) => (
                              <article key={feedback.id}>
                                <strong>{feedback.feedbackType.replace(/_/g, " ")}</strong>
                                <p>{feedback.body}</p>
                                <small>
                                  {feedback.authorName} · {feedback.status}
                                </small>
                              </article>
                            ))}
                            {!reviewFeedback.length && (
                              <article>
                                <strong>No feedback yet</strong>
                                <p>Share the link, then keep owner comments and approval notes attached to this post.</p>
                              </article>
                            )}
                          </div>
                        </div>
                        <div className="calendar-actions">
                          <button
                            type="button"
                            disabled={approvalPending === plan.id || plan.status === "Approved"}
                            onClick={() => approvePlan(index)}
                          >
                            Approve exact version
                          </button>
                          <button
                            type="button"
                            disabled={approvalFeedbackPending === feedbackPendingKey}
                            onClick={() => addApprovalFeedback(index, "approval_note")}
                          >
                            Add approval note
                          </button>
                          <button
                            type="button"
                            disabled={reviewNotificationPending === reviewCreative?.id}
                            onClick={() => sendReviewNotification(index)}
                          >
                            Send review link
                          </button>
                          <button
                            type="button"
                            disabled={approvalFeedbackPending === changePendingKey}
                            onClick={() => requestChanges(index)}
                          >
                            Request changes
                          </button>
                        </div>
                      </article>
                    );
                  })}
                </section>
              </div>
            )}

            {config.view === "accounts" && (
              <div className="predis-surface">
                <section className="accounts-hero">
                  <div>
                    <p className="app-kicker">Brand & Social Accounts</p>
                    <h2>Clickable auth, brand details, style, integrations, and exports.</h2>
                    <p>
                      Predis parity needs an account and brand hub. LocalPilot keeps the secure boundary explicit:
                      users click OAuth to grant access, and provider credentials stay server-side.
                    </p>
                  </div>
                  <button className="primary-action" type="button" onClick={connectFacebook}>
                    {facebookConnection.connectedPages.length ? "Reconnect Facebook" : "Connect Facebook"}
                  </button>
                </section>
                <div className="brand-account-tabs" role="tablist" aria-label="Brand and social account sections">
                  {brandAccountTabs.map((tab) => (
                    <button
                      className={activeBrandAccountTab === tab ? "active" : ""}
                      type="button"
                      role="tab"
                      aria-selected={activeBrandAccountTab === tab}
                      key={tab}
                      onClick={() => setActiveBrandAccountTab(tab)}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
                {activeBrandAccountTab === "Social Platforms" && (
                  <section className="account-grid social-platform-grid">
                    {socialPlatformRows.map((platform) => (
                      <article className={platform.provider === "Facebook" ? "expanded" : ""} key={platform.provider}>
                        <div className={`social-platform-icon ${platform.tone}`}>{platform.icon}</div>
                        <div className="social-platform-copy">
                          <strong>{platform.provider}</strong>
                          <p>{platform.accountType}</p>
                        </div>
                        <div className="social-platform-actions">
                          {platform.watch && (
                            <button type="button" onClick={() => openSocialDialog(platform.provider, "video")}>
                              <span className="social-action-icon">▦</span>
                              Watch Videos
                            </button>
                          )}
                          <button type="button" onClick={() => openSocialDialog(platform.provider, "faq")}>
                            <span className="social-action-icon">?</span>
                            FAQ
                          </button>
                          <button type="button" onClick={() => handleSocialAdd(platform)}>
                            Add
                          </button>
                        </div>
                        {platform.provider === "Facebook" && (
                          <div className="social-connected-card">
                            <div className="social-connected-avatar">●</div>
                            <strong>{selectedFacebookPage?.name || campaignInput.business}</strong>
                            <small>{selectedFacebookPage?.pageId || "1243605852158721_"}</small>
                            <button type="button" onClick={() => showAppToast("Demo unlink keeps OAuth tokens server-side.")}>
                              Unlink
                            </button>
                          </div>
                        )}
                      </article>
                    ))}
                  </section>
                )}
                {activeBrandAccountTab === "Social Platforms" && (
                  <section className="facebook-page-picker social-platform-admin-panel" aria-label="Facebook Page selection modal" hidden>
                    <div>
                      <span>Facebook Page selection</span>
                      <h3>Choose the Page LocalPilot should use after OAuth.</h3>
                      <p>
                        The cards mirror the logged-in Page picker. Demo cards are placeholders until a real
                        OAuth callback returns manageable Pages.
                      </p>
                    </div>
                    <div className="page-card-grid">
                      {pagePickerPages.map((page) => (
                        <button
                          className={(selectedFacebookPageId || pagePickerPages[0]?.pageId) === page.pageId ? "active" : ""}
                          type="button"
                          key={page.pageId}
                          onClick={() => setSelectedFacebookPageId(page.pageId)}
                        >
                          <strong>{page.name || page.pageId}</strong>
                          <span>{page.category || "Facebook Page"}</span>
                          <small>{(page.tasks || []).join(" · ") || "Page permissions pending"}</small>
                        </button>
                      ))}
                    </div>
                    <div className="permission-health-card">
                      <span>Permission health</span>
                      <strong>{facebookConnection.configured ? "OAuth configured" : "Backend env required"}</strong>
                      <p>
                        Required scopes: {(facebookConnection.scopes || []).join(", ") || "pages_show_list, pages_read_engagement, pages_manage_posts"}.
                      </p>
                      <small>{facebookConnection.redirectUri || "Backend callback not loaded"}</small>
                    </div>
                    <button className="primary-action" type="button" onClick={saveSelectedFacebookPage}>
                      Save selected Page
                    </button>
                  </section>
                )}
                {activeBrandAccountTab === "Brand Details" && (
                  <section className="brand-details-workspace" aria-label="Brand Details">
                    <nav className="brand-details-inner-nav" aria-label="Brand Details sections">
                      {brandDetailSections.map((section) => (
                        <button
                          className={activeBrandDetailSection === section ? "active" : ""}
                          type="button"
                          key={section}
                          onClick={() => setActiveBrandDetailSection(section)}
                        >
                          {section}
                        </button>
                      ))}
                    </nav>
                    <div className="brand-details-main">
                      {activeBrandDetailSection === "Business identity" && (
                        <div className="brand-identity-panel">
                          <h3>Business identity</h3>
                          <div className="brand-details-form">
                            {[
                              ["Business name", campaignInput.business],
                              ["Business description", phase3BrandKit.voice?.promise || "Local team with honest recommendations and fast scheduling."],
                              ["Website", phase3BrandKit.website || "https://auroraheatcool.example"],
                              ["Social handle", phase3BrandKit.socialHandle || "@auroraheatcool"],
                              ["Hashtags", (phase3BrandKit.hashtags || ["#AnnArbor", "#HVAC", "#LocalService"]).join(" ")],
                            ].map(([label, value]) => (
                              <label key={label}>
                                {label}
                                <input readOnly value={value} />
                              </label>
                            ))}
                            <button className="secondary-action" type="button" onClick={() => showAppToast("Website fetch demo uses the existing source URL import boundary.")}>
                              Fetch details from website
                            </button>
                          </div>
                        </div>
                      )}

                      {activeBrandDetailSection === "Style" && (
                        <div className="brand-style-panel">
                          <div className="brand-style-preview-row" aria-hidden="true">
                            <i />
                            <i />
                          </div>
                          <p>
                            Note: Not all templates will adapt well to the brand colors. It is possible that a
                            creative template might lose its sheen because of color/font change.
                          </p>
                          <div className="brand-style-grid" aria-label="Brand Style">
                            {[
                              ["Title typography", phase3BrandKit.typography?.title || "Fraunces-style bold service headline"],
                              ["Subtitle typography", phase3BrandKit.typography?.subtitle || "Clean sans caption for readable local offers"],
                              ["Light logo", phase3BrandKit.logos?.light || phase3BrandKit.logoRef || "localpilot-brand/aurora/logo.svg"],
                              ["Dark logo", phase3BrandKit.logos?.dark || "localpilot-brand/aurora/logo-dark.svg"],
                            ].map(([label, value]) => (
                              <article key={label}>
                                <span>{label}</span>
                                <strong>{value}</strong>
                              </article>
                            ))}
                            <article className="brand-color-control">
                              <span>Font colors</span>
                              <div className="brand-swatches" aria-label="Brand font colors">
                                {(phase3BrandKit.colors || ["#172033", "#2563eb", "#f4a62a", "#fff7e8"]).map((color) => (
                                  <i style={{ background: color }} key={color} />
                                ))}
                              </div>
                            </article>
                          </div>
                        </div>
                      )}

                      {activeBrandDetailSection === "Content settings" && (
                        <div className="brand-content-settings">
                          <div className="brand-style-preview-row" aria-hidden="true">
                            <i />
                            <i />
                          </div>
                          <p>
                            Note: Not all templates will adapt well to the brand colors. It is possible that a
                            creative template might lose its sheen because of color/font change.
                          </p>
                          <h3>Content settings</h3>
                          <div className="brand-content-form">
                            <label>
                              Tonality of Communication
                              <select defaultValue="">
                                <option value="" disabled>Select tonality</option>
                                <option>Motivational</option>
                                <option>Helpful expert</option>
                                <option>Friendly local</option>
                              </select>
                            </label>
                            <label>
                              Select Timezone
                              <select value={selectedTimezone} onChange={(event) => setSelectedTimezone(event.target.value)}>
                                <option value="America/Detroit">(GMT -4:00) America/Detroit</option>
                                <option value="America/New_York">(GMT -4:00) America/New_York</option>
                                <option value="America/Chicago">(GMT -5:00) America/Chicago</option>
                              </select>
                            </label>
                            <label>
                              Brand Ethnicity
                              <select defaultValue="">
                                <option value="" disabled>Select Ethnicity</option>
                                <option>Local market neutral</option>
                                <option>Inclusive small business</option>
                              </select>
                            </label>
                            <label>
                              Brand Voiceover <span aria-label="Voiceover info">ⓘ</span>
                              <select defaultValue="">
                                <option value="" disabled>Select Voiceover</option>
                                <option>Warm owner voice</option>
                                <option>Clear service narrator</option>
                              </select>
                              <small>Used in all voiceover videos.</small>
                            </label>
                          </div>
                          <h3>AI Media</h3>
                          <div className="brand-content-form">
                            <label>
                              Brand Avatar
                              <small>Used in UGC style Videos. each avatar will speak using this voice.</small>
                              <select defaultValue="">
                                <option value="" disabled>Select Avatar</option>
                                <option>Owner-style avatar</option>
                                <option>Service expert avatar</option>
                              </select>
                            </label>
                          </div>
                        </div>
                      )}

                      <div className="brand-details-save">
                        <button type="button" onClick={saveBrandKitCalibration}>
                          Save Changes
                        </button>
                      </div>
                    </div>
                  </section>
                )}
                {activeBrandAccountTab === "Integrations" && (
                  <section className="integrations-reference-panel" aria-label="Integrations">
                    <div className="integrations-copy">
                      <h3>Integrations</h3>
                      <p>Connect your online store and link your products.</p>
                    </div>
                    <div className="integration-trust-grid" aria-label="Integration trust signals">
                      {integrationTrustCards.map((card) => (
                        <article key={card.title}>
                          <span>{card.icon}</span>
                          <strong>{card.title}</strong>
                          <p>{card.detail}</p>
                        </article>
                      ))}
                    </div>
                    <div className="ecommerce-connector-grid" aria-label="E-commerce platform connectors">
                      {ecommerceConnectors.map((connector) => (
                        <article key={connector.name}>
                          <span className={`ecommerce-icon ${connector.tone}`}>{connector.icon}</span>
                          <strong>{connector.name}</strong>
                          <button type="button" onClick={() => showAppToast(`${connector.name} connect is demo-safe and keeps credentials server-side.`)}>
                            Connect
                          </button>
                        </article>
                      ))}
                    </div>
                    <div className="integration-or-separator">
                      <span>or</span>
                    </div>
                    <div className="other-ecommerce-head">
                      <h3>Other E-Commerce Platforms</h3>
                      <button type="button" onClick={exportPackage}>
                        Download Sample
                      </button>
                    </div>
                    <button
                      className="ecommerce-upload-dropzone"
                      type="button"
                      onClick={() => showAppToast("CSV upload demo uses the existing source import boundary.")}
                    >
                      <span>☁</span>
                      <strong>
                        Click to upload <em>or drag and drop</em>
                      </strong>
                      <small>Upload any e-commerce store's product csv to create posts for them.</small>
                    </button>
                  </section>
                )}
                {activeBrandAccountTab === "Exports" && (
                  <section className="exports-panel export-table-panel" aria-label="Exports">
                    <div className="exports-table-copy">
                      <h3>Exports</h3>
                      <p>View, download, and reuse all the posts you've created.</p>
                    </div>
                    <div className="exports-table" role="table" aria-label="Created post exports">
                      <div className="exports-table-head" role="row">
                        <span role="columnheader">Description</span>
                        <span role="columnheader">Dimension</span>
                        <span role="columnheader">Status</span>
                        <span role="columnheader" aria-label="Download action" />
                      </div>
                      {brandExportRows.map((row) => (
                        <div className="exports-table-row" role="row" key={row.id}>
                          <div className="export-description-cell" role="cell">
                            <img src={row.preview} alt="" />
                            <strong>{row.title}</strong>
                          </div>
                          <span role="cell">{row.dimension}</span>
                          <span role="cell">{row.status}</span>
                          <button type="button" aria-label={`Download ${row.title}`} onClick={exportPackage}>
                            ⇩
                          </button>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>
            )}

            {config.view === "ideas" && (
              <div className="predis-surface">
                <section className="competitor-link-gate" aria-label="Competitor Analysis account link gate">
                  <div className="competitor-link-copy">
                    <h2>Please link Your Accounts to start using Competitor Analysis</h2>
                    <p>
                      Competitor Analysis needs Facebook and Instagram API access to work. Please give
                      access to all facebook pages to authorise API access.
                    </p>
                  </div>
                  <article className="competitor-link-account">
                    <div>
                      <strong>Instagram - Business or Creator Account</strong>
                      <p>Must be connected via Facebook Page for competitor analysis to work</p>
                      <span>Facebook connection required</span>
                    </div>
                    <button
                      className="competitor-link-button"
                      type="button"
                      onClick={() => {
                        setActiveBrandAccountTab("Social Platforms");
                        selectModule("Brand & Social Accounts");
                        openSocialDialog("Instagram", "add");
                      }}
                    >
                      Link now
                    </button>
                  </article>
                </section>

                <section className="competitor-advanced-panel" aria-label="LocalPilot competitor analysis advanced panel">
                  <div>
                    <p className="app-kicker">LocalPilot advanced demo</p>
                    <h3>Analyze a saved source after account linking is ready</h3>
                    <p>
                      This preserves the backend competitor-source workflow, but the first screen now
                      matches the reference account-link gate.
                    </p>
                  </div>
                  <form className="competitor-source-form" onSubmit={analyzeCompetitorSource}>
                    <input
                      aria-label="Competitor source label"
                      value={competitorSourceForm.label}
                      onChange={(event) => updateCompetitorSourceForm("label", event.target.value)}
                      placeholder="Source label"
                    />
                    <input
                      aria-label="Competitor profile URL"
                      value={competitorSourceForm.url}
                      onChange={(event) => updateCompetitorSourceForm("url", event.target.value)}
                      placeholder="Paste competitor profile or Page URL"
                    />
                    <button className="primary-action" type="submit" disabled={competitorAnalysisPending}>
                      {competitorAnalysisPending ? "Analyzing..." : "Analyze"}
                    </button>
                  </form>
                  <section className="competitor-source-list" aria-label="Saved competitor sources">
                    {phase3CompetitorSources.map((source) => (
                      <article key={source.id}>
                        <span>{source.status}</span>
                        <strong>{source.label}</strong>
                        <p>{source.url}</p>
                      </article>
                    ))}
                  </section>
                  <section className="idea-card-grid">
                    {(phase3Ideas.length ? phase3Ideas : competitorIdeas).map((idea) => (
                      <article key={idea.id || safeText(idea.hook, "idea")}>
                        <span>{idea.source || idea.confidence || "Demo competitor pattern"}</span>
                        <strong>{idea.theme}</strong>
                        <p>{safeText(idea.hook)}</p>
                        <small>{idea.timing}</small>
                        <em>{Array.isArray(idea.hashtags) ? idea.hashtags.join(" ") : idea.hashtags}</em>
                      </article>
                    ))}
                  </section>
                </section>
              </div>
            )}

            {config.view === "ai" && (
              <div className="ai-studio">
                <section className="ai-command-grid">
                  {aiStudioTasks.map(([action, title, body]) => (
                    <button type="button" key={title} onClick={() => askAiAssistant(title)} disabled={assistantReplyPending === "reply"}>
                      <span>{action}</span>
                      <strong>{title}</strong>
                      <small>{body}</small>
                    </button>
                  ))}
                </section>
                <div className="ai-thread">
                  <article>
                    <span>AI Generator</span>
                    <p>
                      Build a week of Predis-style posts for {campaignInput.business} using the offer "{campaignInput.offer}".
                      Make each channel native, branded, approval-ready, and measurable.
                    </p>
                  </article>
                  <article className="ai-answer">
                    <span>LocalPilot AI</span>
                    <p>{aiResponse}</p>
                  </article>
                </div>
                <section className="assistant-reply-panel" aria-label="AI Assistant replies">
                  <div>
                    <span>In-built AI chat</span>
                    <strong>Ask for post ideas, then create posts with one click</strong>
                    <p>
                      Predis-style assistant replies are saved by the backend. Use a reply as the input
                      for a new weekly content batch when the idea is ready.
                    </p>
                  </div>
                  <form className="assistant-prompt-form" onSubmit={submitAssistantPrompt}>
                    <input
                      aria-label="AI Assistant prompt"
                      value={assistantPrompt}
                      onChange={(event) => setAssistantPrompt(event.target.value)}
                      placeholder="Ask for post ideas or a content calendar outline..."
                    />
                    <button className="primary-action" type="submit" disabled={assistantReplyPending === "reply"}>
                      {assistantReplyPending === "reply" ? "Asking..." : "Ask AI Assistant"}
                    </button>
                  </form>
                  <div className="assistant-reply-list" aria-label="Saved AI Assistant replies">
                    {phase3AssistantReplies.slice(0, 3).map((reply) => (
                      <article key={reply.id}>
                        <span>{reply.status}</span>
                        <strong>{reply.prompt}</strong>
                        <p>{reply.replyText}</p>
                        <ul>
                          {(reply.outline || []).slice(0, 3).map((item) => (
                            <li key={`${reply.id}-${item.day}`}>
                              {item.day}: {item.postIdea}
                            </li>
                          ))}
                        </ul>
                        <button
                          className="secondary-action"
                          type="button"
                          disabled={assistantReplyPending === reply.id}
                          onClick={() => createPostsFromAssistantReply(reply)}
                        >
                          {assistantReplyPending === reply.id ? "Creating..." : "Create posts from reply"}
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
                <section className="source-import-panel" aria-label="Source URL import">
                  <div>
                    <span>Source URL import</span>
                    <strong>Turn a local offer page into social posts</strong>
                    <p>
                      Paste a business page, service URL, product page, or offer link. LocalPilot stores the source
                      server-side, extracts a demo brief, and can generate approval-ready posts from it.
                    </p>
                  </div>
                  <form className="source-import-form" onSubmit={importContentSource}>
                    <input
                      aria-label="Source page label"
                      value={contentSourceForm.label}
                      onChange={(event) => updateContentSourceForm("label", event.target.value)}
                      placeholder="Source label"
                    />
                    <input
                      aria-label="Source page URL"
                      value={contentSourceForm.url}
                      onChange={(event) => updateContentSourceForm("url", event.target.value)}
                      placeholder="https://business.example/offer"
                    />
                    <button className="primary-action" type="submit" disabled={contentSourcePending}>
                      {contentSourcePending ? "Importing..." : "Import source URL"}
                    </button>
                  </form>
                  <form className="source-image-form" onSubmit={importContentImage}>
                    <input
                      aria-label="Source image label"
                      value={contentImageForm.label}
                      onChange={(event) => updateContentImageForm("label", event.target.value)}
                      placeholder="Image source label"
                    />
                    <label className="source-image-picker">
                      <span>Product/service image</span>
                      <input aria-label="Source image file" type="file" accept="image/*" onChange={readContentImageFile} />
                    </label>
                    {contentImageForm.imageDataUrl && (
                      <img
                        className="source-image-preview"
                        src={contentImageForm.imageDataUrl}
                        alt={contentImageForm.fileName || "Selected source image preview"}
                      />
                    )}
                    <button className="primary-action" type="submit" disabled={contentImagePending}>
                      {contentImagePending ? "Importing..." : "Import source image"}
                    </button>
                  </form>
                  <div className="source-import-list" aria-label="Imported source URLs">
                    {phase3ContentSources.slice(0, 3).map((source) => (
                      <article key={source.id}>
                        {source.extracted?.previewDataUrl && (
                          <img className="source-card-image" src={source.extracted.previewDataUrl} alt={`${source.label} preview`} />
                        )}
                        <span>{source.sourceType === "image" ? `${source.status} image` : source.status}</span>
                        <strong>{source.label}</strong>
                        <p>{source.brief?.summary || source.url}</p>
                        <small>{Array.isArray(source.brief?.angles) ? source.brief.angles.join(" / ") : source.url}</small>
                        <button
                          className="secondary-action"
                          type="button"
                          onClick={() => generateFromContentSource(source)}
                          disabled={sourceGenerationPending === source.id}
                        >
                          {sourceGenerationPending === source.id ? "Generating..." : "Generate from source"}
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
                <div className="ai-output-list">
                  {(phase3Creatives.length ? phase3Creatives : plans).map((item) => (
                    <article key={`${item.id || item.name}-ai`}>
                      <span>{item.platform || item.name}</span>
                      <strong>{safeText(item.title, safeText(item.nativeCreative?.hook))}</strong>
                      <p>{safeText(item.caption, safeText(item.nativeCreative?.caption))}</p>
                    </article>
                  ))}
                </div>
                <form className="ai-prompt" onSubmit={submitPrompt}>
                  <input name="prompt" type="text" placeholder="Describe one offer, product, service, or local event..." />
                  <button className="primary-action" type="submit">
                    Generate weekly batch
                  </button>
                </form>
              </div>
            )}

            {config.view === "generation" && (
              <div className="generation-workspace">
                <section className="generation-header">
                  <div>
                    <p className="app-kicker">Generation workspace</p>
                    <h2>AI Studio</h2>
                    <p className="panel-subtitle">Choose a model, see the cost, and launch work you can actually track.</p>
                  </div>
                  <div className="generation-balance-strip">
                    <span className="gen-balance-label">Available credits</span>
                    <strong className="gen-balance-value">{genCredits.available}</strong>
                    {genCredits.reserved > 0 && <small className="gen-balance-reserved">{genCredits.reserved} reserved</small>}
                  </div>
                </section>

                <div className="generation-layout">
                  <aside className="generation-catalog-rail" aria-label="Models">
                    <h3>Models</h3>
                    {genCatalog.map((model) => (
                      <button
                        type="button"
                        key={model.id}
                        className={`gen-model-card ${genSelectedModel === model.id ? "active" : ""}`}
                        onClick={() => setGenSelectedModel(model.id)}
                      >
                        <span className="gen-model-capability">{model.capability}</span>
                        <strong>{model.displayName}</strong>
                        <small>{model.creditCost} credits &middot; {model.provider}</small>
                      </button>
                    ))}
                    {genCatalog.length === 0 && genStatus === "ready" && (
                      <p className="gen-empty-hint">No models available.</p>
                    )}
                    {genStatus === "loading" && <p className="gen-empty-hint">Loading models...</p>}
                  </aside>

                  <div className="generation-studio">
                    <section className="gen-prompt-section">
                      <div className="gen-cost-strip">
                        <span>Canonical carousel package</span>
                        <strong>{carouselCreditCost} credits</strong>
                        {(carouselCreditCost > genCredits.available) && (
                          <span className="gen-insufficient">You do not have enough credits for this run.</span>
                        )}
                      </div>
                      <div className="carousel-source-tabs" role="tablist" aria-label="Carousel source">
                        <button
                          className={carouselSourceMode === "idea" ? "active" : ""}
                          type="button"
                          onClick={() => setCarouselSourceMode("idea")}
                        >
                          Write idea
                        </button>
                        <button
                          className={carouselSourceMode === "url" ? "active" : ""}
                          type="button"
                          onClick={() => setCarouselSourceMode("url")}
                        >
                          Paste public URL
                        </button>
                      </div>
                      {carouselSourceMode === "idea" ? (
                        <textarea
                          className="gen-prompt-input"
                          placeholder="Describe the offer, proof, and CTA you want in the carousel..."
                          value={carouselIdeaText}
                          onChange={(e) => setCarouselIdeaText(e.target.value)}
                          rows={4}
                        />
                      ) : (
                        <div className="carousel-url-entry">
                          <input
                            className="gen-url-input"
                            type="url"
                            placeholder="https://www.nike.com/"
                            value={carouselSourceUrl}
                            onChange={(e) => setCarouselSourceUrl(e.target.value)}
                          />
                          {!carouselUrlValidity && carouselSourceUrl.trim() && (
                            <p className="gen-blocked-helper">Enter one valid public URL. Local and private hosts are blocked.</p>
                          )}
                          {latestCarouselJob?.sourcePreview?.domain && (
                            <div className="carousel-source-preview">
                              <strong>{latestCarouselJob.sourcePreview.title || latestCarouselJob.sourcePreview.domain}</strong>
                              <small>{latestCarouselJob.sourcePreview.domain}</small>
                              {latestCarouselJob.sourceHealth === "limited" && (
                                <span>Source limited; using fallback storyline</span>
                              )}
                            </div>
                          )}
                        </div>
                      )}
                      <article className="carousel-package-card">
                        <span>carousel_canonical_v1</span>
                        <h3>5 slides · cover -&gt; problem -&gt; proof -&gt; offer -&gt; CTA</h3>
                        <p>Brand locked from saved kit. Aspect ratio stays fixed at 3:4. MiniMax is the default merchant-facing model.</p>
                        <div className="carousel-package-meta">
                          <small>{carouselBrandReady ? "Brand locked from saved kit" : "Finish brand kit first"}</small>
                          <small>{carouselModel?.displayName || "MiniMax default model"}</small>
                          <small>{carouselStageLabel(latestCarouselJob)}</small>
                        </div>
                      </article>
                      <div className="gen-launch-row">
                        {carouselModel && (
                          <span className="gen-model-context">{carouselModel.displayName} &middot; {carouselModel.capability}</span>
                        )}
                        <button
                          className="primary-action gen-launch-btn"
                          type="button"
                          disabled={carouselLaunchBlocked}
                          onClick={handleCarouselLaunch}
                        >
                          {genLaunchPending ? "Launching..." : "Generate carousel"}
                        </button>
                      </div>
                      {!carouselBrandReady && (
                        <p className="gen-blocked-helper">Finish the saved brand kit before generating a carousel package.</p>
                      )}
                      {carouselActiveJobs.length > 0 && (
                        <p className="gen-blocked-helper">One carousel package is already running. Wait for it to finish before launching another.</p>
                      )}
                      {(carouselCreditCost > genCredits.available) && (
                        <p className="gen-blocked-helper">Add credits before launching this carousel package.</p>
                      )}
                    </section>

                    <section className="gen-jobs-section" aria-label="Job activity">
                      <h3>Job activity</h3>
                      {genJobs.length === 0 && (
                        <div className="gen-empty-jobs">
                          <p>No generation jobs yet</p>
                          <small>Pick a model and launch your first run.</small>
                        </div>
                      )}
                      {genJobs.map((job) => (
                        <article
                          key={job.id}
                          className={`gen-job-row gen-status-${job.status}`}
                          onClick={() => setGenDetailJobId(genDetailJobId === job.id ? "" : job.id)}
                        >
                          <span className={`gen-status-chip ${job.status}`}>
                            {job.workflowType === "carousel" ? carouselStageLabel(job) : job.status === "succeeded" ? "Ready" : job.status}
                          </span>
                          <div className="gen-job-meta">
                            <strong>{job.modelDisplayName || job.modelId}</strong>
                            <small>
                              {job.workflowType === "carousel" ? "carousel package" : job.capability}
                              {" "}· {job.creditCost} credits · {job.createdAt ? new Date(job.createdAt).toLocaleString() : ""}
                            </small>
                          </div>
                          {job.status === "failed" && (
                            <button
                              className="gen-retry-btn"
                              type="button"
                              disabled={genRetryPending === job.id}
                              onClick={(e) => { e.stopPropagation(); handleGenRetry(job.id); }}
                            >
                              {genRetryPending === job.id ? "Retrying..." : "Retry job"}
                            </button>
                          )}
                        </article>
                      ))}
                    </section>

                    {carouselJobs.filter((job) => job.status === "succeeded").length > 0 && (
                      <section className="gen-outputs-section" aria-label="Generated outputs">
                        <h3>Generated carousel packages</h3>
                        <div className="gen-output-grid">
                          {carouselJobs.filter((job) => job.status === "succeeded").map((job) => (
                            <article key={job.id} className="gen-output-card carousel-output-card">
                              <div className="carousel-output-preview-grid">
                                {job.slideCompositions.slice(0, 5).map((slide, index) => (
                                  <div key={`${job.id}-slide-${index}`} className="carousel-output-thumb">
                                    {slide.thumbnailRender ? (
                                      <img src={slide.thumbnailRender} alt={`${slide.layout?.role || "slide"} thumbnail`} />
                                    ) : (
                                      <span>{slide.layout?.role || `Slide ${index + 1}`}</span>
                                    )}
                                  </div>
                                ))}
                              </div>
                              <strong>{job.modelDisplayName || job.modelId}</strong>
                              <small>{job.prompt.length > 80 ? job.prompt.slice(0, 80) + "..." : job.prompt}</small>
                              <p className="carousel-output-summary">
                                {job.slideCompositions[0]?.headline || "Carousel package ready"} · {job.slideCompositions[0]?.body || ""}
                              </p>
                              <button className="primary-action" type="button" onClick={() => openCarouselEditor(job.creativeId)}>
                                Open in Creative Editor
                              </button>
                            </article>
                          ))}
                        </div>
                      </section>
                    )}

                    {genSucceededJobs.filter((j) => j.workflowType === "video").length > 0 && (
                      <section className="gen-outputs-section" aria-label="Generated video outputs">
                        <h3>Generated videos</h3>
                        <div className="gen-output-grid">
                          {genSucceededJobs.filter((j) => j.workflowType === "video").map((job) => (
                            <article key={job.id} className="gen-output-card gen-video-output-card">
                              <div className="gen-video-thumb">
                                {job.outputs[0]?.previewRef && (
                                  <img src={job.outputs[0].previewRef} alt="Video thumbnail" />
                                )}
                              </div>
                              <strong>{job.modelDisplayName || job.modelId}</strong>
                              <small>{job.prompt.length > 80 ? job.prompt.slice(0, 80) + "..." : job.prompt}</small>
                              <button
                                className="primary-action"
                                type="button"
                                disabled={!job.creativeId}
                                onClick={() => openVideoEditor(job.creativeId)}
                              >
                                Open in Creative Editor
                              </button>
                            </article>
                          ))}
                        </div>
                      </section>
                    )}

                    {genDetailJobId && (() => {
                      const detailJob = genJobs.find((j) => j.id === genDetailJobId);
                      if (!detailJob) return null;
                      return (
                        <aside className="gen-detail-drawer" aria-label="Job details">
                          <div className="gen-detail-header">
                            <h3>Job details</h3>
                            <button type="button" onClick={() => setGenDetailJobId("")}>&times;</button>
                          </div>
                          <dl className="gen-detail-fields">
                            <dt>Status</dt>
                            <dd><span className={`gen-status-chip ${detailJob.status}`}>{detailJob.status}</span></dd>
                            <dt>Model</dt>
                            <dd>{detailJob.modelDisplayName || detailJob.modelId}</dd>
                            <dt>Capability</dt>
                            <dd>{detailJob.capability}</dd>
                            <dt>Credits</dt>
                            <dd>{detailJob.creditCost}</dd>
                            <dt>Prompt</dt>
                            <dd>{detailJob.prompt}</dd>
                            <dt>Attempts</dt>
                            <dd>{detailJob.attemptCount}</dd>
                            {detailJob.workflowType === "carousel" && <>
                              <dt>Package stage</dt>
                              <dd>{carouselStageLabel(detailJob)}</dd>
                            </>}
                            {detailJob.errorMessage && <>
                              <dt>Error</dt>
                              <dd className="gen-detail-error">{detailJob.errorMessage}</dd>
                            </>}
                            <dt>Created</dt>
                            <dd>{detailJob.createdAt ? new Date(detailJob.createdAt).toLocaleString() : "—"}</dd>
                          </dl>
                          {detailJob.outputs.length > 0 && (
                            <div className="gen-detail-outputs">
                              <h4>Outputs</h4>
                              {detailJob.outputs.map((output) => (
                                <div key={output.id} className="gen-detail-output-row">
                                  <span>{output.metadata?.carouselSlide?.role || output.outputType}</span>
                                  <small>{output.previewRef || output.storagePath || output.providerRef}</small>
                                </div>
                              ))}
                            </div>
                          )}
                          {detailJob.workflowType === "carousel" && detailJob.creativeId && (
                            <button className="primary-action" type="button" onClick={() => openCarouselEditor(detailJob.creativeId)}>
                              Open in Creative Editor
                            </button>
                          )}
                          {detailJob.workflowType === "video" && detailJob.creativeId && (
                            <button className="primary-action" type="button" onClick={() => openVideoEditor(detailJob.creativeId)}>
                              Open in Creative Editor
                            </button>
                          )}
                        </aside>
                      );
                    })()}
                  </div>
                </div>
              </div>
            )}

            {config.view === "month" && (
              <div className="month-grid" aria-label="Calendar overview">
                {(phase3CalendarSlots.length ? phase3CalendarSlots : plans).map((item) => (
                  <div key={`${item.id || item.name}-month`}>
                    <span>{item.slotLabel || item.scheduleSlot}</span>
                    <strong>{item.platform || item.name}</strong>
                    <small>{item.status || item.publishingMode}</small>
                  </div>
                ))}
              </div>
            )}

            {config.view === "inbox" && (
              <div className="inbox-workspace">
                <div className="inbox-list">
                  {inboxThreads.map((thread, index) => (
                    <article
                      className={safeSelectedInbox === index ? "active" : ""}
                      key={stableNodeKey(thread.source, "inbox-thread", index)}
                    >
                      <button type="button" onClick={() => setSelectedInbox(index)}>
                        <span>{safeText(thread.source)}</span>
                        <strong>{safeText(thread.customer)}</strong>
                        <small>{safeText(thread.intent)}</small>
                      </button>
                    </article>
                  ))}
                </div>
                <section className="inbox-detail">
                  <span>{safeText(inboxThreads[safeSelectedInbox]?.source)}</span>
                  <h3>{safeText(inboxThreads[safeSelectedInbox]?.intent)}</h3>
                  <p>{safeText(inboxThreads[safeSelectedInbox]?.message)}</p>
                  <div>
                    <strong>Suggested reply</strong>
                    <p>{safeText(inboxThreads[safeSelectedInbox]?.draft)}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() =>
                      showAppToast(`${safeText(inboxThreads[safeSelectedInbox]?.action)} saved.`)
                    }
                  >
                    {safeText(inboxThreads[safeSelectedInbox]?.action)}
                  </button>
                </section>
              </div>
            )}

            {config.view === "analytics" && (
              <div className="analytics-workspace">
                <section className="performance-dashboard analytics-reference-dashboard" aria-label="Performance analytics dashboard">
                  <div className="analytics-reference-consistency" aria-label="Post consistency">
                    <article className="consistency-grid-card">
                      <strong>Post consistency</strong>
                      <div className="consistency-week-row" aria-label="Weekly posting consistency">
                        {["F", "S", "S", "M", "T", "W", "T"].map((day, index) => (
                          <span className={index === 2 ? "posted" : index === 3 ? "scheduled" : ""} key={`${day}-${index}`}>
                            <small>{day}</small>
                            <i />
                          </span>
                        ))}
                      </div>
                      <div className="consistency-legend">
                        <span><i className="posted" />Posted</span>
                        <span><i />No Activity</span>
                        <span><i className="scheduled" />Scheduled</span>
                      </div>
                    </article>
                    <article className="posting-streak-card">
                      <strong>Post consistency</strong>
                      <p>
                        <b>1</b>
                        <span>Day streak</span>
                      </p>
                      <small>Based on your recent activity</small>
                    </article>
                  </div>

                  <div className="analytics-account-tabs" role="tablist" aria-label="Analytics connected accounts">
                    {analyticsAccountTabs.map((tab) => (
                      <button className={tab.active ? "active" : ""} type="button" role="tab" aria-selected={tab.active} key={tab.label}>
                        <span>{tab.icon}</span>
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  <div className="analytics-reference-metrics">
                    {analyticsMetricCards.map((metric) => (
                      <article className={`analytics-reference-card ${metric.tone}`} key={metric.label}>
                        <span>{metric.icon}</span>
                        <div>
                          <strong>{metric.label}</strong>
                          <b>{metric.value}</b>
                          <small>{metric.dateRange}</small>
                        </div>
                      </article>
                    ))}
                  </div>

                  <div className="analytics-chart-grid">
                    <article className="analytics-chart-card posting">
                      <h3>Your Posting Activity</h3>
                      <div className="analytics-chart-area">
                        <i className="activity-bar first" />
                        <i className="activity-bar second" />
                      </div>
                      <div className="analytics-chart-axis">
                        {analyticsChartDates.map((date) => (
                          <span key={date}>{date}</span>
                        ))}
                      </div>
                    </article>
                    <article className="analytics-chart-card engagement">
                      <h3>Your Posts' Engagement</h3>
                      <div className="analytics-chart-area">
                        <i className="engagement-line" />
                      </div>
                      <div className="analytics-chart-axis">
                        {["24 May", "28 May", "02 Jun", "06 Jun", "11 Jun", "16 Jun", "20 Jun"].map((date) => (
                          <span key={date}>{date}</span>
                        ))}
                      </div>
                    </article>
                    <article className="analytics-chart-card followers">
                      <h3>Your Followers' Growth</h3>
                      <div className="analytics-chart-area">
                        <i className="followers-line" />
                      </div>
                      <div className="analytics-chart-axis">
                        {["22 May", "25 May", "27 May", "29 May", "01 Jun", "03 Jun", "05 Jun", "08 Jun", "10 Jun", "15 Jun", "19 Jun"].map((date) => (
                          <span key={date}>{date}</span>
                        ))}
                      </div>
                    </article>
                  </div>
                </section>
                <section className="roi-signal-grid">
                  {proofEventDisplayCards.map(([label, value, body]) => (
                    <article key={label}>
                      <span>{label}</span>
                      <strong>{value}</strong>
                      <p>{body}</p>
                      <button type="button" onClick={() => recordProofEvent(label, phase3Creatives[0]?.id)}>
                        Record demo event
                      </button>
                    </article>
                  ))}
                </section>
                <section className="roi-explain-panel">
                  <div>
                    <span>Proof loop</span>
                    <h3>Lower-bound evidence, not fake exact ROI.</h3>
                    <p>
                      LocalPilot connects content to observable actions: short-link clicks, QR scans, call taps,
                      direction taps, DMs, coupon redemptions, and owner-confirmed mentions.
                    </p>
                  </div>
                  <div className="analytics-channel-list">
                    {plans.map((plan) => (
                      <article key={`${plan.name}-roi`}>
                        <strong>{plan.name}</strong>
                        <span>{plan.kpi}</span>
                        <button type="button" onClick={() => showAppToast(`${plan.name} proof note added to report.`)}>
                          Add note
                        </button>
                      </article>
                    ))}
                  </div>
                </section>
              </div>
            )}

            {config.view === "help" && (
              <div className="help-workspace">
                <section className="help-support-hero">
                  <div>
                    <p className="app-kicker">Need help</p>
                    <h2>Support center for account setup, FAQs, and demo handoff.</h2>
                    <p>
                      Choose a topic, review the status, and save a local support draft. Nothing is sent
                      externally from this demo.
                    </p>
                  </div>
                  <div className="help-status-strip">
                    <article>
                      <span>Service status</span>
                      <strong>Local demo online</strong>
                      <p>Backend workflow and screen smoke passed.</p>
                    </article>
                    <article>
                      <span>Account safety</span>
                      <strong>No external send</strong>
                      <p>Drafts stay local until production confirmation exists.</p>
                    </article>
                    <article>
                      <span>Publishing help</span>
                      <strong>Owner approval first</strong>
                      <p>Facebook live publish stays gated by connected accounts.</p>
                    </article>
                  </div>
                </section>
                <section className="help-action-grid">
                  {helpActions.map(([title, body]) => (
                    <article className={activeHelpAction === title ? "active" : ""} key={title}>
                      <span>{title}</span>
                      <strong>{title}</strong>
                      <p>{body}</p>
                      <button type="button" onClick={() => openHelpAction(title, body)}>
                        Open
                      </button>
                    </article>
                  ))}
                </section>
                <section className="help-message-card">
                  <div>
                    <p className="app-kicker">Selected topic</p>
                    <h3>{selectedHelpAction[0]}</h3>
                    <p>{selectedHelpAction[1]}</p>
                  </div>
                  <form className="help-message-form" onSubmit={submitHelpDraft}>
                    <label>
                      Send a message
                      <textarea
                        value={helpDraft}
                        onChange={(event) => setHelpDraft(event.target.value)}
                        placeholder="Draft a setup question for the LocalPilot team..."
                      />
                    </label>
                    <div className="help-message-actions">
                      <button className="secondary-action" type="button" onClick={() => setHelpDraft("")}>
                        Clear draft
                      </button>
                      <button className="primary-action" type="submit">
                        Save local draft
                      </button>
                    </div>
                  </form>
                </section>
              </div>
            )}

            {creatorWorkflowOpen && (
              <div className="modal-backdrop creator-workflow-backdrop" role="presentation">
                <section className="creator-workflow-modal" role="dialog" aria-modal="true" aria-label="Creator Style Video workflow modal">
                  <button className="modal-close" type="button" aria-label="Close workflow" onClick={closeCreatorWorkflow}>
                    ×
                  </button>
                  <div className="creator-reference-shell">
                    <aside className="creator-reference-sidebar" aria-label="Creator workflow reference navigation">
                      <div className="creator-reference-brand">
                        <span className="creator-reference-mark">LP</span>
                        <strong>LocalPilot.ai</strong>
                      </div>
                      <button className="creator-reference-create" type="button">
                        <span>+</span>
                        Create New
                      </button>
                      <button className="creator-reference-auto" type="button">
                        <span>➤</span>
                        Auto Posting
                      </button>
                      <nav>
                        {[
                          ["◐", "Ad Inspirations", "New"],
                          ["▰", "Content Library", ""],
                          ["▦", "Content Calendar", ""],
                          ["▣", "Brand & Social Accounts", ""],
                          ["▥", "Competitor Analysis", ""],
                          ["▤", "Analytics", ""],
                          ["?", "Need help?", ""],
                        ].map(([icon, label, badge]) => (
                          <button type="button" key={label}>
                            <span>{icon}</span>
                            <strong>{label}</strong>
                            {badge && <em>{badge}</em>}
                          </button>
                        ))}
                      </nav>
                      <article className="creator-reference-trial">
                        <strong>Rise Plan Trial Activated</strong>
                        <p>Enjoy full access. Your card will be charged tomorrow</p>
                      </article>
                      <div className="creator-reference-user">
                        <span>H</span>
                        <div>
                          <strong>Aurora Heating &...</strong>
                          <small>huihuipan69@gm...</small>
                        </div>
                      </div>
                    </aside>
                    <main className="creator-reference-main">
                  <div className="creator-modal-head">
                    <div>
                      <p className="app-kicker">Creator Style Video</p>
                      <h2>Make creator-style videos using AI-generated actors.</h2>
                      <p>
                        Popup workflow: generate ideas, select the angle, choose Motivational style,
                        pick AI actor and subtitle style, then generate backend artifacts.
                      </p>
                    </div>
                  </div>
                  <section className="creator-style-wizard" aria-label="Creator Style Video workflow">
                    <div className="creator-progress-dots" aria-label="Creator Style Video workflow progress">
                      {creatorVisibleWorkflowSteps.map((step, index) => (
                        <span
                          className={
                            index < creatorWorkflowStepIndex
                              ? "complete"
                              : index === creatorWorkflowStepIndex
                              ? "active"
                              : ""
                          }
                          key={step.id}
                          aria-label={`${index + 1}. ${step.label}`}
                        >
                          {index < creatorWorkflowStepIndex ? "✓" : index + 1}
                        </span>
                      ))}
                    </div>
                    <div className="creator-step-title">
                      <h2>{activeCreatorWorkflowStep.title}</h2>
                      <p>{activeCreatorWorkflowStep.subtitle}</p>
                    </div>

                    <div className="creator-step-shell">
                      {creatorWorkflowStep === "prompt" && (
                        <article className="creator-step-panel creator-prompt-panel">
                        <label>
                          Write Your Idea
                          <textarea
                            rows="6"
                            value={creatorStyleForm.prompt}
                            placeholder="Describe what this UGC Video should be about."
                            onChange={(event) => updateCreatorStyleForm("prompt", event.target.value)}
                          />
                        </label>
                        <button
                          className="secondary-action creator-idea-button"
                          type="button"
                          onClick={openCreatorIdeaChat}
                          disabled={creatorStylePending === "ideas"}
                        >
                          {creatorStylePending === "ideas" ? "Generating ideas..." : "Generate ideas for me"}
                        </button>
                      </article>
                      )}

                      {creatorWorkflowStep === "idea" && (
                        <article className="creator-step-panel">
                        <div className="creator-idea-list">
                          {selectedCreatorIdeas.length ? (
                            selectedCreatorIdeas.map((idea) => (
                              <button
                                className={
                                  (creatorStyleForm.selectedIdeaId || selectedCreatorWorkflow?.selectedIdeaId) === idea.id
                                    ? "active"
                                    : ""
                                }
                                type="button"
                                key={idea.id}
                                onClick={() => updateCreatorStyleForm("selectedIdeaId", idea.id)}
                              >
                                <strong>{idea.label}</strong>
                                <small>{safeText(idea.hook)}</small>
                              </button>
                            ))
                          ) : (
                            <div className="creator-empty-state">
                              <strong>No ideas yet.</strong>
                              <p>Click Generate ideas for me to populate backend ideas.</p>
                              <button className="secondary-action" type="button" onClick={generateCreatorStyleIdeas}>
                                Generate ideas for me
                              </button>
                            </div>
                          )}
                        </div>
                      </article>
                      )}

                      {creatorWorkflowStep === "style" && (
                        <article className="creator-step-panel">
                        <div className="creator-field-group">
                          <span>Script Style</span>
                          <p>Choose the kind of post you want to create.</p>
                        </div>
                        <div className="creator-segmented">
                          {creatorStyleStyleChoices.map((style) => (
                            <button
                              className={creatorStyleForm.styleId === style.id ? "active" : ""}
                              type="button"
                              key={style.id}
                              onClick={() => updateCreatorStyleForm("styleId", style.id)}
                            >
                              <strong>{style.label}</strong>
                            </button>
                          ))}
                        </div>
                        <div className="creator-field-group">
                          <span>Aspect Ratio</span>
                          <p>Select a canvas size to proceed.</p>
                        </div>
                        <div className="ratio-picker creator-ratio-picker" aria-label="Creator Style Video aspect ratios">
                          {creatorAspectRatioOptions.map((ratio) => (
                            <button
                              className={creatorStyleForm.aspectRatio === ratio ? "active" : ""}
                              type="button"
                              key={ratio}
                              onClick={() => updateCreatorStyleForm("aspectRatio", ratio)}
                            >
                              {ratio}
                            </button>
                          ))}
                        </div>
                      </article>
                      )}

                      {creatorWorkflowStep === "actor" && (
                        <article className="creator-step-panel">
                        <div className="creator-filter-row" aria-label="Avatar filters">
                          <span>Gender</span>
                          <span>Age</span>
                          <span>Ethnicity</span>
                        </div>
                        <div className="creator-avatar-grid">
                          {creatorStyleActorChoices.map((actor, index) => (
                            <button
                              className={creatorStyleForm.actorId === actor.id ? "active" : ""}
                              type="button"
                              aria-label={`Select ${actor.name}: ${actor.persona}`}
                              key={actor.id}
                              onClick={() => updateCreatorStyleForm("actorId", actor.id)}
                            >
                              {creatorStyleForm.actorId === actor.id && (
                                <span className="creator-selection-check" aria-hidden="true">
                                  ✓
                                </span>
                              )}
                              <div
                                className={`creator-avatar-swatch swatch-${index + 1}`}
                                style={creatorAvatarPreviewStyle(index)}
                              >
                                {actor.badge || "Actor"}
                              </div>
                              <strong>{actor.name}</strong>
                              <small>{actor.persona}</small>
                            </button>
                          ))}
                        </div>
                      </article>
                      )}

                      {creatorWorkflowStep === "template" && (
                        <article className="creator-step-panel">
                        <div className="creator-template-grid">
                          {creatorStyleTemplateChoices.map((template, index) => {
                            const sample = creatorTemplatePreviewSamples[index % creatorTemplatePreviewSamples.length];
                            return (
                              <button
                                className={creatorStyleForm.templateId === template.id ? "active" : ""}
                                type="button"
                                key={template.id}
                                onClick={() => updateCreatorStyleForm("templateId", template.id)}
                              >
                                {creatorStyleForm.templateId === template.id && (
                                  <span className="creator-selection-check" aria-hidden="true">
                                    ✓
                                  </span>
                                )}
                                <div className={`creator-template-preview subtitle-style-${(index % 8) + 1}`}>
                                  <span>{sample.lead}</span>
                                  <strong>{sample.accent}</strong>
                                </div>
                              </button>
                            );
                          })}
                        </div>
                      </article>
                      )}

                      {creatorWorkflowStep === "review" && (
                        <article className="creator-step-panel creator-review-panel">
                          <div className="creator-script-card">
                            <span className="creator-script-tab">Your script</span>
                            <blockquote>{creatorReviewScript}</blockquote>
                            <span className="creator-duration-pill">
                              Estimated Duration: {selectedCreatorScriptDuration.estimate}
                            </span>
                          </div>
                          <div className="creator-rewrite-block">
                            <strong>Want a different length? We'll rewrite the script.</strong>
                            <div className="creator-duration-options" aria-label="Rewrite duration options">
                              {creatorScriptDurationOptions.map((duration) => (
                                <button
                                  className={creatorScriptDuration === duration.id ? "active" : ""}
                                  type="button"
                                  key={duration.id}
                                  onClick={() => setCreatorScriptDuration(duration.id)}
                                >
                                  {duration.label}
                                </button>
                              ))}
                            </div>
                          </div>
                          <label className="creator-script-rewrite">
                            Update your script by describing the changes you want
                            <span>
                              <input
                                type="text"
                                value={creatorScriptRewritePrompt}
                                placeholder="e.g. Make it more casual, add a stronger CTA at the end, keep it under 30 seconds."
                                onChange={(event) => setCreatorScriptRewritePrompt(event.target.value)}
                              />
                              <button type="button" aria-label="Apply script rewrite" onClick={applyCreatorScriptRewrite}>
                                →
                              </button>
                            </span>
                          </label>
                      </article>
                      )}

                      {creatorWorkflowStep === "confirm" && (
                        <article className="creator-step-panel creator-confirm-panel">
                          <div className="creator-confirm-summary">
                            <h3>Summary</h3>
                            <div className="creator-confirm-grid">
                              <span className="creator-confirm-icon">▣</span>
                              <p>
                                <strong>Post Type:</strong> UGC
                              </p>
                              <span className="creator-confirm-icon">↗</span>
                              <p>
                                <strong>Aspect Ratio:</strong> {creatorStyleForm.aspectRatio}
                              </p>
                              <span className="creator-confirm-icon">$</span>
                              <p>
                                <strong>Estimated credit usage ⓘ :</strong> 114 - 139
                              </p>
                            </div>
                          </div>
                        </article>
                      )}

                      {creatorWorkflowStep === "generated" && (
                        <article className="creator-output-panel">
                          <div className="creator-video-preview" aria-label="Generated creator-style media preview">
                            <span>{creatorStyleForm.aspectRatio}</span>
                            <button type="button" aria-label="Play generated storyboard preview">▶</button>
                            <strong>{selectedCreatorActor?.name || selectedCreatorPackage?.avatar?.name || "AI actor"}</strong>
                            <p>{selectedCreatorTemplate?.sceneStyle || selectedCreatorMediaAsset?.metadata?.template?.sceneStyle || "actor + service b-roll + branded end card"}</p>
                          </div>
                          <div className="creator-output-details">
                            <div className="creator-output-topline">
                              <span>from your idea</span>
                              <span>130.18 credits used</span>
                            </div>
                            <h3>Caption</h3>
                            <p>
                              {safeText(selectedCreatorCreative?.caption) || "Generate the creator-style video to create caption and storyboard output."}
                            </p>
                            <h3>Input Prompt:</h3>
                            <p>{creatorStyleForm.prompt}</p>
                            <div className="creator-artifact-list">
                              <span>creative: {selectedCreatorCreative?.id || "not generated"}</span>
                              <span>media asset: {selectedCreatorMediaAsset?.status || "pending"}</span>
                              <span>UGC package: {selectedCreatorPackage?.status || "pending"}</span>
                              <span>calendar slot: {selectedCreatorCalendarSlot?.slotLabel || selectedCreatorCreative?.scheduleSlot || "pending"}</span>
                            </div>
                            <div className="creator-generated-actions">
                              <button
                                type="button"
                                onClick={() => {
                                  setCreatorWorkflowOpen(false);
                                  openPublishModal(selectedCreatorCreative);
                                }}
                                disabled={!selectedCreatorCreative}
                              >
                                Publish
                              </button>
                              <button type="button" onClick={openCreatorSchedule} disabled={!selectedCreatorCreative}>
                                Schedule Post
                              </button>
                            </div>
                          </div>
                        </article>
                      )}
                    </div>

                    {creatorWorkflowStep !== "generated" && (
                      <div className="creator-wizard-footer">
                        <button className="secondary-action" type="button" onClick={stepCreatorWorkflowBack}>
                          ← Back
                        </button>
                        <button
                          className="primary-action"
                          type="button"
                          onClick={continueCreatorWorkflow}
                          disabled={!creatorCanContinue || creatorStylePending === "ideas" || creatorStylePending === "generate"}
                        >
                          {creatorWorkflowStep === "review"
                            ? "Continue"
                            : creatorWorkflowStep === "confirm"
                            ? creatorStylePending === "generate"
                              ? "Generating..."
                              : "Generate"
                            : creatorWorkflowStep === "prompt" && creatorStylePending === "ideas"
                            ? "Generating ideas..."
                            : "Continue"}
                        </button>
                      </div>
                    )}
                  </section>
                    </main>
                  </div>
                  {creatorIdeaChatOpen && (
                    <div className="creator-idea-chat-backdrop" role="presentation">
                      <section className="creator-idea-chat" role="dialog" aria-modal="true" aria-label="Generate ideas for me chat">
                        <div className="creator-idea-chat-head">
                          <h3>
                            <span aria-hidden="true">✎</span>
                            Generate ideas for me
                          </h3>
                          <button
                            type="button"
                            aria-label="Close generate ideas chat"
                            onClick={closeCreatorIdeaChat}
                            disabled={creatorStylePending === "ideas"}
                          >
                            ×
                          </button>
                        </div>
                        <div className="creator-idea-chat-body">
                          <p className="creator-chat-bubble bot">🤖 What would you like to create?</p>
                          {creatorStyleForm.prompt.trim() && (
                            <p className="creator-chat-bubble user">{creatorStyleForm.prompt.trim()}</p>
                          )}
                          <p className="creator-chat-bubble bot wide">
                            🤖 Can you tell me more about what you would like to achieve with this?
                          </p>
                          {creatorIdeaChatInput.trim() && (
                            <p className="creator-chat-bubble user compact">{creatorIdeaChatInput.trim()}</p>
                          )}
                          {creatorIdeaChatResults.length > 0 && (
                            <div className="creator-chat-prompt-results">
                              <p>🤖 Here are {creatorIdeaChatResults.length} prompts for you:</p>
                              {creatorIdeaChatResults.map((idea, index) => (
                                <article key={idea.id || `${idea.label}-${index}`}>
                                <span>
                                  {index + 1}. {safeText(idea.hook)}
                                </span>
                                  <small>{idea.angle}</small>
                                  <button type="button" onClick={() => useCreatorIdeaPrompt(idea)}>
                                    Use This Prompt
                                  </button>
                                </article>
                              ))}
                            </div>
                          )}
                        </div>
                        <form className="creator-idea-chat-form" onSubmit={submitCreatorIdeaChat}>
                          <input
                            type="text"
                            value={creatorIdeaChatInput}
                            placeholder="Describe what you want to create..."
                            onChange={(event) => setCreatorIdeaChatInput(event.target.value)}
                            disabled={creatorStylePending === "ideas"}
                          />
                          <button type="submit" aria-label="Send idea goal" disabled={creatorStylePending === "ideas"}>
                            {creatorStylePending === "ideas" ? "…" : "➤"}
                          </button>
                        </form>
                      </section>
                    </div>
                  )}
                </section>
              </div>
            )}

            {waitNudgeOpen && (
              <div
                className="wait-nudge-backdrop"
                role="presentation"
                onMouseDown={(event) => event.target === event.currentTarget && closeInspirationNudge()}
              >
                <section className="wait-nudge-modal" role="dialog" aria-modal="true" aria-labelledby="wait-nudge-title">
                  <button className="wait-nudge-close" type="button" aria-label="Close wait nudge" onClick={closeInspirationNudge}>
                    ×
                  </button>
                  <h3 id="wait-nudge-title">Wait! Don&apos;t Go...</h3>
                  <p>
                    You haven&apos;t unlocked the power of AI content yet. Give it a try — your first 10 generations are on us!
                  </p>
                  <div className="wait-nudge-actions">
                    <button className="wait-nudge-secondary" type="button" onClick={continueInspirationAfterNudge}>
                      Maybe later
                    </button>
                    <button className="wait-nudge-primary" type="button" onClick={downloadPostFromInspirationNudge}>
                      Download a post
                    </button>
                  </div>
                </section>
              </div>
            )}

            {libraryDetailCreative && (
              <div className="library-detail-backdrop" role="presentation">
                <section className="library-detail-modal" role="dialog" aria-modal="true" aria-label="Content Library asset detail">
                  {(() => {
                    const isVideoCreative = libraryDetailMediaAsset?.assetType === "video";
                    return (
                      <div className="library-detail-preview" style={referencePreviewStyle(libraryDetailPreviewImage)}>
                        <span>{libraryDetailMediaAsset?.aspectRatio || "9:16"}</span>
                        {isVideoCreative ? (
                          <video
                            className="library-detail-video"
                            src={libraryDetailMediaAsset.storageRef}
                            controls
                            poster={libraryDetailMediaAsset.storageRef !== libraryDetailPreviewImage ? libraryDetailPreviewImage || undefined : undefined}
                          />
                        ) : (
                          <button type="button" aria-label={`Play ${libraryDetailCreative.title}`}>
                            ▶
                          </button>
                        )}
                        <strong>{libraryDetailCreative.platform?.replace(/_/g, " ") || "Generated video"}</strong>
                      </div>
                    );
                  })()}
                <div className="library-detail-copy">
                    <button className="library-detail-close" type="button" aria-label="Close asset detail" onClick={closeLibraryDetail}>
                      ×
                    </button>
                    <div className="library-detail-topline">
                      <span>from your idea</span>
                      <span>130.18 credits used</span>
                    </div>
                    <h3>Caption</h3>
                    <p>{safeText(libraryDetailCreative?.caption)}</p>
                    <p className="library-detail-tags">{(libraryDetailCreative.hashtags || []).join(" ") || "#auroraheatcool"}</p>
                    <h3>Input Prompt:</h3>
                    <p>
                      <strong>Text to Post</strong>
                      <br />
                      {libraryDetailPrompt}
                    </p>
                    <small>{libraryDetailCreative.updatedAt || "11 minutes ago"}</small>
                    <div className="library-detail-feedback">
                      <strong>Would you use this post?</strong>
                      <span>
                        <button type="button" aria-label="Like this post">♡</button>
                        <button type="button" aria-label="Dislike this post">♧</button>
                      </span>
                    </div>
                    <div className="library-detail-actions">
                      <button type="button" onClick={() => openPublishModal(libraryDetailCreative)}>
                        Publish
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedPost(libraryDetailIndex);
                          closeLibraryDetail();
                          showAppToast("Creative editor selected this generated asset.");
                        }}
                      >
                        Edit
                      </button>
                      <button type="button" onClick={() => showAppToast("Download package prepared for owner review.")}>
                        Download
                      </button>
                      <button type="button" aria-label="More asset actions" onClick={() => showAppToast("More asset actions are demo-safe.")}>
                        …
                      </button>
                      {libraryDetailMediaAsset?.assetType === "video" && (
                        <>
                          <button
                            type="button"
                            disabled={approvalFeedbackPending === libraryDetailCreative.id}
                            onClick={() => addApprovalFeedback(libraryDetailIndex, "approval_note")}
                          >
                            Approve video
                          </button>
                          <button
                            type="button"
                            onClick={() => addApprovalFeedback(libraryDetailIndex, "change_request")}
                          >
                            Request changes
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                </section>
              </div>
            )}

            {socialActionDialog && activeSocialPlatform && (
              <div className="social-action-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && closeSocialDialog()}>
                <section
                  className={`social-action-modal ${socialActionDialog.mode}`}
                  role="dialog"
                  aria-modal="true"
                  aria-label={`${activeSocialPlatform.provider} social account dialog`}
                >
                  <header className="social-action-modal-head">
                    <div className={`social-platform-icon ${activeSocialPlatform.tone}`}>{activeSocialPlatform.icon}</div>
                    <div>
                      <h3>
                        {socialActionDialog.mode === "faq"
                          ? `${activeSocialPlatform.provider} FAQ's`
                          : socialActionDialog.mode === "video"
                          ? `${activeSocialPlatform.provider} Videos`
                          : activeSocialPlatform.provider}
                      </h3>
                      {socialActionDialog.mode === "add" && <p>Connect your {activeSocialPlatform.provider} account</p>}
                      {socialActionDialog.mode === "video" && <p>Watch setup videos before linking the account.</p>}
                    </div>
                    <button className="social-action-close" type="button" aria-label="Close social account dialog" onClick={closeSocialDialog}>
                      ×
                    </button>
                  </header>

                  {socialActionDialog.mode === "faq" && (
                    <div className="social-action-accordion">
                      {activeSocialFaqs.map((question) => (
                        <button type="button" key={question} onClick={() => showAppToast(`${activeSocialPlatform.provider} FAQ opened.`)}>
                          <span>{question}</span>
                          <i>⌄</i>
                        </button>
                      ))}
                    </div>
                  )}

                  {socialActionDialog.mode === "add" && (
                    <div className="social-connect-options">
                      {activeSocialConnectionChoices.map((choice) => (
                        <button type="button" key={`${choice.title}-${choice.subtitle}`} onClick={() => handleSocialConnectionChoice(choice)}>
                          <span className="social-connect-icons">
                            <b>{choice.icon}</b>
                            {choice.companion && <em>{choice.companion}</em>}
                          </span>
                          <span>
                            <strong>{choice.title}</strong>
                            <small>{choice.subtitle}</small>
                          </span>
                          {choice.badge && <i className={choice.badgeTone}>{choice.badge}</i>}
                          {choice.note && <mark>{choice.note}</mark>}
                        </button>
                      ))}
                    </div>
                  )}

                  {socialActionDialog.mode === "video" && (
                    <div className="social-action-accordion">
                      {[
                        `How to connect ${activeSocialPlatform.provider}`,
                        `How to schedule ${activeSocialPlatform.provider} posts`,
                        "How owner approval works before publishing",
                      ].map((title) => (
                        <button type="button" key={title} onClick={() => showAppToast(`${title} queued for the demo help panel.`)}>
                          <span>{title}</span>
                          <i>▶</i>
                        </button>
                      ))}
                    </div>
                  )}
                </section>
              </div>
            )}

            {publishDraft.creativeId && publishCreative && (
              <div className="modal-backdrop publish-modal-backdrop" role="presentation">
                <section className="modal publish-modal" role="dialog" aria-modal="true" aria-label="Publish post modal">
                  <button className="modal-close" type="button" onClick={closePublishModal}>
                    ×
                  </button>
                  <div className="modal-copy">
                    <p className="app-kicker">{publishDraft.step === "schedule" ? "Schedule post" : "Publish post"}</p>
                    <h2>
                      {publishDraft.step === "schedule"
                        ? "Choose the optimal time for your post to go live."
                        : "Choose the specific social media platform below to publish/schedule your post."}
                    </h2>
                  </div>
                  {publishDraft.step === "platform" ? (
                    <>
                      <div className="publish-reference-body">
                        <section className="publish-ready-panel" aria-label="Ready to post">
                          <h3>Ready to post</h3>
                          <button
                            className={publishDraft.platform === "Facebook" && publishDraft.postType === "Feed post" ? "active" : ""}
                            type="button"
                            onClick={() => {
                              updatePublishDraft("platform", "Facebook");
                              updatePublishDraft("postType", "Feed post");
                            }}
                          >
                            <span>{publishDraft.platform === "Facebook" && publishDraft.postType === "Feed post" ? "✓" : ""}</span>
                            <strong>f</strong>
                            Facebook
                            <i>›</i>
                          </button>
                          <button
                            className={publishDraft.platform === "Facebook Reel" || publishDraft.postType === "Reel/Short" ? "active" : ""}
                            type="button"
                            onClick={() => {
                              updatePublishDraft("platform", "Facebook Reel");
                              updatePublishDraft("postType", "Reel/Short");
                            }}
                          >
                            <span>{publishDraft.platform === "Facebook Reel" || publishDraft.postType === "Reel/Short" ? "✓" : ""}</span>
                            <strong>▣</strong>
                            Facebook Reel
                            <i>›</i>
                          </button>
                        </section>
                        <section className="publish-reference-status">
                          <article className={publishUnsupported ? "warning" : ""}>
                            <strong>{publishUnsupported ? "Not Supported" : "Supported"}</strong>
                            <p>
                              {publishUnsupported
                                ? "Videos media type are not supported by this destination."
                                : "Selected destination is compatible with assisted owner-approval handoff."}
                            </p>
                          </article>
                          <article>
                            <div>
                              <strong>{publishMissingAccount && !publishAssisted ? "Accounts not linked" : "Accounts ready"}</strong>
                              <button type="button" onClick={() => selectModule("Brand & Social Accounts")}>
                                Link account
                              </button>
                            </div>
                            <p>Please connect the accounts below to publish/schedule this post!</p>
                            <div className="publish-account-icons" aria-label="Supported account connectors">
                              {["IG", "in", "P", "f", "♪", "X", "▶", "+"].map((icon) => (
                                <span key={icon}>{icon}</span>
                              ))}
                            </div>
                          </article>
                        </section>
                        {publishAssisted && (
                          <div className="publish-assisted">
                            <strong>Assisted package</strong>
                            <p>This path creates a handoff package. It is not autonomous publishing.</p>
                          </div>
                        )}
                      </div>
                      <button className="primary-action publish-reference-continue" type="button" disabled={!publishCanContinue} onClick={continuePublishSchedule}>
                        Continue
                      </button>
                    </>
                  ) : (
                    <>
                      <div className="publish-schedule-body">
                        <section className="publish-schedule-calendar" aria-label="Schedule calendar">
                          <div className="publish-schedule-month">
                            <button type="button" aria-label="Previous month">‹</button>
                            <strong>June 2026</strong>
                            <button type="button" aria-label="Next month">›</button>
                          </div>
                          <div className="publish-schedule-days">
                            {["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"].map((day) => (
                              <span key={day}>{day}</span>
                            ))}
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 1, 2, 3, 4, 5].map((day, index) => (
                              <button
                                className={publishDraft.scheduleDay === day && index < 30 ? "active" : ""}
                                type="button"
                                key={`${day}-${index}`}
                                onClick={() => updatePublishDraft("scheduleDay", day)}
                              >
                                {day}
                              </button>
                            ))}
                          </div>
                        </section>
                        <section className="publish-schedule-time" aria-label="Schedule time">
                          <h3>Monday, June {publishDraft.scheduleDay}, 2026</h3>
                          <p>Brand Timezone : (GMT -4:00) America/Detroit</p>
                          <div className="publish-time-picker">
                            {["scheduleHour", "scheduleMinute", "scheduleMeridiem"].map((field) => (
                              <label key={field}>
                                <span>⌃</span>
                                <input
                                  value={publishDraft[field]}
                                  onChange={(event) => updatePublishDraft(field, event.target.value)}
                                  aria-label={field}
                                />
                                <span>⌄</span>
                              </label>
                            ))}
                          </div>
                        </section>
                        <label className="publish-schedule-check">
                          <input
                            type="checkbox"
                            checked={publishDraft.aiSuggestedTime}
                            onChange={(event) => updatePublishDraft("aiSuggestedTime", event.target.checked)}
                          />
                          Apply AI suggested time for publishing
                        </label>
                        <label className="publish-schedule-check">
                          <input
                            type="checkbox"
                            checked={publishDraft.approvalMember}
                            onChange={(event) => updatePublishDraft("approvalMember", event.target.checked)}
                          />
                          Select Team Member for approval
                        </label>
                      </div>
                      <button className="publish-immediate-link" type="button" onClick={schedulePublishPost}>
                        Publish Immediately Instead?
                      </button>
                      <div className="publish-schedule-actions">
                        <button type="button" onClick={() => updatePublishDraft("step", "platform")}>
                          Back
                        </button>
                        <button className="primary-action" type="button" onClick={schedulePublishPost}>
                          Schedule Post
                        </button>
                      </div>
                    </>
                  )}
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
          </>
        )}
      </main>
      {appToast && <div className="app-toast">{appToast}</div>}
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <TranslationLayer />
      <AppRoutes appElement={<AppDemo />} landingElement={<LandingPage />} />
    </LanguageProvider>
  );
}

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("LocalPilot root element was not found.");
}

const rootStoreKey = "__localpilotReactRoot";
const existingRoot = window[rootStoreKey];
const localPilotRoot =
  existingRoot && existingRoot._internalRoot?.containerInfo === rootElement
    ? existingRoot
    : createRoot(rootElement);
window[rootStoreKey] = localPilotRoot;
localPilotRoot.render(<App />);

if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    // Intentionally no root disposal here. Keep the existing root between module updates
    // to avoid duplicate createRoot() calls and child-removal consistency errors.
  });
}
