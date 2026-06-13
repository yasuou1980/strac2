# STRAC Calculator

STRAC（戦略会計）の計算を行う Streamlit アプリです。西順一郎『利益が見える戦略会計
STRAC』のポケットコンピュータ用プログラム「STRAC-T/M/1」(J.NISHI 著) を Web アプリ
として再実装したものです。

## STRAC とは

売上・原価・利益の関係を次の恒等式で捉える管理会計の手法です。

```
PQ = VQ + F + G          売上 = 変動費 + 固定費 + 利益
(P - V) * Q = F + G      限界利益 = 固定費 + 利益
M * Q       = F + G      MQ = F + G
```

| 記号 | 意味 | 記号 | 意味 |
|------|------|------|------|
| P | 単価 | F | 固定費 |
| V | 単位変動費 | G | 利益 |
| Q | 数量 | M | 単位限界利益 (= P − V) |
| PQ | 売上 | MQ | 限界利益合計 (= M × Q) |
| VQ | 変動費合計 | | |

## 機能

- **Basic Calculation** — P/V/Q/F/G のうち 1 つを空欄にすると、恒等式から自動逆算。
  あわせて V%（変動費率）、FM（損益分岐点比率）、Q0（損益分岐点数量）を表示。
- **T-STRAC（目標分析）** — 現状値に対する目標値の差分（変化額・変化率）を算出。
- **H-STRAC（時系列分析）** — 基準期と比較期の差を、単価・変動費・数量などの要因に分解。
- **MQ-Strategy** — 一定の MQ を保つ P と Q の組み合わせ表とグラフ（P 戦略 / Q 戦略）。

## 構成

| ファイル | 役割 |
|----------|------|
| `strac.py` | 計算ロジック（UI 非依存・テスト可能な純粋関数群） |
| `app.py` | Streamlit UI |
| `tests/test_strac.py` | 計算ロジックのテスト |

## ローカルでの実行

### 必要な環境
- Python 3.9+
- pip

### 手順
```bash
git clone https://github.com/yasuou1980/strac2.git
cd strac2

pip install -r requirements.txt

streamlit run app.py
```

## テスト
```bash
python tests/test_strac.py
# pytest を使う場合:
pytest
```
