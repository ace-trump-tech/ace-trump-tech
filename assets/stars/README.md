# 项目 Star 徽章

个人主页的项目表格引用本目录 SVG，避免动态徽章服务失败时显示 `invalid` 或令牌池错误。

数据直接来自 GitHub API 的 `stargazers_count`。工作流每 6 小时尝试更新，也可以在 Actions 中手动运行 **Update repository star badges**。请求失败时保留上一份有效数据；数字未变时不重复提交。`stats.json` 记录数据更新时间。

新增项目时，修改 `scripts/update_star_badges.py` 的 `REPOSITORIES`，并在主页表格引用对应 SVG。本地更新可在已登录 GitHub CLI 后运行 `python scripts/update_star_badges.py`；工作流使用 GitHub 自带的临时令牌，无需配置个人密钥。
