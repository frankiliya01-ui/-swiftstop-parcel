"""第 3 组 · 速达驿站 —— 校园快递驿站管理系统

运行：streamlit run app.py
覆盖：动态数组、链表、栈、队列、双端队列、哈希表、堆、二叉搜索树、
      字典树、图、并查集（11 种）。
"""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

import ui
from ds_core import BST, Deque, DynamicArray, Graph, HashTable, LinkedList, MinHeap, Queue, Stack, Trie, UnionFind

ACCENT = "#38bdf8"
ACCENT2 = "#fbbf24"
GROUP = "第 3 组"
SYSTEM = "速达驿站"
SUBTITLE = "校园快递驿站管理系统 · Campus Parcel Station"

STATUS = {
    "pending": ("待取", "#38bdf8"),
    "notified": ("已通知", "#fbbf24"),
    "picked": ("已取", "#34d399"),
    "returned": ("退回", "#fb7185"),
}


@dataclass
class Parcel:
    code: str
    name: str
    phone: str
    dorm: str
    carrier: str
    weight: float
    arrived: int
    cell: str | None
    status: str = "pending"
    picked_day: int | None = None


@dataclass
class Cell:
    zone: str
    index: int
    code: str | None = None

    @property
    def cell_id(self) -> str:
        return f"{self.zone}-{self.index:02d}"


