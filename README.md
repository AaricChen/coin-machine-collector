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
# 编辑 config/settings.yaml，填入抓包得到的接口路径与 Token 字段
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

- 业务配置：`config/settings.yaml`
- 敏感凭据：`.env` 中的 `COIN_MACHINE_USERNAME` / `COIN_MACHINE_PASSWORD`，或 macOS Keychain（见 settings 中 `credentials.keychain_service`）

## 许可证

Private — 仅供内部运维使用。
