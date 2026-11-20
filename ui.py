"""ui.py —— 四个小组系统共用的界面组件

只做两件事：把页面变好看，把数据结构画出来。
不包含任何业务逻辑，业务逻辑在各组的 app.py 里。
"""
from __future__ import annotations

import html
import json
import math
from typing import Any, Iterable, Sequence

import streamlit as st

_LANG = "zh"


def set_lang(lang: str) -> None:
    """Switch built-in visual labels between Chinese and English."""
    global _LANG
    _LANG = "en" if str(lang).lower().startswith("en") else "zh"


def _t(zh: str, en: str) -> str:
    return en if _LANG == "en" else zh


# ---------------------------------------------------------------------------
# 主题与基础样式
# ---------------------------------------------------------------------------
def inject_css(accent: str = "#5eead4", accent2: str = "#a78bfa") -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --accent: {accent};
            --accent2: {accent2};
            --bg: #070b14;
            --panel: rgba(17, 24, 39, 0.72);
            --panel-solid: #111827;
            --line: rgba(148, 163, 184, 0.18);
            --text: #e5eef7;
            --muted: #8fa3b8;
            --ok: #34d399;
            --warn: #fbbf24;
            --bad: #fb7185;
        }}
        html, body, [class*="css"] {{
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC",
                         "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", sans-serif;
        }}
        .stApp {{
            background:
                radial-gradient(900px 520px at 12% -8%, {accent}1f, transparent 60%),
                radial-gradient(820px 480px at 88% 0%, {accent2}1a, transparent 58%),
                linear-gradient(180deg, #070b14 0%, #080d18 45%, #060a12 100%);
            color: var(--text);
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stToolbar"] {{ right: 12px; }}
        #MainMenu, footer {{ visibility: hidden; }}
        .block-container {{ padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1320px; }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0b1220 0%, #080d17 100%);
            border-right: 1px solid var(--line);
        }}
        [data-testid="stSidebar"] .block-container {{ padding-top: 1.1rem; }}

        h1, h2, h3, h4 {{ color: var(--text); letter-spacing: -0.02em; }}
        p, li, span, label {{ color: var(--text); }}
        a {{ color: var(--accent); }}
        hr {{ border-color: var(--line); }}

        .sl-hero {{
            position: relative;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 26px 28px 22px;
            margin-bottom: 18px;
            background:
                radial-gradient(520px 240px at 92% -20%, {accent}30, transparent 65%),
                radial-gradient(420px 220px at 8% 120%, {accent2}22, transparent 62%),
                linear-gradient(135deg, rgba(19, 28, 45, 0.92), rgba(10, 16, 28, 0.88));
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
        }}
        .sl-hero::after {{
            content: ""; position: absolute; inset: 0;
            background-image: linear-gradient(rgba(148,163,184,.05) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(148,163,184,.05) 1px, transparent 1px);
            background-size: 34px 34px;
            mask-image: linear-gradient(180deg, rgba(0,0,0,.6), transparent 80%);
            pointer-events: none;
        }}
        .sl-eyebrow {{
            display: inline-flex; align-items: center; gap: 8px;
            font-size: 12px; letter-spacing: .16em; text-transform: uppercase;
            color: var(--accent); font-weight: 700;
        }}
        .sl-eyebrow i {{ width: 7px; height: 7px; border-radius: 50%; background: var(--accent);
                         box-shadow: 0 0 0 4px {accent}22; display: inline-block; }}
        .sl-hero h1 {{ font-size: 34px; line-height: 1.18; margin: 10px 0 6px; font-weight: 750; }}
        .sl-hero h1 small {{ display: block; font-size: 16px; color: var(--muted); font-weight: 500;
                             letter-spacing: 0; margin-top: 6px; }}
        .sl-hero p {{ color: var(--muted); max-width: 780px; margin: 0; font-size: 14.5px; line-height: 1.75; }}

        .sl-chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
        .sl-chip {{
            border: 1px solid {accent}33; background: {accent}12; color: var(--accent);
            border-radius: 999px; padding: 5px 11px; font-size: 12px; font-weight: 600;
        }}
        .sl-chip.muted {{ border-color: var(--line); background: rgba(148,163,184,.08); color: var(--muted); }}
        .sl-chip.warn {{ border-color: #fbbf2440; background: #fbbf2414; color: var(--warn); }}
        .sl-chip.bad {{ border-color: #fb718540; background: #fb718514; color: var(--bad); }}
        .sl-chip.ok {{ border-color: #34d39940; background: #34d39914; color: var(--ok); }}

        .sl-kpis {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 4px 0 20px; }}
        .sl-kpi {{
            border: 1px solid var(--line); border-radius: 16px; padding: 14px 16px;
            background: linear-gradient(160deg, rgba(23, 33, 51, .85), rgba(12, 18, 30, .78));
        }}
        .sl-kpi .lab {{ color: var(--muted); font-size: 12px; letter-spacing: .04em; }}
        .sl-kpi .val {{ color: var(--text); font-size: 25px; font-weight: 750; margin-top: 4px;
                        font-variant-numeric: tabular-nums; }}
        .sl-kpi .sub {{ color: var(--muted); font-size: 11.5px; margin-top: 3px; }}
        .sl-kpi .val em {{ font-style: normal; font-size: 14px; color: var(--muted); margin-left: 3px; }}
        .sl-kpi.accent {{ border-color: {accent}40; box-shadow: inset 0 0 0 1px {accent}12, 0 10px 30px {accent}0f; }}
        .sl-kpi.accent .val {{ color: var(--accent); }}

        .sl-section {{ display: flex; align-items: flex-end; justify-content: space-between; gap: 14px;
                       margin: 6px 0 12px; }}
        .sl-section h3 {{ margin: 0; font-size: 18px; font-weight: 700; }}
        .sl-section p {{ margin: 4px 0 0; color: var(--muted); font-size: 12.5px; }}
        .sl-section .right {{ color: var(--muted); font-size: 12px; white-space: nowrap; }}

        .sl-card {{
            border: 1px solid var(--line); border-radius: 18px; padding: 16px 18px;
            background: linear-gradient(165deg, rgba(20, 29, 46, .8), rgba(11, 17, 29, .75));
            margin-bottom: 12px;
        }}
        .sl-card.tight {{ padding: 12px 14px; }}
        .sl-card h4 {{ margin: 0 0 6px; font-size: 14.5px; }}
        .sl-card p {{ margin: 0; color: var(--muted); font-size: 12.5px; line-height: 1.65; }}

        .sl-visual {{
            border: 1px dashed rgba(148,163,184,.22); border-radius: 14px; padding: 14px;
            background: rgba(8, 13, 23, .55); overflow-x: auto;
        }}
        .sl-visual-label {{ color: var(--muted); font-size: 11px; letter-spacing: .08em;
                            text-transform: uppercase; margin-bottom: 9px; }}
        .sl-empty {{ color: var(--muted); font-size: 12.5px; padding: 10px 2px; }}

        /* 数组 */
        .sl-array {{ display: flex; gap: 6px; align-items: stretch; flex-wrap: wrap; }}
        .sl-cell {{ min-width: 46px; border: 1px solid var(--line); border-radius: 9px;
                    background: rgba(30, 41, 59, .55); text-align: center; padding-bottom: 3px; }}
        .sl-cell .v {{ padding: 8px 8px 2px; font-size: 13px; font-weight: 650; color: var(--text);
                       max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .sl-cell .i {{ font-size: 9.5px; color: var(--muted); border-top: 1px solid var(--line);
                       padding-top: 2px; }}
        .sl-cell.hl {{ border-color: var(--accent); background: {accent}1c; box-shadow: 0 0 0 1px {accent}40; }}
        .sl-cell.hl .v {{ color: var(--accent); }}
        .sl-cell.ghost {{ opacity: .38; border-style: dashed; }}

        /* 链表 */
        .sl-linked {{ display: flex; align-items: center; gap: 4px; flex-wrap: wrap; }}
        .sl-node {{ border: 1px solid {accent}55; background: {accent}16; color: var(--text);
                    border-radius: 10px; padding: 8px 11px; font-size: 12.5px; font-weight: 600;
                    max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .sl-arrow {{ color: var(--accent); font-size: 15px; opacity: .85; }}
        .sl-null {{ color: var(--muted); font-size: 11px; border: 1px dashed var(--line);
                    border-radius: 8px; padding: 7px 8px; }}

        /* 栈 */
        .sl-stack {{ display: flex; flex-direction: column-reverse; gap: 5px; align-items: flex-start; }}
        .sl-stack .item {{ border: 1px solid var(--line); background: rgba(30,41,59,.55);
                           border-radius: 8px; padding: 6px 12px; min-width: 120px; font-size: 12px; }}
        .sl-stack .item.top {{ border-color: var(--accent); background: {accent}16; color: var(--accent); }}
        .sl-stack .cap {{ color: var(--muted); font-size: 10px; margin-left: 6px; }}

        /* 队列 / 双端 */
        .sl-queue {{ display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }}
        .sl-queue .qitem {{ border: 1px solid var(--line); border-radius: 8px; padding: 7px 10px;
                            background: rgba(30,41,59,.5); font-size: 12px; }}
        .sl-queue .qitem.head {{ border-color: var(--accent); color: var(--accent); background: {accent}15; }}
        .sl-queue .qtag {{ color: var(--muted); font-size: 10px; }}

        /* 哈希桶 */
        .sl-buckets {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 7px; }}
        .sl-bucket {{ border: 1px solid var(--line); border-radius: 9px; padding: 6px 8px;
                      background: rgba(30,41,59,.35); min-height: 46px; }}
        .sl-bucket .b {{ color: var(--muted); font-size: 9.5px; letter-spacing: .05em; }}
        .sl-bucket .kv {{ font-size: 10.5px; color: var(--text); margin-top: 2px; white-space: nowrap;
                          overflow: hidden; text-overflow: ellipsis; }}
        .sl-bucket .kv b {{ color: var(--accent); font-weight: 600; }}

        /* 堆 / 树 */
        .sl-levels {{ display: flex; flex-direction: column; gap: 6px; align-items: center; }}
        .sl-level {{ display: flex; gap: 5px; justify-content: center; flex-wrap: nowrap; }}
        .sl-tnode {{ border: 1px solid var(--line); background: rgba(30,41,59,.55); border-radius: 7px;
                     padding: 5px 7px; font-size: 10.5px; text-align: center; min-width: 34px; }}
        .sl-tnode.root {{ border-color: var(--accent); color: var(--accent); background: {accent}16; }}
        .sl-tnode.null {{ opacity: 0; border: none; background: none; }}
        .sl-tnode .k {{ font-weight: 650; }}
        .sl-tnode .p {{ color: var(--muted); font-size: 9px; }}

        /* 图 */
        .sl-graph {{ width: 100%; }}
        .sl-graph svg {{ width: 100%; height: auto; display: block; }}
        .sl-legend {{ display: flex; gap: 14px; flex-wrap: wrap; margin-top: 8px; color: var(--muted); font-size: 11px; }}
        .sl-dot {{ width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 4px; }}

        /* 并查集 */
        .sl-groups {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .sl-group {{ border: 1px solid {accent2}44; background: {accent2}11; border-radius: 10px; padding: 7px 10px; }}
        .sl-group .g {{ color: {accent2}; font-size: 10px; letter-spacing: .04em; }}
        .sl-group .m {{ font-size: 11.5px; margin-top: 2px; }}

        /* 日志 / 时间线 */
        .sl-log {{ display: flex; flex-direction: column; gap: 0; }}
        .sl-log .row {{ display: flex; gap: 10px; padding: 7px 0; border-bottom: 1px dashed rgba(148,163,184,.12); }}
        .sl-log .row:last-child {{ border-bottom: none; }}
        .sl-log .t {{ color: var(--muted); font-size: 10.5px; min-width: 62px; padding-top: 2px;
                      font-variant-numeric: tabular-nums; }}
        .sl-log .m {{ font-size: 12px; color: var(--text); }}
        .sl-log .tag {{ font-size: 9.5px; color: var(--accent); border: 1px solid {accent}33;
                        border-radius: 99px; padding: 0 6px; margin-left: 4px; }}

        /* 表格 */
        .sl-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
        .sl-table th {{ text-align: left; color: var(--muted); font-weight: 600; font-size: 10.5px;
                        letter-spacing: .06em; padding: 7px 8px; border-bottom: 1px solid var(--line); }}
        .sl-table td {{ padding: 8px; border-bottom: 1px solid rgba(148,163,184,.09); color: var(--text); }}
        .sl-table tr:last-child td {{ border-bottom: none; }}
        .sl-table td.num {{ font-variant-numeric: tabular-nums; }}

        /* 排行条 */
        .sl-bars {{ display: flex; flex-direction: column; gap: 8px; }}
        .sl-bar .top {{ display: flex; justify-content: space-between; font-size: 11.5px; margin-bottom: 3px; }}
        .sl-bar .top span:last-child {{ color: var(--muted); }}
        .sl-bar .track {{ height: 6px; border-radius: 99px; background: rgba(148,163,184,.12); overflow: hidden; }}
        .sl-bar .fill {{ height: 100%; border-radius: 99px;
                         background: linear-gradient(90deg, var(--accent), var(--accent2)); }}

        /* Streamlit 控件微调 */
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
            border-radius: 10px; border: 1px solid {accent}55; background: {accent}18;
            color: var(--text); font-weight: 600; transition: all .15s ease;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            border-color: var(--accent); background: {accent}2b; color: #fff;
        }}
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
            background: linear-gradient(120deg, {accent}, {accent2}); color: #06121c; border: none;
        }}
        [data-testid="stSidebar"] .stRadio label {{ font-size: 13px; }}
        [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {{ gap: 4px; }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 6px; border-bottom: 1px solid var(--line); }}
        .stTabs [data-baseweb="tab"] {{
            height: 38px; border-radius: 9px 9px 0 0; padding: 0 14px;
            color: var(--muted); font-size: 13px;
        }}
        .stTabs [aria-selected="true"] {{ color: var(--accent); background: {accent}10; }}
        [data-testid="stMetric"] {{
            background: var(--panel); border: 1px solid var(--line); border-radius: 14px;
            padding: 10px 14px;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--muted); }}
        [data-testid="stExpander"] {{
            border: 1px solid var(--line); border-radius: 12px; background: rgba(17,24,39,.45);
        }}
        [data-testid="stDataFrame"] {{ border-radius: 12px; overflow: hidden; }}
        .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] > div,
        .stTextArea textarea {{
            background: rgba(8, 13, 23, .8) !important; border-color: var(--line) !important;
            color: var(--text) !important; border-radius: 9px !important;
        }}
        .stSlider [data-baseweb="slider"] {{ padding-top: 4px; }}
        .stAlert {{ border-radius: 12px; }}
        div[data-testid="stToast"] {{ background: #111827; border: 1px solid var(--line); }}
        @media (max-width: 900px) {{
            .sl-kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
            .sl-hero h1 {{ font-size: 26px; }}
            .sl-hero {{ padding: 20px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_setup(title: str, icon: str, accent: str, accent2: str) -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide", initial_sidebar_state="expanded")
    inject_css(accent, accent2)


# ---------------------------------------------------------------------------
# 文本与布局组件
# ---------------------------------------------------------------------------
def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def hero(eyebrow: str, title: str, subtitle: str, chips: Sequence[str] = ()) -> None:
    chip_html = "".join(f'<span class="sl-chip">{esc(c)}</span>' for c in chips)
    st.markdown(
        f"""
        <div class="sl-hero">
          <span class="sl-eyebrow"><i></i>{esc(eyebrow)}</span>
          <h1>{esc(title)}<small>{esc(subtitle)}</small></h1>
          <div class="sl-chips">{chip_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpis(items: Sequence[dict[str, Any]]) -> None:
    cards = []
    for item in items:
        tone = " accent" if item.get("accent") else ""
        unit = f"<em>{esc(item['unit'])}</em>" if item.get("unit") else ""
        sub = f'<div class="sub">{esc(item.get("sub", ""))}</div>' if item.get("sub") else ""
        cards.append(
            f'<div class="sl-kpi{tone}"><div class="lab">{esc(item["label"])}</div>'
            f'<div class="val">{esc(item["value"])}{unit}</div>{sub}</div>'
        )
    st.markdown(f'<div class="sl-kpis">{"".join(cards)}</div>', unsafe_allow_html=True)


def section(title: str, desc: str = "", right: str = "") -> None:
    right_html = f'<div class="right">{esc(right)}</div>' if right else ""
    desc_html = f"<p>{esc(desc)}</p>" if desc else ""
    st.markdown(
        f'<div class="sl-section"><div><h3>{esc(title)}</h3>{desc_html}</div>{right_html}</div>',
        unsafe_allow_html=True,
    )


def card(body_html: str, tight: bool = False) -> None:
    cls = "sl-card tight" if tight else "sl-card"
    st.markdown(f'<div class="{cls}">{body_html}</div>', unsafe_allow_html=True)


def note(body: str, title: str | None = None) -> None:
    st.markdown(
        f'<div class="sl-card"><h4>{esc(title or _t("设计说明", "Design note"))}</h4><p>{body}</p></div>',
        unsafe_allow_html=True,
    )


def empty(text: str | None = None) -> None:
    st.markdown(f'<div class="sl-empty">{esc(text if text is not None else _t("暂无数据", "No data yet"))}</div>', unsafe_allow_html=True)


def chip(text: str, tone: str = "") -> str:
    cls = f"sl-chip {tone}".strip()
    return f'<span class="{cls}">{esc(text)}</span>'


def visual_label(label: str) -> None:
    st.markdown(f'<div class="sl-visual-label">{esc(label)}</div>', unsafe_allow_html=True)


def log_view(entries: Iterable[dict[str, Any]], limit: int = 10) -> None:
    rows = []
    for entry in list(entries)[:limit]:
        tag = f'<span class="tag">{esc(entry["tag"])}</span>' if entry.get("tag") else ""
        rows.append(
            f'<div class="row"><div class="t">{esc(entry.get("time", ""))}</div>'
            f'<div class="m">{esc(entry.get("text", ""))}{tag}</div></div>'
        )
    if not rows:
        empty(_t("还没有操作记录", "No activity yet"))
        return
    st.markdown(f'<div class="sl-log">{"".join(rows)}</div>', unsafe_allow_html=True)


def table_view(headers: Sequence[str], rows: Sequence[Sequence[Any]], num_cols: Sequence[int] = ()) -> None:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = "".join(
            f'<td class="{"num" if i in num_cols else ""}">{esc(c)}</td>' for i, c in enumerate(row)
        )
        body.append(f"<tr>{cells}</tr>")
    st.markdown(
        f'<table class="sl-table"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>',
        unsafe_allow_html=True,
    )


def bar_view(items: Sequence[tuple[str, float]], suffix: str = "") -> None:
    if not items:
        empty()
        return
    top = max(v for _, v in items) or 1
    rows = []
    for label, value in items:
        pct = max(3, min(100, value / top * 100))
        rows.append(
            f'<div class="sl-bar"><div class="top"><span>{esc(label)}</span>'
            f'<span>{esc(value)}{esc(suffix)}</span></div>'
            f'<div class="track"><div class="fill" style="width:{pct:.1f}%"></div></div></div>'
        )
    st.markdown(f'<div class="sl-bars">{"".join(rows)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 数据结构可视化
# ---------------------------------------------------------------------------
def array_html(
    values: Sequence[Any],
    labels: Sequence[Any] | None = None,
    highlight: Iterable[int] = (),
    max_cells: int = 18,
    label_fmt: str = "{}",
) -> str:
    hl = set(highlight)
    cells = []
    shown = list(values)[:max_cells]
    for i, value in enumerate(shown):
        cls = "sl-cell hl" if i in hl else "sl-cell"
        idx = labels[i] if labels and i < len(labels) else i
        cells.append(
            f'<div class="{cls}"><div class="v">{esc(_trunc(value, 14))}</div>'
            f'<div class="i">{esc(label_fmt.format(idx))}</div></div>'
        )
    if len(values) > max_cells:
        cells.append(f'<div class="sl-cell ghost"><div class="v">…</div><div class="i">+{len(values) - max_cells}</div></div>')
    return f'<div class="sl-array">{"".join(cells)}</div>'


def linked_html(values: Sequence[Any], max_nodes: int = 8, label: str = "head") -> str:
    values = list(values)
    if not values:
        return f'<div class="sl-empty">{_t("空链表 · head → NULL", "Empty list · head → NULL")}</div>'
    shown = values[:max_nodes]
    parts = [f'<span class="sl-null">{esc(label)}</span>', '<span class="sl-arrow">→</span>']
    for value in shown:
        parts.append(f'<div class="sl-node">{esc(_trunc(value, 18))}</div>')
        parts.append('<span class="sl-arrow">→</span>')
    if len(values) > max_nodes:
        parts.append(f'<span class="sl-null">… {len(values) - max_nodes} {_t("项", "more")}</span>')
        parts.append('<span class="sl-arrow">→</span>')
    parts.append('<span class="sl-null">NULL</span>')
    return f'<div class="sl-linked">{"".join(parts)}</div>'


def stack_html(values: Sequence[Any], max_items: int = 8) -> str:
    """values 为从栈底到栈顶。"""
    values = list(values)
    if not values:
        return f'<div class="sl-empty">{_t("空栈 · 栈顶 = 栈底", "Empty stack · top = bottom")}</div>'
    shown = values[-max_items:]
    rows = []
    for i, value in enumerate(shown):
        is_top = i == len(shown) - 1
        cap = f' <span class="cap">{_t("← 栈顶 top", "← top")}</span>' if is_top else ""
        rows.append(f'<div class="item{" top" if is_top else ""}">{esc(_trunc(value, 22))}{cap}</div>')
    hidden = len(values) - len(shown)
    if hidden:
        rows.insert(0, f'<div class="item" style="opacity:.45">{_t(f"… 下方还有 {hidden} 项", f"… {hidden} more below")}</div>')
    return f'<div class="sl-stack">{"".join(rows)}</div>'


def queue_html(values: Sequence[Any], max_items: int = 9) -> str:
    values = list(values)
    if not values:
        return f'<div class="sl-empty">{_t("空队列 · head = tail", "Empty queue · head = tail")}</div>'
    shown = values[:max_items]
    items = []
    for i, value in enumerate(shown):
        cls = "qitem head" if i == 0 else "qitem"
        items.append(f'<div class="{cls}">{esc(_trunc(value, 16))}</div>')
    if len(values) > max_items:
        items.append(f'<div class="qitem" style="opacity:.5">… +{len(values) - max_items}</div>')
    return (
        f'<div class="sl-queue"><span class="qtag">{_t("队头", "front")}<br>head</span>'
        + '<span class="sl-arrow">→</span>'
        + f'{"".join(items)}<span class="sl-arrow">→</span><span class="qtag">{_t("队尾", "rear")}<br>tail</span></div>'
    )


def deque_html(values: Sequence[Any], max_items: int = 10) -> str:
    values = list(values)
    if not values:
        return f'<div class="sl-empty">{_t("空双端队列", "Empty deque")}</div>'
    shown = values[:max_items]
    items = "".join(f'<div class="qitem">{esc(_trunc(v, 14))}</div>' for v in shown)
    return (
        f'<div class="sl-queue"><span class="qtag">{_t("左端", "left")}<br>left</span><span class="sl-arrow">→</span>'
        f'{items}<span class="sl-arrow">→</span><span class="qtag">{_t("右端", "right")}<br>right</span></div>'
    )


def hash_html(buckets: Sequence[Sequence[tuple[Any, Any]]], max_buckets: int = 16) -> str:
    shown = buckets[:max_buckets]
    cards = []
    for i, bucket in enumerate(shown):
        kvs = "".join(
            f'<div class="kv"><b>{esc(_trunc(k, 10))}</b> → {esc(_trunc(v, 12))}</div>' for k, v in bucket[:3]
        )
        if len(bucket) > 3:
            kvs += f'<div class="kv" style="color:var(--muted)">… +{len(bucket) - 3}</div>'
        cards.append(f'<div class="sl-bucket"><div class="b">BUCKET {i}</div>{kvs}</div>')
    if len(buckets) > max_buckets:
        cards.append(f'<div class="sl-bucket"><div class="b">…</div><div class="kv">{_t("还有", "and")} {len(buckets) - max_buckets} {_t("个桶", "more buckets")}</div></div>')
    return f'<div class="sl-buckets">{"".join(cards)}</div>'


def heap_html(items: Sequence[tuple[float, Any]], priority_fmt: str = "{:g}") -> str:
    """items 为堆数组顺序 (priority, item)。按层画成完全二叉树。"""
    if not items:
        return f'<div class="sl-empty">{_t("空堆", "Empty heap")}</div>'
    levels = []
    index = 0
    width = 1
    while index < len(items):
        level = []
        for i in range(width):
            if index + i < len(items):
                priority, value = items[index + i]
                level.append(
                    f'<div class="sl-tnode"><div class="k">{esc(_trunc(value, 12))}</div>'
                    f'<div class="p">{esc(priority_fmt.format(priority))}</div></div>'
                )
            else:
                level.append('<div class="sl-tnode null">·</div>')
        levels.append(f'<div class="sl-level">{"".join(level)}</div>')
        index += width
        width *= 2
    return f'<div class="sl-levels">{"".join(levels)}</div>'


def bst_html(levels: Sequence[Sequence[tuple[Any, Any] | None]]) -> str:
    if not levels:
        return f'<div class="sl-empty">{_t("空树", "Empty tree")}</div>'
    rows = []
    for depth, level in enumerate(levels):
        cells = []
        for node in level:
            if node is None:
                cells.append('<div class="sl-tnode null">·</div>')
            else:
                key, value = node
                cells.append(
                    f'<div class="sl-tnode{" root" if depth == 0 else ""}">'
                    f'<div class="k">{esc(_trunc(key, 10))}</div>'
                    f'<div class="p">{esc(_trunc(value, 8))}</div></div>'
                )
        rows.append(f'<div class="sl-level">{"".join(cells)}</div>')
    return f'<div class="sl-levels">{"".join(rows)}</div>'


def trie_html(words: Sequence[str], prefix: str = "", max_items: int = 10) -> str:
    if not words:
        return f'<div class="sl-empty">{_t("没有匹配的词条", "No matching entries")}</div>'
    parts = []
    for word in list(words)[:max_items]:
        if prefix and word.startswith(prefix):
            rest = word[len(prefix):]
            parts.append(
                f'<div class="qitem"><b style="color:var(--accent)">{esc(prefix)}</b>{esc(rest)}</div>'
            )
        else:
            parts.append(f'<div class="qitem">{esc(word)}</div>')
    return f'<div class="sl-queue">{"".join(parts)}</div>'


def graph_html(
    nodes: Sequence[Any],
    edges: Sequence[tuple[Any, Any, float]],
    highlight_nodes: Iterable[Any] = (),
    path: Sequence[Any] = (),
    labels: dict[Any, str] | None = None,
    width: int = 660,
    height: int = 360,
) -> str:
    nodes = list(dict.fromkeys(nodes))
    if not nodes:
        return f'<div class="sl-empty">{_t("空图", "Empty graph")}</div>'
    n = len(nodes)
    cx, cy = width / 2, height / 2 - 6
    rx, ry = width * 0.37, height * 0.34
    pos: dict[Any, tuple[float, float]] = {}
    for i, node in enumerate(nodes):
        angle = -math.pi / 2 + 2 * math.pi * i / n
        pos[node] = (cx + rx * math.cos(angle), cy + ry * math.sin(angle))

    edge_parts = []
    path_pairs = set()
    for a, b in zip(path, path[1:]):
        path_pairs.add((a, b))
        path_pairs.add((b, a))
    for a, b, w in edges:
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        on_path = (a, b) in path_pairs
        color = "#5eead4" if on_path else "rgba(148,163,184,.30)"
        dash = "" if on_path else ' stroke-dasharray="3 4"'
        stroke_w = 3.4 if on_path else 1.5
        edge_parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{stroke_w}"{dash}/>'
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if w and float(w) != 1.0 and n <= 14:
            edge_parts.append(
                f'<text x="{mx:.1f}" y="{my:.1f}" fill="#8fa3b8" font-size="9" '
                f'text-anchor="middle" dy="-3">{esc(_fmt_weight(w))}</text>'
            )

    hl = set(highlight_nodes)
    node_parts = []
    for node in nodes:
        x, y = pos[node]
        active = node in hl or node in path
        fill = "#0f2f33" if active else "#111a2b"
        stroke = "#5eead4" if node in hl else ("#a78bfa" if node in path else "rgba(148,163,184,.38)")
        node_parts.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
            f'<text x="{x:.1f}" y="{y:.1f}" fill="{"#5eead4" if active else "#dbe7f3"}" font-size="9.5" '
            f'text-anchor="middle" dy="3.4" font-weight="600">{esc(_trunc(labels.get(node, node) if labels else node, 6))}</text>'
        )
    return (
        f'<div class="sl-graph"><svg viewBox="0 0 {width} {height}" role="img">'
        f'{"".join(edge_parts)}{"".join(node_parts)}</svg></div>'
        f'<div class="sl-legend"><span><i class="sl-dot" style="background:#5eead4"></i>{_t("起点/关键节点", "Start / key node")}</span>'
        f'<span><i class="sl-dot" style="background:#a78bfa"></i>{_t("最短路径", "Shortest path")}</span>'
        f'<span><i class="sl-dot" style="background:#475569"></i>{_t("其他连接", "Other links")}</span></div>'
    )


def union_html(groups: dict[Any, Sequence[Any]], max_groups: int = 8) -> str:
    if not groups:
        return f'<div class="sl-empty">{_t("没有分组", "No groups")}</div>'
    cards = []
    for root, members in list(groups.items())[:max_groups]:
        cards.append(
            f'<div class="sl-group"><div class="g">{_t("代表元", "Root")} {esc(_trunc(root, 12))}</div>'
            f'<div class="m">{esc(_t("、", ", ").join(_trunc(m, 10) for m in members[:6]))}'
            f'{" …" if len(members) > 6 else ""}</div></div>'
        )
    if len(groups) > max_groups:
        cards.append(f'<div class="sl-group"><div class="g">…</div><div class="m">{_t("还有", "and")} {len(groups) - max_groups} {_t("组", "more groups")}</div></div>')
    return f'<div class="sl-groups">{"".join(cards)}</div>'


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------
def _trunc(value: Any, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _fmt_weight(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:g}"


def download_json(data: Any, filename: str, label: str | None = None) -> None:
    payload = json.dumps(data, ensure_ascii=False, indent=2, default=str)
    st.download_button(label or _t("导出数据 JSON", "Export JSON"), payload, file_name=filename,
                       mime="application/json", use_container_width=True)


def sidebar_brand(mark: str, name: str, tagline: str, accent: str) -> None:
    st.markdown(
        f"""
        <div style="display:flex;gap:11px;align-items:center;padding:2px 0 14px">
          <div style="width:38px;height:38px;border-radius:11px;display:grid;place-items:center;
                      background:linear-gradient(135deg,{accent},#a78bfa);color:#06121c;
                      font-weight:800;font-size:16px;box-shadow:0 8px 22px {accent}33">{esc(mark)}</div>
          <div><div style="font-weight:750;font-size:15px;letter-spacing:-.01em">{esc(name)}</div>
          <div style="color:#8fa3b8;font-size:10.5px;margin-top:1px">{esc(tagline)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_status(items: Sequence[tuple[str, str]]) -> None:
    rows = "".join(
        f'<div style="display:flex;justify-content:space-between;font-size:11px;padding:3px 0;color:#8fa3b8">'
        f'<span>{esc(k)}</span><span style="color:#dbe7f3">{esc(v)}</span></div>'
        for k, v in items
    )
    st.markdown(f'<div style="border:1px solid rgba(148,163,184,.16);border-radius:10px;padding:8px 10px">{rows}</div>', unsafe_allow_html=True)


__all__ = [
    "page_setup",
    "set_lang",
    "inject_css",
    "hero",
    "kpis",
    "section",
    "card",
    "note",
    "empty",
    "chip",
    "visual_label",
    "log_view",
    "table_view",
    "bar_view",
    "array_html",
    "linked_html",
    "stack_html",
    "queue_html",
    "deque_html",
    "hash_html",
    "heap_html",
    "bst_html",
    "trie_html",
    "graph_html",
    "union_html",
    "download_json",
    "sidebar_brand",
    "sidebar_status",
    "esc",
]
