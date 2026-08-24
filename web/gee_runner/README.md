# GEE Runner 模块

访问地址：`/gee-runner`

该模块已接入 geeToOGE Flask 应用，提供 GEE JavaScript 执行、自动修复、CSV/JSON 批量运行、实时日志、历史批次和断点续跑。

配置：

- 在本目录创建 `.env`，设置 `GEE_PRIVATE_KEY_FILE` 指向 Earth Engine 服务账号 JSON。
- 设置 `GEE_PROJECT`、代理和 OpenAI/Codex API 配置（如需要自动修复）。
- 服务由上级 `web/app.py` 统一启动，不要单独启动 `backend.py`。

接口统一使用 `/api/gee-runner/` 前缀。