class StationState:
    def __init__(self) -> None:
        self.day = 20
        self.seq = 100014
        self.parcels = HashTable(8)
        self.shelf = DynamicArray(4)
        self.pick_queue = Queue(8)          # 队列：取件排队
        self.remind_deque = Deque(8)        # 双端队列：提醒
        self.overdue_heap = MinHeap()       # 堆：滞留最久
        self.flow = LinkedList()            # 链表：包裹流水
        self.undo = Stack()                 # 栈：撤销取件
        self.name_trie = Trie()             # 字典树：收件人
        self.weight_bst = BST()             # BST：重量
        self.route_graph = Graph()          # 图：配送路线
        self.dorm_groups = UnionFind()      # 并查集：寝室代取组
        self._seed()
        self._build_graph()
        self._build_groups()

    # -- 种子 -------------------------------------------------------------
    def _seed(self) -> None:
        for z in ["A", "B", "C", "D"]:
            row = DynamicArray(8)
            for i in range(1, 9):
                row.append(Cell(z, i))
            self.shelf.append(row)
        rows = [
            ("张同学", "138****1024", "1号楼 302", "顺丰", 2.4, 20, "A-01", "pending"),
            ("李同学", "139****2048", "2号楼 105", "中通", 0.8, 20, "A-02", "notified"),
            ("王同学", "137****3096", "1号楼 508", "京东", 5.2, 19, "A-03", "pending"),
            ("赵同学", "136****4096", "3号楼 201", "圆通", 1.1, 19, "B-01", "pending"),
            ("陈同学", "135****5120", "2号楼 407", "顺丰", 3.6, 18, "B-02", "notified"),
            ("刘同学", "134****6144", "4号楼 101", "韵达", 0.5, 18, "B-03", "pending"),
            ("孙同学", "133****7168", "1号楼 302", "中通", 8.9, 17, "C-01", "pending"),
            ("周同学", "132****8192", "3号楼 305", "京东", 12.5, 17, "C-02", "pending"),
            ("吴同学", "131****9216", "2号楼 105", "顺丰", 1.8, 15, "C-03", "notified"),
            ("郑同学", "130****0240", "4号楼 206", "圆通", 4.4, 14, "D-01", "pending"),
            ("冯同学", "188****1264", "1号楼 508", "韵达", 0.9, 13, "D-02", "pending"),
            ("何同学", "187****2288", "3号楼 201", "中通", 6.7, 12, "D-03", "notified"),
            ("许同学", "186****3312", "2号楼 407", "京东", 2.2, 18, None, "picked"),
            ("邓同学", "185****4336", "4号楼 101", "顺丰", 1.4, 16, None, "picked"),
        ]
        for i, (name, phone, dorm, carrier, weight, arrived, cell, status) in enumerate(rows):
            code = str(100001 + i)
            p = Parcel(code, name, phone, dorm, carrier, weight, arrived, cell, status,
                       20 if status == "picked" else None)
            self.parcels.put(code, p)
            self.name_trie.insert(name, code)
            self.weight_bst.insert((weight, code), name)
            self.dorm_groups.add(dorm)
            if status == "pending":
                self.overdue_heap.push(arrived, code)
            if cell:
                self.set_cell(cell, code)
        self._log("驿站开门，14 件包裹在架", "系统")

    def _build_graph(self) -> None:
        edges = [
            ("驿站", "快递柜", 1), ("驿站", "食堂", 4), ("驿站", "1号楼", 6),
            ("驿站", "2号楼", 8), ("1号楼", "2号楼", 3), ("2号楼", "3号楼", 4),
            ("3号楼", "4号楼", 5), ("食堂", "图书馆", 3), ("图书馆", "体育馆", 6),
            ("4号楼", "东门", 7), ("驿站", "东门", 9), ("食堂", "3号楼", 5),
        ]
        for a, b, w in edges:
            self.route_graph.add_edge(a, b, w)

    def _build_groups(self) -> None:
        # 同寝室 / 同楼层可以互相代取
        for a, b in [("1号楼 302", "1号楼 508"), ("2号楼 105", "2号楼 407"),
                     ("3号楼 201", "3号楼 305"), ("4号楼 101", "4号楼 206")]:
            self.dorm_groups.union(a, b)

    # -- 工具 -------------------------------------------------------------
    def _log(self, text: str, tag: str = "操作") -> None:
        self.flow.append({"day": self.day, "text": text, "tag": tag})

    def cells(self) -> list[Cell]:
        return [c for row in self.shelf for c in row]

    def cell_of(self, cell_id: str) -> Cell | None:
        return next((c for c in self.cells() if c.cell_id == cell_id), None)

    def set_cell(self, cell_id: str, code: str | None) -> None:
        c = self.cell_of(cell_id)
        if c:
            c.code = code

    def free_cell(self) -> Cell | None:
        return next((c for c in self.cells() if c.code is None), None)

    def pending(self) -> list[Parcel]:
        return [p for p in self.parcels.values() if p.status in ("pending", "notified")]

    def days_waiting(self, p: Parcel) -> int:
        return max(0, self.day - p.arrived)

    def is_overdue(self, p: Parcel) -> bool:
        return p.status in ("pending", "notified") and self.days_waiting(p) >= 3

    # -- 业务 -------------------------------------------------------------
    def add_parcel(self, name: str, phone: str, dorm: str, carrier: str, weight: float) -> tuple[bool, str]:
        cell = self.free_cell()
        if not cell:
            return False, "货架已满，请先清理滞留包裹"
        self.seq += 1
        code = str(self.seq)
        p = Parcel(code, name, phone, dorm, carrier, round(weight, 1), self.day, cell.cell_id)
        self.parcels.put(code, p)
        self.name_trie.insert(name, code)
        self.weight_bst.insert((p.weight, code), name)
        self.dorm_groups.add(dorm)
        cell.code = code
        self.overdue_heap.push(self.day, code)
        self._log(f"入库 {code} · {name} · {carrier} · 放到 {cell.cell_id}", "入库")
        return True, f"入库成功：取件码 {code}，已放到 {cell.cell_id}"

    def enqueue_pickup(self, code: str) -> tuple[bool, str]:
        p = self.parcels.get(code)
        if not p:
            return False, "取件码不存在"
        if p.status == "picked":
            return False, "该包裹已经取走"
        if p.status == "returned":
            return False, "该包裹已退回，无法取件"
        for item in self.pick_queue.to_list():
            if item["code"] == code:
                return False, "该包裹已经在排队"
        self.pick_queue.enqueue({"code": code, "name": p.name, "day": self.day})
        self._log(f"{p.name} 扫码排队取件（第 {len(self.pick_queue)} 位）", "排队")
        return True, f"{p.name} 已加入取件队列，前面还有 {len(self.pick_queue) - 1} 人"

    def serve_pickup(self) -> tuple[bool, str]:
        if self.pick_queue.is_empty():
            return False, "取件队列为空"
        item = self.pick_queue.dequeue()
        p = self.parcels.get(item["code"])
        if not p or p.status == "picked":
            return False, "该包裹状态异常，已跳过"
        cell_id = p.cell
        prev_status = "notified" if p.status == "notified" else "pending"
        p.status = "picked"
        p.picked_day = self.day
        p.cell = None
        if cell_id:
            self.set_cell(cell_id, None)
        self.undo.push({"code": p.code, "cell": cell_id, "prev_status": prev_status})
        self._log(f"{p.name} 取走 {p.code}，{cell_id or '货架'} 释放", "取件")
        return True, f"{p.name} 取件成功：《{p.carrier}》{p.code}，{cell_id or ''} 已释放"

    def undo_pickup(self) -> tuple[bool, str]:
        if self.undo.is_empty():
            return False, "没有可撤销的取件"
        action = self.undo.pop()
        p = self.parcels.get(action["code"])
        if not p:
            return False, "包裹不存在"
        if p.status != "picked":
            return False, "该包裹当前不是已取状态"
        if action["cell"] and self.cell_of(action["cell"]) and self.cell_of(action["cell"]).code is not None:
            return False, "原货位已被占用，无法撤销"
        if action["cell"]:
            self.set_cell(action["cell"], p.code)
        p.cell = action["cell"]
        p.status = action["prev_status"]
        p.picked_day = None
        self.overdue_heap.push(p.arrived, p.code)
        self._log(f"撤销取件：{p.code} 放回 {p.cell}", "撤销")
        return True, f"已撤销取件，{p.code} 放回 {p.cell}"

    def remind(self, code: str, urgent: bool | None = None) -> tuple[bool, str]:
        p = self.parcels.get(code)
        if not p or p.status not in ("pending", "notified"):
            return False, "该包裹不需要提醒"
        if urgent is None:
            urgent = self.is_overdue(p)
        p.status = "notified"
        if urgent:
            self.remind_deque.appendleft({"code": code, "name": p.name, "urgent": True})
            self._log(f"{p.name} 的 {code} 超过 3 天，插入加急提醒队首", "催取")
            return True, f"{p.name} 的包裹已加急提醒（从队首）"
        self.remind_deque.append({"code": code, "name": p.name, "urgent": False})
        self._log(f"{p.name} 的 {code} 进入普通提醒队尾", "提醒")
        return True, f"{p.name} 的包裹已加入普通提醒队列"

    def send_reminder(self) -> tuple[bool, str]:
        if self.remind_deque.is_empty():
            return False, "提醒队列为空"
        item = self.remind_deque.popleft()
        tag = "加急" if item["urgent"] else "普通"
        self._log(f"已向 {item['name']} 发送{tag}取件提醒", "发送")
        return True, f"已向 {item['name']} 发送{tag}短信：取件码 {item['code']}"

    def return_oldest(self) -> tuple[bool, str]:
        while not self.overdue_heap.is_empty():
            arrived, code = self.overdue_heap.peek_priority(), self.overdue_heap.pop()
            p = self.parcels.get(code)
            if not p or p.status not in ("pending", "notified"):
                continue
            cell_id = p.cell
            p.status = "returned"
            p.cell = None
            if cell_id:
                self.set_cell(cell_id, None)
            self._log(f"{code} 滞留 {self.days_waiting(p)} 天，退回快递公司，{cell_id} 释放", "退回")
            return True, f"已退回 {p.name} 的 {code}（滞留 {self.days_waiting(p)} 天）"
        return False, "没有可退回的滞留包裹"

    def merge_dorms(self, a: str, b: str) -> tuple[bool, str]:
        if self.dorm_groups.union(a, b):
            self._log(f"代取组合并：{a} ↔ {b}", "代取")
            return True, f"{a} 与 {b} 已合并为同一个代取组"
        return False, "两个寝室已经在同一代取组"

    def notify_due(self) -> int:
        """把超过 3 天未取的包裹自动加入提醒队列（不重复）。"""
        queued = {i["code"] for i in self.remind_deque.to_list()}
        count = 0
        for p in self.pending():
            if self.is_overdue(p) and p.code not in queued:
                self.remind(p.code, True)
                count += 1
        return count


