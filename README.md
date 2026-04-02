# Tieba_Sgin

百度贴吧自动签到脚本，支持：

- 多账号签到（多 `BDUSS`）
- 失败重试
- 推送签到结果到 Server酱（微信）
- 适配本地 Python 与青龙面板环境变量配置

---

## 功能说明

- 自动获取关注贴吧列表
- 区分「已签到 / 新签到成功 / 签到失败」
- 输出并推送详细签到报告（含签到排名）
- 可配置最大重试次数，避免无限重试

---

## 运行环境

- Python 3.6+
- 依赖：
  - `requests`
  - `pretty_errors`（可选，缺失不影响功能）

安装依赖示例：

```bash
pip install requests pretty_errors
```

---

## 配置方式（推荐：环境变量）

脚本支持以下环境变量：

- `TIEBA_BDUSS`：贴吧账号 `BDUSS`，支持多账号
  - 分隔符支持：`,` / `&` / 换行
  - 可从浏览器登录百度后，在 Cookie 中获取 `BDUSS` 值
- `TIEBA_STOKEN`：可选，账号 `STOKEN`
- `SERVERCHAN_SCKEY`：可选，Server酱 `SCKEY`（配置后才会推送）
- `TIEBA_MAX_RETRY`：可选，最大重试次数，默认 `3`

### 多账号示例

```bash
export TIEBA_BDUSS="bduss_a,bduss_b"
export TIEBA_STOKEN=""
export SERVERCHAN_SCKEY="SCTxxxxxxxx"
export TIEBA_MAX_RETRY="3"
python Tieba_Sgin.py
```

---

## 青龙面板示例

在青龙中新增任务前，先安装依赖并设置环境变量：

1. 安装依赖：`requests`（`pretty_errors` 可选）
2. 配置环境变量：`TIEBA_BDUSS`、`TIEBA_STOKEN`、`SERVERCHAN_SCKEY`、`TIEBA_MAX_RETRY`
3. 新建定时任务执行 `python Tieba_Sgin.py`

---

## 结果说明

脚本会输出：

- 总贴吧数量
- 签到成功数量
- 签到失败数量
- 已签到数量
- 详细贴吧列表（成功/失败/已签到）

如已配置 `SERVERCHAN_SCKEY`，同样内容会推送到微信。

---

## 注意事项

- `BDUSS` 属于敏感凭据，请勿提交到仓库。
- 若不使用环境变量，脚本中仍保留了占位写法，建议仅用于本地临时调试。
- 百度接口策略可能变动，若失效请结合返回信息排查。
