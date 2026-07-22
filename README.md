# Prediction Market Research Signals

公开展示预测市场研究信号的静态网站。页面只呈现需要执行的买入、加仓和卖出信号，以及对应方向、Agent 合理价格、当前可执行价格、价差、简要原因和公开证据。

公网地址：<https://youngy620.github.io/prediction-signals/>

## 公开边界

本仓库只接受符合 `schemas/public-brief.schema.json` 的公共 JSON，不保存或发布：

- 账户地址或个人主页
- 总资产、可用资金或持仓价值
- 当前持仓数量或建议操作金额
- 登录凭据、机器人凭据或聊天目标
- 私有报告、本机路径或研究运行日志

所有公共对象均禁止未声明的额外字段。校验器还会拒绝钱包地址、电子邮箱和本机用户目录。

## 发布研究信号

准备一份符合协议的 JSON，然后运行：

```bash
python3 scripts/validate_public_brief.py path/to/public-brief.json
python3 scripts/publish_public_brief.py \
  path/to/public-brief.json --site-data site/data
python3 scripts/validate_public_brief.py site/data
```

发布脚本将以 `brief_id` 写入不可变的历史文件，同时更新 `site/data/latest.json` 和 `site/data/index.json`。提交并推送这些公开文件后，GitHub Actions 会先验证数据，再部署 Pages。

## JSON 核心字段

每个 `actions` 元素包含：

- `action`：`BUY`、`ADD` 或 `SELL`
- `outcome`：`YES` 或 `NO`
- `polymarket_url` 与 `link_verified_at`
- `fair_price`、`current_price` 与 `price_gap`
- `confidence` 和 `reason`
- `evidence`：来源 URL、标题、核心内容摘要及概率影响
- `probability_tree`：最终采用的递归贝叶斯/全概率树，以及证据与节点的对应关系

`price_gap` 必须严格等于 `fair_price - current_price`。价格均表示当前 `outcome` 的份额价格，范围为 0–1。

## 贝叶斯树格式

公共协议 `1.1` 直接保存可重新计算的递归树，不保存具体页面布局。每个节点都包含稳定 ID、类型、标题、说明、该节点的最终概率以及 `evidence_refs`。

支持四类节点：

- `estimate`：证据直接支持的点估计。
- `partition`：互斥且完备的情景分支；所有 `weight` 之和必须为 1。
- `bayes_update`：从一个完整的 `prior` 子树开始，按顺序应用似然并保存每一步后验概率。
- `complement`：一个子节点概率的补集。

树使用嵌套 `child`、`prior` 和 `branches` 表达父子关系；情景分支通过 `evidence_refs` 说明权重依据。每条公开证据拥有独立 ID，并且必须至少被一个节点、分支或贝叶斯更新步骤引用。校验器会重新计算全部内部节点，要求根节点概率等于该方向的 `fair_price`。当前网页暂不绘制树，后续展示层可以直接遍历这一结构，而无需改变历史 JSON。

## 本地预览

```bash
python3 -m http.server 8080 --directory site
```

然后打开 <http://localhost:8080/>。

本网站不自动提交订单。概率估算和研究信号不保证结果。
