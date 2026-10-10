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
PYTHONPATH=src python src/list_facilities.py --all --compact   # 设备列表
PYTHONPATH=src python src/list_track_share.py 3222 --compact   # 货道配货/库存
PYTHONPATH=src python src/sync_goods_orders.py full --begin 2026-10-01 --end 2026-10-31 --save-state --compact
PYTHONPATH=src python src/sync_goods_orders.py incremental --compact   # 定时增量
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
| `GET /vending/track/share/{facilityId}` | 单台设备货道配货与库存（`data.list` + `data.facility`） |
| `GET /vending/goods_order/list` | 订单明细分页（按 `params[beginCreateTime]` / `endCreateTime`） |
| `GET /vending/goods_order/listAll` | 同区间金额/渠道汇总（**不是**订单全量列表） |

### 业务 API 封装（`src/hfyuwo/`）

后续新接口按同一模式扩展：**模型**（`hfyuwo/models/`）+ **独立函数**（`hfyuwo/services/`）。

```python
from hfyuwo import create_context
from hfyuwo.services.facility import list_facilities_page, list_all_facilities
from hfyuwo.services.track import get_facility_track_share, list_track_share_items
from hfyuwo.services.goods_order import sync_goods_orders_full, sync_goods_orders_incremental
from hfyuwo.models.goods_order import GoodsOrderTimeRange
from hfyuwo.services.user import get_user_info

page = list_facilities_page(1, 50)   # -> RuoYiPage[Facility]
devices = list_all_facilities()
info = get_user_info()

# 复用同一登录会话（避免重复登录）
ctx = create_context()
list_facilities_page(1, 50, ctx=ctx)
```

新增接口步骤：在 `models/` 定义 Pydantic 模型 → 在 `services/` 写 `xxx()` 函数（内部用 `ctx.client.get_json`）→ CLI 脚本仅负责 argparse 与打印 JSON。

## 许可证

Private — 仅供内部运维使用。
