# UR団地 空室チェッカー

`check_ur_vacancy.py` は、CSVで管理している団地リストに対してUR賃貸の公式APIを叩き、
**2DK / 2LDK / 3DK / 3LDK** の空室をまとめてCSV・Excelに出力するスクリプトです。

---

## ディレクトリ構成

```
rk/
├── code/
│   ├── check_ur_vacancy.py   # 本スクリプト
│   └── README.md             # 本ドキュメント
└── ur_agent/
    ├── ur_danchi.csv          # 団地リスト（入力）
    ├── ur_danchi.xlsx         # 団地リスト（参考用Excel）
    └── aval/
        ├── vacancy_YYYYMMDD_HHMMSS.csv    # 出力CSV
        └── vacancy_YYYYMMDD_HHMMSS.xlsx   # 出力Excel
```

---

## 必要な環境

| 項目 | 要件 |
|------|------|
| Python | 3.9 以上 |
| 外部ライブラリ | `openpyxl`（Excel出力に必要） |

標準ライブラリのみで動くため、`openpyxl` がなくてもCSVは出力されます。

---

## セットアップ

### openpyxl のインストール（初回のみ）

macOS（Homebrewで管理されているPython環境）の場合：

```bash
# 仮想環境を作成してインストール（推奨）
python3 -m venv ~/.venv/ur
source ~/.venv/ur/bin/activate
pip install openpyxl

# 以降の実行時も同じ仮想環境を使う
source ~/.venv/ur/bin/activate
```

または一時的な仮想環境（毎回不要）：

```bash
python3 -m venv /tmp/xlenv
/tmp/xlenv/bin/pip install openpyxl -q
```

---

## 実行方法

### 基本実行（リポジトリルートから）

```bash
# 仮想環境が有効な場合
python3 code/check_ur_vacancy.py

# /tmp/xlenv を使う場合
/tmp/xlenv/bin/python3 code/check_ur_vacancy.py
```

### 実行例

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

## 出力ファイル

ファイル名はタイムスタンプ形式で、実行のたびに新しいファイルが生成されます。

```
vacancy_20260810_194105.csv
vacancy_20260810_194105.xlsx
```

### 出力列

| 列名 | 内容 |
|------|------|
| 番号 | 団地リストの連番 |
| 団地名 | UR団地名 |
| 最寄り駅 | 最寄り駅（二子玉川から） |
| 二子玉川からの所要時間 | 乗車時間の目安 |
| 間取り | 2DK / 2LDK / 3DK / 3LDK（空室なしの場合は「なし」） |
| 部屋名 | 棟・部屋番号 |
| 月額家賃 | 例: 152,400円 |
| 共益費 | 例: 3,800円 |
| 床面積 | 例: 61㎡ |
| 階 | 例: 10階 |
| URページ | 団地詳細ページURL（Excelではリンク付き） |

### Excelの見た目

- **緑色の行** → 空室あり（ヒット）
- **グレー/白の行** → 空室なし
- ヘッダー行は固定（スクロールしても表示される）
- URページ列はクリック可能なハイパーリンク

---

## カスタマイズ

`check_ur_vacancy.py` の冒頭の設定値を変更することで動作を調整できます。

```python
# 対象とする間取り
TARGET_TYPES = {"2DK", "2LDK", "3DK", "3LDK"}

# リクエスト間隔（秒）：サーバー負荷軽減のため変更しないことを推奨
REQUEST_INTERVAL = 1.0

# 入力CSVのパス（デフォルトはスクリプトから相対的に解決）
CSV_INPUT = Path(__file__).parent.parent / "ur_agent" / "ur_danchi.csv"

# 出力先ディレクトリ
OUTPUT_DIR = Path(__file__).parent.parent / "ur_agent" / "aval"
```

---

## 定期実行（cron）

毎日朝8時に自動チェックする例：

```bash
# crontab -e で以下を追加
0 8 * * * /tmp/xlenv/bin/python3 /path/to/rk/code/check_ur_vacancy.py >> /tmp/ur_check.log 2>&1
```

---

## 仕組み

1. `ur_danchi.csv` の「団地URページ」列からURLパターン（例: `40_2690.html`）を解析し、
   `shisya=40`, `danchi=269` のパラメータを自動抽出
2. UR公式API `https://chintai.r6.ur-net.go.jp/chintai/api/bukken/detail/detail_bukken_room/`
   にPOSTリクエストを送信
3. レスポンスのJSONから `type` フィールドで間取りを絞り込み
4. 全ページ（ページネーション対応）を取得してから出力

> ページURLとAPIパラメータの対応：`XX_YYYY.html` → `shisya=XX`, `danchi=int(YYYY)/10`
> 例: `40_2690.html` → `shisya=40`, `danchi=269`
