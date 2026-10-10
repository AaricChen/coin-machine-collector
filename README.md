# 纪念币机后台数据自动采集

在 Mac 上定时调用纪念币机后台管理接口，自动登录、拉取机器状态与轨道库存，并写入本地 SQLite。

详细设计见 [docs/DESIGN.md](docs/DESIGN.md)。

## 快速开始

```bash
cd coin_machine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/.env.example .env   # 填入真实账号密码
python src/login_probe.py     # 验证登录并查看账号/设备摘要
python src/main.py --mode once
```

数据文件：`data/coin_machine.db`；日志：`logs/`。

## 运行模式

| 模式 | 命令 |
| --- | --- |
| 单次采集 | `python src/main.py --mode once` |
| 进程内定时（APScheduler） | `python src/main.py --mode schedule` |

生产环境更推荐 macOS **launchd** 定时调用 `--mode once`，示例 plist 见 [deploy/com.coinmachine.collector.plist.example](deploy/com.coinmachine.collector.plist.example)。

## 配置

- 业务配置：`config/settings.yaml`（已对接 `ads.hfyuwo.com` RuoYi 登录：`/captchaImage` + `/login`）
- 敏感凭据：`.env` 中的 `COIN_MACHINE_USERNAME` / `COIN_MACHINE_PASSWORD`，或 macOS Keychain（见 settings 中 `credentials.keychain_service`）
- 算术验证码：默认自动识别（macOS Vision；可选 `pip install -r requirements-captcha.txt` 提高成功率）
- 调试：`COIN_MACHINE_CAPTCHA_CODE=8 python src/login_probe.py` 可手动指定一次验证码答案

### 登录后可用的主要数据

| 接口 | 说明 |
| --- | --- |
| `POST /login` | 返回 JWT `token`（`Authorization: Bearer …`，请求头 `isToken: true`） |
| `GET /getInfo` | 用户、角色、`permissions` 权限列表 |
| `GET /vending/facility/list` | 纪念币机列表（`facilityId`、`facilityNumber`、库存/连接状态等） |

## 许可证

Private — 仅供内部运维使用。