ui.page_setup(f"{SYSTEM} · {GROUP}", "📦", ACCENT, ACCENT2)


def flash(ok: bool, msg: str) -> None:
    st.session_state.g3_flash = (ok, msg)
    st.rerun()


def show_flash() -> None:
    payload = st.session_state.pop("g3_flash", None)
    if payload:
        (st.success if payload[0] else st.error)(payload[1])


def get_state() -> StationState:
    if "g3_state" not in st.session_state:
        st.session_state.g3_state = StationState()
    return st.session_state.g3_state


def shelf_html(state: StationState) -> str:
    rows = []
    for row in state.shelf:
        cells = []
        for cell in row:
            p = state.parcels.get(cell.code) if cell.code else None
            color = STATUS[p.status][1] if p else "#475569"
            label = p.name if p else "空"
            code = p.code if p else "—"
            cells.append(
                f"<div style='border:1px solid {color}55;background:{color}10;border-radius:8px;padding:6px 4px;text-align:center'>"
                f"<div style='font-size:9.5px;color:#8fa3b8'>{cell.cell_id}</div>"
                f"<div style='font-size:11px;font-weight:700;color:{color}'>{ui.esc(label)}</div>"
                f"<div style='font-size:9px;color:#8fa3b8'>{ui.esc(code)}</div></div>"
            )
        rows.append(f"<div style='display:grid;grid-template-columns:repeat(8,1fr);gap:5px;margin-bottom:5px'>{''.join(cells)}</div>")
    return f"<div class='sl-card'><h4>货架图 · 4 区 × 8 格</h4><p>二维动态数组：每个格子是一个 Cell，code 为空表示空闲。</p><div style='margin-top:10px'>{''.join(rows)}</div></div>"


