# UR小区空房查询工具

`check_ur_vacancy.py` 读取 CSV 管理的小区列表，调用 UR 租房官方 API，
批量查询 **2DK / 2LDK / 3DK / 3LDK** 的空房情况，并输出 CSV 和 Excel 文件。

---

## 目录结构

```
rk/
├── code/
│   ├── check_ur_vacancy.py   # 本脚本
│   └── README.md             # 本文档
└── ur_agent/
    ├── ur_danchi.csv          # 小区列表（输入）
    ├── ur_danchi.xlsx         # 小区列表（参考用 Excel）
    └── aval/
        ├── vacancy_YYYYMMDD_HHMMSS.csv    # 输出 CSV
        └── vacancy_YYYYMMDD_HHMMSS.xlsx   # 输出 Excel
```

---

## 环境要求

| 项目 | 要求 |
|------|------|
| Python | 3.9 及以上 |
| 第三方库 | `openpyxl`（输出 Excel 需要） |

若未安装 `openpyxl`，脚本仍可正常运行，但只输出 CSV，不输出 Excel。

---

## 初次配置

### 安装 openpyxl（仅需一次）

macOS（Homebrew 管理的 Python 环境）推荐使用虚拟环境：

```bash
# 创建虚拟环境并安装
python3 -m venv ~/.venv/ur
source ~/.venv/ur/bin/activate
pip install openpyxl

# 之后每次运行前激活环境即可
source ~/.venv/ur/bin/activate
```

或使用临时虚拟环境（无需每次激活）：

```bash
python3 -m venv /tmp/xlenv
/tmp/xlenv/bin/pip install openpyxl -q
```

---

## 执行方法

### 从仓库根目录运行

```bash
# 虚拟环境已激活时
python3 code/check_ur_vacancy.py

# 使用 /tmp/xlenv 时
/tmp/xlenv/bin/python3 code/check_ur_vacancy.py
```

### 执行示例输出

```
=== UR空室チェック開始: 20260810_194105 ===
対象間取り: 2DK, 2LDK, 3DK, 3LDK
入力CSV: /path/to/ur_agent/ur_danchi.csv

[1/12] かわさきテクノピア堀川町ハイツ を確認中...
  → 対象間取りの空室なし
...
[12/12] 港北ニュータウン サントゥール中川 を確認中...
  → 1件 ヒット (['2LDK'])
CSV保存: /path/to/ur_agent/aval/vacancy_20260810_194105.csv
Excel保存: /path/to/ur_agent/aval/vacancy_20260810_194105.xlsx

=== 完了 ===
総団地数: 12
空室あり: 1件
出力先: /path/to/ur_agent/aval
```

---

## 输出文件说明

文件名包含时间戳，每次执行生成新文件，不覆盖历史记录：

```
vacancy_20260810_194105.csv
vacancy_20260810_194105.xlsx
```

### 输出列说明

| 列名 | 内容 |
|------|------|
| 番号 | 小区列表序号 |
| 団地名 | UR 小区名称 |
| 最寄り駅 | 最近车站（来自二子玉川） |
| 二子玉川からの所要時間 | 乘车时间参考 |
| 間取り | 户型（2DK / 2LDK / 3DK / 3LDK，无空房时显示「なし」） |
| 部屋名 | 楼栋·房间号 |
| 月額家賃 | 月租金，例：152,400円 |
| 共益費 | 管理费，例：3,800円 |
| 床面積 | 建筑面积，例：61㎡ |
| 階 | 楼层，例：10階 |
| URページ | 小区详情页 URL（Excel 中为可点击链接） |

### Excel 样式说明

- **绿色行** → 有空房（命中）
- **灰/白行** → 无空房
- 首行冻结，滚动时始终可见
- URページ 列为超链接，可直接点击跳转

---

## 自定义配置

修改 `check_ur_vacancy.py` 开头的配置项即可调整行为：

```python
# 目标户型
TARGET_TYPES = {"2DK", "2LDK", "3DK", "3LDK"}

# 请求间隔（秒），建议不低于 1.0，避免对服务器造成压力
REQUEST_INTERVAL = 1.0

# 输入 CSV 路径（默认相对于脚本位置自动解析）
CSV_INPUT = Path(__file__).parent.parent / "ur_agent" / "ur_danchi.csv"

# 输出目录
OUTPUT_DIR = Path(__file__).parent.parent / "ur_agent" / "aval"
```

---

## 定时自动执行（cron）

每天早上 8 点自动查询的示例：

```bash
# 执行 crontab -e，添加以下一行
0 8 * * * /tmp/xlenv/bin/python3 /path/to/rk/code/check_ur_vacancy.py >> /tmp/ur_check.log 2>&1
```

---

## 实现原理

1. 解析 `ur_danchi.csv` 中「団地URページ」列的 URL（如 `40_2690.html`），自动提取
   `shisya=40`、`danchi=269` 参数
2. 向 UR 官方 API POST 请求：
   `https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/`
3. 从返回 JSON 的 `type` 字段筛选目标户型
4. 自动翻页，获取全部空房数据后再输出

> URL 与 API 参数的对应规则：`XX_YYYY.html` → `shisya=XX`，`danchi=int(YYYY)/10`
> 例：`40_2690.html` → `shisya=40`，`danchi=269`
