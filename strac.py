"""STRAC（戦略会計）の計算ロジック。

西順一郎『STRAC会計』のポケコンプログラム「STRAC-T/M/1」(J.NISHI 著) を
基にした純粋な計算関数群。Streamlit などの UI には依存しないため、
そのまま単体テストできる。

基本恒等式:
    PQ = VQ + F + G
    (P - V) * Q = F + G
    M * Q       = F + G

記号:
    P  単価            V  単位変動費        Q  数量
    F  固定費          G  利益              M  単位限界利益 (= P - V)
    PQ 売上            VQ 変動費合計        MQ 限界利益合計 (= M * Q)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# MQ = F + G の整合性チェックで許容する誤差。
CONSISTENCY_TOLERANCE = 0.1


@dataclass(frozen=True)
class StracValues:
    """STRAC の 5 つの基本値と、そこから導かれる派生値。"""

    p: float
    v: float
    q: float
    f: float
    g: float

    # --- 派生値 ---
    @property
    def m(self) -> float:
        """単位限界利益 M = P - V。"""
        return self.p - self.v

    @property
    def pq(self) -> float:
        return self.p * self.q

    @property
    def vq(self) -> float:
        return self.v * self.q

    @property
    def mq(self) -> float:
        return self.m * self.q

    # --- 比率（定義できない場合は None） ---
    @property
    def v_percent(self) -> Optional[float]:
        """変動費率 V% = V / P * 100。"""
        return self.v / self.p * 100 if self.p != 0 else None

    @property
    def fm_percent(self) -> Optional[float]:
        """損益分岐点比率 FM = F / MQ * 100。"""
        return self.f / self.mq * 100 if self.mq != 0 else None

    @property
    def q0(self) -> Optional[float]:
        """損益分岐点数量 Q0 = F / M。"""
        return self.f / self.m if self.m != 0 else None

    @property
    def is_consistent(self) -> bool:
        """MQ = F + G が（許容誤差内で）成り立つか。"""
        return abs(self.mq - (self.f + self.g)) <= CONSISTENCY_TOLERANCE


def solve_basic(
    p: Optional[float],
    v: Optional[float],
    q: Optional[float],
    f: Optional[float],
    g: Optional[float],
) -> StracValues:
    """空欄(None)を 1 つだけ許し、恒等式 (P-V)*Q = F+G から逆算する。

    原典 STRAC-1 の 130〜170 行に対応:
        P 空欄: P = (V*Q + F + G) / Q
        V 空欄: V = (P*Q - F - G) / Q
        Q 空欄: Q = (F + G) / (P - V)
        F 空欄: F = P*Q - V*Q - G
        G 空欄: G = P*Q - V*Q - F

    空欄が 2 つ以上ある場合は ValueError を送出する。
    """
    inputs = {"P": p, "V": v, "Q": q, "F": f, "G": g}
    blanks = [name for name, val in inputs.items() if val is None]

    if len(blanks) > 1:
        raise ValueError(
            f"空欄は1つまでにしてください。現在 {', '.join(blanks)} が空欄です。"
        )

    if p is None:
        p = (v * q + f + g) / q if q != 0 else 0.0
    elif v is None:
        v = (p * q - f - g) / q if q != 0 else 0.0
    elif q is None:
        q = (f + g) / (p - v) if (p - v) != 0 else 0.0
    elif f is None:
        f = p * q - v * q - g
    elif g is None:
        g = p * q - v * q - f

    return StracValues(p, v, q, f, g)


@dataclass(frozen=True)
class TStracResult:
    """T-STRAC: 目標値と現状値の差分（変化額・変化率）。

    変化率は分母が 0 のとき None。
    """

    target: StracValues
    delta: dict[str, float]
    delta_percent: dict[str, Optional[float]]


def compute_tstrac(current: StracValues, target: StracValues) -> TStracResult:
    """現状値 current に対する目標値 target の差分を計算する（原典 T-STRAC）。"""
    pairs = {
        "P": (target.p, current.p),
        "V": (target.v, current.v),
        "Q": (target.q, current.q),
        "F": (target.f, current.f),
        "G": (target.g, current.g),
    }
    delta = {key: t - c for key, (t, c) in pairs.items()}
    delta_percent = {
        key: (delta[key] / c * 100 if c != 0 else None)
        for key, (_t, c) in pairs.items()
    }
    return TStracResult(target=target, delta=delta, delta_percent=delta_percent)


@dataclass(frozen=True)
class HStracResult:
    """H-STRAC: 基準期から比較期への各要素の変化を要因分解した結果。"""

    pk: float  # 単価要因
    vk: float  # 変動費要因
    mk: float  # 限界利益要因
    qk: float  # 数量要因
    pqk: float  # 売上の変化   (AK)
    vqk: float  # 変動費合計の変化 (BK)
    mqk: float  # 限界利益合計の変化 (CK)
    fk: float  # 固定費の変化
    gk: float  # 利益の変化 (= MQK - FK)


def compute_hstrac(base: StracValues, new: StracValues) -> HStracResult:
    """基準期 base から比較期 new への変化を要因分解する（原典 H-STRAC 760〜840）。

    PK/VK/MK/QK は両期の平均で重み付けした要因分析。GK は原典に従い
    GK = CK - FK（利益の変化 = 限界利益の変化 - 固定費の変化）で求める。
    """
    q_sum = new.q + base.q
    return HStracResult(
        pk=(new.p - base.p) * q_sum / 2,
        vk=(new.v - base.v) * q_sum / 2,
        mk=(new.m - base.m) * q_sum / 2,
        qk=(new.q - base.q) * (new.m + base.m) / 2,
        pqk=new.pq - base.pq,
        vqk=new.vq - base.vq,
        mqk=new.mq - base.mq,
        fk=new.f - base.f,
        gk=(new.mq - base.mq) - (new.f - base.f),
    )


# MQ-Strategy で生成する行数の上限（暴走防止）。
MQ_STRATEGY_MAX_ROWS = 101


def compute_mq_strategy(
    mq: float,
    v: float,
    start: float,
    end: float,
    step: float,
    by_price: bool,
) -> list[dict[str, float]]:
    """一定の MQ を保つ P と Q の組み合わせ表を生成する（原典 MQ-STRATEGY）。

    by_price=True: P を start→end まで step 刻みで動かし、必要な Q を求める。
    by_price=False: Q を動かし、必要な M（および P）を求める。

    step が 0 の場合は ValueError。浮動小数点の累積誤差を避けるため、
    刻み幅から反復回数を整数で算出してインデックス基準でループする。
    """
    if step == 0:
        raise ValueError("Step cannot be 0")

    n_steps = int(round(abs(end - start) / abs(step))) + 1
    n_steps = min(n_steps, MQ_STRATEGY_MAX_ROWS)

    rows: list[dict[str, float]] = []
    for i in range(n_steps):
        if by_price:
            p = start + i * step
            m = p - v
            q = round(mq / m, 1) if m != 0 else 0.0
        else:
            q = start + i * step
            m = round(mq / q, 1) if q != 0 else 0.0
            p = v + m
        rows.append(
            {
                "P": round(p, 1),
                "V": round(v, 1),
                "M": round(m, 1),
                "Q": round(q, 1),
                "PQ": round(p * q, 1),
                "VQ": round(v * q, 1),
                "MQ": round(m * q, 1),
            }
        )
    return rows