def sidebar(state: StationState) -> str:
    with st.sidebar:
        ui.sidebar_brand("03", SYSTEM, f"{GROUP} · 11 种数据结构", ACCENT)
        pages = ["驿站总览", "入库上架", "取件排队", "提醒中心", "查询中心", "配送路线", "代取分组", "数据结构总览", "关于本组"]
        page = st.radio("导航", pages, label_visibility="collapsed")
        st.markdown("---")
        ui.sidebar_status([
            ("当前天数", f"第 {state.day} 天"),
            ("待取包裹", f"{len(state.pending())} 件"),
            ("货架占用", f"{sum(1 for c in state.cells() if c.code)} / 32"),
            ("取件队列", f"{len(state.pick_queue)} 人"),
        ])
        st.markdown("---")
        if st.button("推进一天 →", use_container_width=True):
            state.day += 1
            state._log(f"时间推进到第 {state.day} 天", "时间")
            st.toast(f"第 {state.day} 天，记得清理超时包裹")
            st.rerun()
        if st.button("撤销最近取件", use_container_width=True):
            flash(*state.undo_pickup())
        ui.download_json({
            "day": state.day,
            "parcels": [p.__dict__ for p in state.parcels.values()],
            "shelf": {c.cell_id: c.code for c in state.cells()},
        }, "station-state.json", "导出系统快照")
        st.markdown('<a href="https://en-g3.algo.43.135.50.247.sslip.io" target="_blank">English edition ↗</a>', unsafe_allow_html=True)
        st.caption("本地 Streamlit · 数据存于本次会话")
    return page


# ---------------------------------------------------------------------------
# 总览
# ---------------------------------------------------------------------------
def page_dashboard(state: StationState) -> None:
    ui.hero("GROUP 03 · PARCEL", SYSTEM,
            "入库、上架、排队、提醒、配送、代取——一个驿站就是一套小型的数据结构交响乐。",
            ["14 件初始包裹", "32 个货位", "11 种数据结构", f"第 {state.day} 天"])
    overdue = [p for p in state.pending() if state.is_overdue(p)]
    occupied = sum(1 for c in state.cells() if c.code)
    ui.kpis([
        {"label": "待取包裹", "value": len(state.pending()), "sub": f"超时 {len(overdue)} 件", "accent": True},
        {"label": "货架占用", "value": occupied, "unit": "/ 32", "sub": "4 区 × 8 格"},
        {"label": "取件队列", "value": len(state.pick_queue), "sub": "FIFO"},
        {"label": "今日入库", "value": sum(1 for p in state.parcels.values() if p.arrived == state.day), "unit": " 件"},
    ])
    left, right = st.columns([1.1, 1])
    with left:
        ui.section("最近 7 天入库量", "柱状条由大到小排列，便于观察高峰")
        ui.bar_view([(f"D-{6 - i}", v) for i, v in enumerate([18, 24, 21, 30, 27, 35, 29])], " 件")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        ui.section("滞留最久 TOP 5", "小顶堆按到达日排序，堆顶最久")
        oldest = sorted(state.pending(), key=lambda p: p.arrived)[:5]
        ui.table_view(["取件码", "收件人", "货位", "滞留"], [
            (p.code, p.name, p.cell or "-", f"{state.days_waiting(p)} 天") for p in oldest
        ])
    with right:
        ui.section("超时预警", "超过 3 天标红；可在提醒中心一键催取")
        for p in overdue[:6]:
            st.markdown(f"- **{p.code}** {p.name} · {p.cell} · 已 {state.days_waiting(p)} 天")
        if not overdue:
            ui.empty("没有超时包裹")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        ui.section("包裹流水", "单链表按时间追加")
        ui.log_view([{"time": f"第{e['day']}天", "text": e["text"], "tag": e.get("tag", "")}
                     for e in list(state.flow)[::-1]], 7)
    st.markdown(shelf_html(state), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 入库上架
# ---------------------------------------------------------------------------
def page_intake(state: StationState) -> None:
    ui.hero("INTAKE", "入库上架", "扫描快递单 → 哈希表登记 → 字典树/BST 建索引 → 动态数组找空位 → 堆里排队催取。",
            ["HashTable", "Trie", "BST", "DynamicArray", "MinHeap"])
    c1, c2 = st.columns([1, 1.2])
    with c1:
        ui.section("新包裹入库", "自动分配第一个空闲货位")
        with st.form("intake"):
            name = st.text_input("收件人", "林同学")
            phone = st.text_input("手机号", "139****7788")
            dorm = st.text_input("寝室", "2号楼 302")
            carrier = st.selectbox("快递公司", ["顺丰", "中通", "圆通", "京东", "韵达"])
            weight = st.number_input("重量（kg）", 0.1, 30.0, 2.0, step=0.1)
            go = st.form_submit_button("入库并上架", type="primary", use_container_width=True)
        if go:
            if not name.strip() or not dorm.strip():
                st.error("收件人和寝室不能为空")
            else:
                flash(*state.add_parcel(name.strip(), phone, dorm.strip(), carrier, float(weight)))
    with c2:
        ui.section("货架分配策略", "第一个空闲格子；O(32) 线性扫描")
        free = [c for c in state.cells() if c.code is None]
        ui.kpis([
            {"label": "空闲货位", "value": len(free), "accent": True},
            {"label": "A 区", "value": sum(1 for c in free if c.zone == "A")},
            {"label": "B 区", "value": sum(1 for c in free if c.zone == "B")},
            {"label": "C/D 区", "value": sum(1 for c in free if c.zone in ("C", "D"))},
        ])
        st.caption("如果要改成“按重量分区”，只需要修改 free_cell() 的选择规则，不用动其他业务。")
    st.markdown(shelf_html(state), unsafe_allow_html=True)
    ui.section("在架包裹", f"{len(state.pending())} 件")
    rows = []
    for p in sorted(state.pending(), key=lambda p: p.arrived):
        rows.append((p.code, p.name, p.dorm, p.carrier, f"{p.weight} kg", p.cell or "-", STATUS[p.status][0],
                     f"{state.days_waiting(p)} 天"))
    ui.table_view(["取件码", "收件人", "寝室", "快递", "重量", "货位", "状态", "在架"], rows)


# ---------------------------------------------------------------------------
# 取件排队
# ---------------------------------------------------------------------------
def page_pickup(state: StationState) -> None:
    ui.hero("PICKUP", "取件排队", "同学扫码进队，柜台从队头叫号；取走后货位立刻释放，栈里留一次撤销机会。",
            ["Queue", "Stack", "HashTable", "DynamicArray"])
    ui.kpis([
        {"label": "排队人数", "value": len(state.pick_queue), "accent": True},
        {"label": "待取包裹", "value": len(state.pending())},
        {"label": "今日已取", "value": sum(1 for p in state.parcels.values() if p.picked_day == state.day)},
        {"label": "可撤销操作", "value": len(state.undo)},
    ])
    c1, c2 = st.columns(2)
    with c1:
        ui.section("扫码加入队列", "先到先服务，不允许插队")
        with st.form("enqueue"):
            code = st.text_input("取件码", "100003")
            go = st.form_submit_button("加入取件队列", type="primary", use_container_width=True)
        if go:
            flash(*state.enqueue_pickup(code.strip()))
    with c2:
        ui.section("柜台叫号", "从队头 dequeue，核验后标记已取")
        if st.button("叫下一位取件", type="primary", use_container_width=True):
            flash(*state.serve_pickup())
        st.caption("如果队头包裹已取走，会自动跳过并报告异常。")

    ui.section("当前取件队列", "循环队列 · 队头先服务")
    q = state.pick_queue.to_list()
    if q:
        ui.queue_html([f"{i['name']} · {i['code']}" for i in q])
    else:
        ui.empty("队列为空")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    ui.section("操作记录", "每次取件都会压栈，可撤销最近一次")
    ui.log_view([{"time": f"第{e['day']}天", "text": e["text"], "tag": e.get("tag", "")}
                 for e in list(state.flow)[::-1]], 8)
    with st.expander("查看代码：取件时哪些结构同时变化"):
        st.code(
            """item = pick_queue.dequeue()      # 队列：队头出队
p = parcels.get(item["code"])     # 哈希：O(1) 找到包裹
p.status = "picked"
set_cell(p.cell, None)            # 数组：释放货位
undo.push({...})                  # 栈：记录可撤销操作
flow.append(...)                  # 链表：追加流水""",
            language="python",
        )


# ---------------------------------------------------------------------------
# 提醒中心
# ---------------------------------------------------------------------------
def page_remind(state: StationState) -> None:
    ui.hero("REMINDERS", "提醒中心", "超时包裹从左侧加急、普通包裹从右侧排队；堆顶永远是滞留最久的那一件。",
            ["Deque", "MinHeap", "Queue"])
    overdue = [p for p in state.pending() if state.is_overdue(p)]
    ui.kpis([
        {"label": "提醒队列", "value": len(state.remind_deque), "accent": True},
        {"label": "超时包裹", "value": len(overdue)},
        {"label": "最久滞留", "value": max((state.days_waiting(p) for p in state.pending()), default=0), "unit": " 天"},
        {"label": "已退回", "value": sum(1 for p in state.parcels.values() if p.status == "returned")},
    ])
    c1, c2 = st.columns(2)
    with c1:
        ui.section("手动加入提醒", "超时自动走左侧加急")
        with st.form("remind"):
            code = st.text_input("取件码", overdue[0].code if overdue else "100003")
            urgent = st.checkbox("加急（从队首插入）", value=True)
            go = st.form_submit_button("加入提醒队列", type="primary", use_container_width=True)
        if go:
            flash(*state.remind(code.strip(), urgent))
        if st.button("一键扫描超时包裹", use_container_width=True):
            n = state.notify_due()
            flash(n > 0, f"已把 {n} 件超时包裹加入加急提醒")
    with c2:
        ui.section("发送提醒", "从双端队列左端取出（加急优先）")
        if st.button("发送下一条提醒", type="primary", use_container_width=True):
            flash(*state.send_reminder())
        if st.button("退回最久未取件", use_container_width=True):
            flash(*state.return_oldest())
        st.caption("退回会真正从堆中弹出堆顶，并释放对应货位。")
    ui.section("提醒队列", "左端 = 加急，右端 = 普通")
    st.markdown(ui.deque_html([f"{i['name']}·{i['code']}{'!' if i['urgent'] else ''}"
                               for i in state.remind_deque.to_list()]), unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    ui.section("滞留堆", "按到达日从小到大；堆顶最久")
    items = [(pr, f"{code} {state.parcels.get(code).name}")
             for pr, code in state.overdue_heap.to_list()
             if state.parcels.get(code) and state.parcels.get(code).status in ("pending", "notified")]
    st.markdown(ui.heap_html(items[:15], priority_fmt="第{}天"), unsafe_allow_html=True)
    st.caption("已取走 / 已退回的包裹可能还留在堆里（lazy deletion），pop 时用状态过滤。")


# ---------------------------------------------------------------------------
# 查询中心
# ---------------------------------------------------------------------------
def page_query(state: StationState) -> None:
    ui.hero("SEARCH", "查询中心", "三种索引各司其职：哈希查码、字典树查人、BST 查重量区间。",
            ["HashTable", "Trie", "BST", "LinkedList"])
    tab1, tab2, tab3 = st.tabs(["取件码 · 哈希", "收件人 · 字典树", "重量区间 · BST"])
    with tab1:
        code = st.text_input("取件码", "100007", key="q_code")
        p = state.parcels.get(code)
        if p:
            ui.card(
                f"<h4>{ui.esc(p.name)} · {ui.esc(p.carrier)}</h4>"
                f"<p>取件码 {p.code} · {p.dorm} · {p.weight} kg · 第 {p.arrived} 天到达 · "
                f"货位 {p.cell or '已释放'} · 状态 {STATUS[p.status][0]}</p>"
            )
            ui.section("该包裹的流水", "从单链表中筛选")
            ui.log_view([{"time": f"第{e['day']}天", "text": e["text"], "tag": e.get("tag", "")}
                         for e in state.flow if p.code in e["text"]][::-1], 8)
        else:
            ui.empty("没有这个取件码")
    with tab2:
        prefix = st.text_input("收件人姓氏 / 名字前缀", "张", key="q_name")
        hits = state.name_trie.autocomplete(prefix, 8)
        st.caption(f"命中 {len(hits)} 人；字典树按字符逐层下降。")
        for name, code in hits:
            p = state.parcels.get(code)
            st.markdown(f"- **{name}** · {code} · {p.dorm if p else ''} · {STATUS[p.status][0] if p else ''}")
        if not hits:
            ui.empty("没有匹配的收件人")
        ui.visual_label("收件人词条")
        st.markdown(ui.trie_html(state.name_trie.words(30), prefix), unsafe_allow_html=True)
    with tab3:
        lo, hi = st.slider("重量区间（kg）", 0.0, 20.0, (2.0, 8.0), step=0.5, key="q_weight")
        results = state.weight_bst.range_query((lo, ""), (hi, "\uffff"))
        st.caption(f"BST 命中 {len(results)} 件；树高 {state.weight_bst.height()}。")
        ui.table_view(["收件人", "重量", "取件码"], [
            (name, f"{key[0]} kg", key[1]) for key, name in results
        ])
        ui.visual_label("重量 BST · 键 = (重量, 取件码)")
        st.markdown(ui.bst_html(state.weight_bst.levels()), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 配送路线
# ---------------------------------------------------------------------------
def page_route(state: StationState) -> None:
    ui.hero("DELIVERY", "配送路线", "驿站、宿舍楼和食堂构成一张带权图；Dijkstra 找出步行最短的送达路线。",
            ["Graph", "Dijkstra", "BFS", "UnionFind"])
    nodes = state.route_graph.nodes()
    c1, c2 = st.columns(2)
    with c1:
        start = st.selectbox("起点", nodes, index=0, key="r_start")
    with c2:
        target = st.selectbox("终点", nodes, index=3, key="r_target")
    if st.button("规划配送路线", type="primary", use_container_width=True):
        path, dist = state.route_graph.shortest_path(start, target)
        st.session_state.g3_path = (path, dist)
    path, dist = st.session_state.get("g3_path", ([], 0))
    if path:
        st.success(f"最短路线：{' → '.join(path)}，约 {dist:g} 分钟")
    ui.visual_label("校园配送图")
    st.markdown(ui.graph_html(nodes, state.route_graph.edges(), highlight_nodes=[start, target], path=path),
                unsafe_allow_html=True)
    ui.section("连通性检查", "如果校园施工封路，图可能被切成两个连通分量")
    comps = state.route_graph.components()
    ui.table_view(["分量", "节点"], [(f"#{i + 1}", "、".join(c)) for i, c in enumerate(comps)])


# ---------------------------------------------------------------------------
# 代取分组
# ---------------------------------------------------------------------------
def page_groups(state: StationState) -> None:
    ui.hero("PICKUP GROUPS", "代取分组", "室友、同楼层可以互相代取。并查集把“能代取”的关系合并成组。",
            ["UnionFind", "Path Compression"])
    ui.kpis([
        {"label": "寝室数", "value": len(state.dorm_groups)},
        {"label": "代取组", "value": state.dorm_groups.group_count, "accent": True},
        {"label": "最大组", "value": max((len(v) for v in state.dorm_groups.groups().values()), default=0), "unit": " 个寝室"},
        {"label": "合并次数", "value": sum(1 for e in state.flow if e.get("tag") == "代取")},
    ])
    ui.section("当前代取组", "同组内任意一人可代取")
    st.markdown(ui.union_html(state.dorm_groups.groups()), unsafe_allow_html=True)
    dorms = sorted(state.dorm_groups.parent.keys())
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        a = st.selectbox("寝室 A", dorms, key="g_a")
    with c2:
        b = st.selectbox("寝室 B", dorms, index=1, key="g_b")
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("合并代取组", type="primary", use_container_width=True):
            flash(*state.merge_dorms(a, b))
    st.caption(f"connected({a}, {b}) = {state.dorm_groups.connected(a, b)}")
    ui.note("并查集只支持合并，不支持拆分。如果业务需要“解除代取关系”，就要换用图或带删除的并查集变体——这是本组可以继续研究的扩展点。")


# ---------------------------------------------------------------------------
# 结构总览
# ---------------------------------------------------------------------------
def page_structures(state: StationState) -> None:
    ui.hero("DATA STRUCTURES", "11 种数据结构，一次看全", "从货架到路线，每一块都能在业务里找到对应操作。",
            ["Array", "Linked List", "Stack", "Queue", "Deque", "Hash", "Heap", "BST", "Trie", "Graph", "Union-Find"])
    with st.expander("① 动态数组 · 货架 4×8", expanded=True):
        st.markdown(ui.array_html([f"{c.cell_id}:{c.code or '空'}" for c in state.cells()], max_cells=16),
                    unsafe_allow_html=True)
        st.caption(f"外层 4 排，内层 8 格；size={len(state.shelf)}，每排 capacity={state.shelf[0].capacity}")
    with st.expander("② 单链表 · 包裹流水"):
        st.markdown(ui.linked_html([f"第{e['day']}天 {e['text']}" for e in list(state.flow)[-5:]]),
                    unsafe_allow_html=True)
    with st.expander("③ 栈 · 撤销取件"):
        st.markdown(ui.stack_html([f"取件 {a['code']}" for a in state.undo.to_list()]), unsafe_allow_html=True)
    with st.expander("④ 队列 · 取件排队"):
        st.markdown(ui.queue_html([f"{i['name']}·{i['code']}" for i in state.pick_queue.to_list()]),
                    unsafe_allow_html=True)
        st.caption(f"size={len(state.pick_queue)} · capacity={state.pick_queue.capacity}")
    with st.expander("⑤ 双端队列 · 提醒"):
        st.markdown(ui.deque_html([f"{i['name']}{'!' if i['urgent'] else ''}" for i in state.remind_deque.to_list()]),
                    unsafe_allow_html=True)
    with st.expander("⑥ 哈希表 · 取件码索引"):
        st.markdown(ui.hash_html(state.parcels.buckets(), 12), unsafe_allow_html=True)
        st.caption(f"{len(state.parcels)} 件 · {state.parcels.capacity} 桶 · 负载因子 {state.parcels.load_factor:.2f}")
    with st.expander("⑦ 小顶堆 · 滞留最久"):
        st.markdown(ui.heap_html([(p.arrived, f"{p.code} {p.name}") for p in state.pending()][:15],
                                 priority_fmt="第{}天"), unsafe_allow_html=True)
    with st.expander("⑧ 二叉搜索树 · 重量索引"):
        st.markdown(ui.bst_html(state.weight_bst.levels()), unsafe_allow_html=True)
        st.caption(f"树高 {state.weight_bst.height()}")
    with st.expander("⑨ 字典树 · 收件人"):
        st.markdown(ui.trie_html(state.name_trie.words(30), ""), unsafe_allow_html=True)
    with st.expander("⑩ 图 · 校园配送"):
        st.markdown(ui.graph_html(state.route_graph.nodes(), state.route_graph.edges()), unsafe_allow_html=True)
    with st.expander("⑪ 并查集 · 代取组"):
        st.markdown(ui.union_html(state.dorm_groups.groups()), unsafe_allow_html=True)


ROLES = [
    ("组长 / 项目经理", "排期、整合、演示组织", "计划 + 周报 + 答辩"),
    ("线性结构负责人", "数组、链表、栈、队列、双端队列", "ds_core.py 前 5 类 + 测试"),
    ("查找结构负责人", "哈希表、堆、BST", "ds_core.py 中 3 类 + 测试"),
    ("非线性结构负责人", "字典树、图、并查集", "ds_core.py 后 3 类 + 测试"),
    ("驿站业务工程师", "入库、上架、取件、退回", "业务函数 + 流程图"),
    ("界面工程师", "货架图、队列、提醒面板", "ui 组件 + 截图"),
    ("数据工程师", "种子包裹、状态一致性、导出", "seed + 导出"),
    ("测试工程师", "货架满、重复取件、撤销冲突", "tests/ + 缺陷清单"),
    ("部署工程师", "本地运行、依赖、演示环境", "启动脚本 + 部署记录"),
    ("文档 / 演示", "README、手册、PPT", "文档 + 8 分钟演示"),
]

MAP = [
    ("动态数组", "shelf", "4×8 货架"),
    ("单链表", "flow", "包裹流水"),
    ("栈", "undo", "撤销取件"),
    ("队列", "pick_queue", "取件排队 FIFO"),
    ("双端队列", "remind_deque", "加急左插 / 普通右插"),
    ("哈希表", "parcels", "取件码 → 包裹"),
    ("小顶堆", "overdue_heap", "滞留最久优先退回"),
    ("BST", "weight_bst", "重量区间查询"),
    ("字典树", "name_trie", "收件人前缀搜索"),
    ("图", "route_graph", "校园配送最短路"),
    ("并查集", "dorm_groups", "寝室代取组"),
]


def page_about(state: StationState) -> None:
    ui.hero("GROUP 03 · PLAYBOOK", "关于本组", "一个驿站，10 个角色。先让包裹跑起来，再让结构说话。",
            ["8–10 人", "4 周迭代", "可本地部署"])
    ui.section("角色分工", "8 人组把文档并入组长；9 人组把部署并入测试")
    ui.table_view(["角色", "职责", "交付物"], ROLES)
    ui.section("数据结构映射", "答辩抽查表")
    ui.table_view(["结构", "代码位置", "业务用途"], MAP)
    ui.section("四周迭代", "")
    ui.table_view(["周次", "目标", "验收信号"], [
        ("第 1 周", "跑通、读代码、认领角色", "每人能演示一次入库和取件"),
        ("第 2 周", "入库→排队→取件→撤销闭环", "主流程 5 次无报错"),
        ("第 3 周", "提醒 / 查询 / 路线 / 代取", "边界用例通过"),
        ("第 4 周", "打磨、文档、演示", "8 分钟答辩"),
    ])
    st.info("本地运行：pip install -r requirements.txt && streamlit run app.py")


def main() -> None:
    state = get_state()
    show_flash()
    page = sidebar(state)
    if page == "驿站总览":
        page_dashboard(state)
    elif page == "入库上架":
        page_intake(state)
    elif page == "取件排队":
        page_pickup(state)
    elif page == "提醒中心":
        page_remind(state)
    elif page == "查询中心":
        page_query(state)
    elif page == "配送路线":
        page_route(state)
    elif page == "代取分组":
        page_groups(state)
    elif page == "数据结构总览":
        page_structures(state)
    else:
        page_about(state)


main()
