"""Group 3 · SwiftStop Parcel — Campus Parcel Station Management System

Run: streamlit run app_en.py
Covers: dynamic array, linked list, stack, queue, deque, hash table, min-heap,
        binary search tree, trie, graph, and union-find (11 structures).
"""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

import ds_core

ds_core.set_lang("en")

import ui

ui.set_lang("en")

from ds_core import BST, Deque, DynamicArray, Graph, HashTable, LinkedList, MinHeap, Queue, Stack, Trie, UnionFind

ACCENT = "#38bdf8"
ACCENT2 = "#fbbf24"
GROUP = "Group 3"
SYSTEM = "SwiftStop Parcel"
SUBTITLE = "Campus Parcel Station Management System"

STATUS = {
    "pending": ("Pending", "#38bdf8"),
    "notified": ("Notified", "#fbbf24"),
    "picked": ("Picked", "#34d399"),
    "returned": ("Returned", "#fb7185"),
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
        self.pick_queue = Queue(8)          # Queue: pickup line
        self.remind_deque = Deque(8)        # Deque: reminders
        self.overdue_heap = MinHeap()       # Min-heap: longest wait
        self.flow = LinkedList()            # Linked list: parcel activity
        self.undo = Stack()                 # Stack: undo pickup
        self.name_trie = Trie()             # Trie: recipients
        self.weight_bst = BST()             # BST: weights
        self.route_graph = Graph()          # Graph: delivery routes
        self.dorm_groups = UnionFind()      # Union-find: pickup groups
        self._seed()
        self._build_graph()
        self._build_groups()

    # -- Seed data ---------------------------------------------------------
    def _seed(self) -> None:
        for z in ["A", "B", "C", "D"]:
            row = DynamicArray(8)
            for i in range(1, 9):
                row.append(Cell(z, i))
            self.shelf.append(row)
        rows = [
            ("Alice Chen", "138****1024", "Dorm 1-302", "SF Express", 2.4, 20, "A-01", "pending"),
            ("Brian Lee", "139****2048", "Dorm 2-105", "ZTO", 0.8, 20, "A-02", "notified"),
            ("Chloe Wang", "137****3096", "Dorm 1-508", "JD", 5.2, 19, "A-03", "pending"),
            ("Daniel Zhao", "136****4096", "Dorm 3-201", "YTO", 1.1, 19, "B-01", "pending"),
            ("Emma Liu", "135****5120", "Dorm 2-407", "SF Express", 3.6, 18, "B-02", "notified"),
            ("Frank Sun", "134****6144", "Dorm 4-101", "Yunda", 0.5, 18, "B-03", "pending"),
            ("Grace Zhou", "133****7168", "Dorm 1-302", "ZTO", 8.9, 17, "C-01", "pending"),
            ("Henry Wu", "132****8192", "Dorm 3-305", "JD", 12.5, 17, "C-02", "pending"),
            ("Irene Zheng", "131****9216", "Dorm 2-105", "SF Express", 1.8, 15, "C-03", "notified"),
            ("Jason Feng", "130****0240", "Dorm 4-206", "YTO", 4.4, 14, "D-01", "pending"),
            ("Karen He", "188****1264", "Dorm 1-508", "Yunda", 0.9, 13, "D-02", "pending"),
            ("Leo Xu", "187****2288", "Dorm 3-201", "ZTO", 6.7, 12, "D-03", "notified"),
            ("Mia Deng", "186****3312", "Dorm 2-407", "JD", 2.2, 18, None, "picked"),
            ("Nina Lin", "185****4336", "Dorm 4-101", "SF Express", 1.4, 16, None, "picked"),
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
        self._log("Station opened with 14 parcels on the shelves", "System")

    def _build_graph(self) -> None:
        edges = [
            ("Station", "Locker", 1), ("Station", "Cafeteria", 4), ("Station", "Dorm 1", 6),
            ("Station", "Dorm 2", 8), ("Dorm 1", "Dorm 2", 3), ("Dorm 2", "Dorm 3", 4),
            ("Dorm 3", "Dorm 4", 5), ("Cafeteria", "Library", 3), ("Library", "Gym", 6),
            ("Dorm 4", "East Gate", 7), ("Station", "East Gate", 9), ("Cafeteria", "Dorm 3", 5),
        ]
        for a, b, w in edges:
            self.route_graph.add_edge(a, b, w)

    def _build_groups(self) -> None:
        # Roommates or neighbours on the same floor can collect for each other.
        for a, b in [("Dorm 1-302", "Dorm 1-508"), ("Dorm 2-105", "Dorm 2-407"),
                     ("Dorm 3-201", "Dorm 3-305"), ("Dorm 4-101", "Dorm 4-206")]:
            self.dorm_groups.union(a, b)

    # -- Helpers -----------------------------------------------------------
    def _log(self, text: str, tag: str = "Action") -> None:
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

    # -- Business rules ----------------------------------------------------
    def add_parcel(self, name: str, phone: str, dorm: str, carrier: str, weight: float) -> tuple[bool, str]:
        cell = self.free_cell()
        if not cell:
            return False, "The shelves are full. Clear overdue parcels before adding more."
        self.seq += 1
        code = str(self.seq)
        p = Parcel(code, name, phone, dorm, carrier, round(weight, 1), self.day, cell.cell_id)
        self.parcels.put(code, p)
        self.name_trie.insert(name, code)
        self.weight_bst.insert((p.weight, code), name)
        self.dorm_groups.add(dorm)
        cell.code = code
        self.overdue_heap.push(self.day, code)
        self._log(f"Intake {code} · {name} · {carrier} · shelved at {cell.cell_id}", "Intake")
        return True, f"Intake complete: pickup code {code}, shelved at {cell.cell_id}"

    def enqueue_pickup(self, code: str) -> tuple[bool, str]:
        p = self.parcels.get(code)
        if not p:
            return False, "Pickup code not found"
        if p.status == "picked":
            return False, "This parcel has already been picked up"
        if p.status == "returned":
            return False, "This parcel was returned and cannot be collected"
        for item in self.pick_queue.to_list():
            if item["code"] == code:
                return False, "This parcel is already in the queue"
        self.pick_queue.enqueue({"code": code, "name": p.name, "day": self.day})
        self._log(f"{p.name} joined the pickup queue (position {len(self.pick_queue)})", "Queue")
        return True, f"{p.name} joined the pickup queue with {len(self.pick_queue) - 1} ahead"

    def serve_pickup(self) -> tuple[bool, str]:
        if self.pick_queue.is_empty():
            return False, "The pickup queue is empty"
        item = self.pick_queue.dequeue()
        p = self.parcels.get(item["code"])
        if not p or p.status == "picked":
            return False, "Unexpected parcel status; this entry was skipped"
        cell_id = p.cell
        prev_status = "notified" if p.status == "notified" else "pending"
        p.status = "picked"
        p.picked_day = self.day
        p.cell = None
        if cell_id:
            self.set_cell(cell_id, None)
        self.undo.push({"code": p.code, "cell": cell_id, "prev_status": prev_status})
        self._log(f"{p.name} picked up {p.code}; {cell_id or 'shelf'} released", "Pickup")
        return True, f"{p.name} picked up {p.carrier} parcel {p.code}; {cell_id or ''} released"

    def undo_pickup(self) -> tuple[bool, str]:
        if self.undo.is_empty():
            return False, "There is no pickup to undo"
        action = self.undo.pop()
        p = self.parcels.get(action["code"])
        if not p:
            return False, "Parcel not found"
        if p.status != "picked":
            return False, "This parcel is not currently marked as picked up"
        if action["cell"] and self.cell_of(action["cell"]) and self.cell_of(action["cell"]).code is not None:
            return False, "The original slot is occupied, so the pickup cannot be undone"
        if action["cell"]:
            self.set_cell(action["cell"], p.code)
        p.cell = action["cell"]
        p.status = action["prev_status"]
        p.picked_day = None
        self.overdue_heap.push(p.arrived, p.code)
        self._log(f"Pickup undone: {p.code} returned to {p.cell}", "Undo")
        return True, f"Pickup undone. {p.code} returned to {p.cell}"

    def remind(self, code: str, urgent: bool | None = None) -> tuple[bool, str]:
        p = self.parcels.get(code)
        if not p or p.status not in ("pending", "notified"):
            return False, "This parcel does not need a reminder"
        if urgent is None:
            urgent = self.is_overdue(p)
        p.status = "notified"
        if urgent:
            self.remind_deque.appendleft({"code": code, "name": p.name, "urgent": True})
            self._log(f"{p.name}'s {code} is over 3 days old; inserted at the front of the urgent queue", "Urgent")
            return True, f"Urgent reminder queued for {p.name}'s parcel (from the front)"
        self.remind_deque.append({"code": code, "name": p.name, "urgent": False})
        self._log(f"{p.name}'s {code} joined the back of the regular reminder queue", "Reminder")
        return True, f"{p.name}'s parcel was added to the regular reminder queue"

    def send_reminder(self) -> tuple[bool, str]:
        if self.remind_deque.is_empty():
            return False, "The reminder queue is empty"
        item = self.remind_deque.popleft()
        tag = "urgent" if item["urgent"] else "regular"
        article = "an" if item["urgent"] else "a"
        self._log(f"Sent {article} {tag} pickup reminder to {item['name']}", "Sent")
        return True, f"Sent {item['name']} {article} {tag} SMS: pickup code {item['code']}"

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
            self._log(f"{code} waited {self.days_waiting(p)} days and was returned to the carrier; "
                      f"{cell_id or 'shelf'} released", "Return")
            return True, f"Returned {p.name}'s {code} after {self.days_waiting(p)} days"
        return False, "There are no overdue parcels to return"

    def merge_dorms(self, a: str, b: str) -> tuple[bool, str]:
        if self.dorm_groups.union(a, b):
            self._log(f"Pickup groups merged: {a} ↔ {b}", "Group")
            return True, f"{a} and {b} are now in the same pickup group"
        return False, "These dorms are already in the same pickup group"

    def notify_due(self) -> int:
        """Queue reminders for every parcel waiting more than 3 days (no duplicates)."""
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
            label = p.name if p else "Empty"
            code = p.code if p else "—"
            cells.append(
                f"<div style='border:1px solid {color}55;background:{color}10;border-radius:8px;padding:6px 4px;text-align:center'>"
                f"<div style='font-size:9.5px;color:#8fa3b8'>{cell.cell_id}</div>"
                f"<div style='font-size:11px;font-weight:700;color:{color}'>{ui.esc(label)}</div>"
                f"<div style='font-size:9px;color:#8fa3b8'>{ui.esc(code)}</div></div>"
            )
        rows.append(f"<div style='display:grid;grid-template-columns:repeat(8,1fr);gap:5px;margin-bottom:5px'>{''.join(cells)}</div>")
    return f"<div class='sl-card'><h4>Shelf map · 4 zones × 8 slots</h4><p>A 2D dynamic array: each slot is a Cell, and an empty code means the slot is free.</p><div style='margin-top:10px'>{''.join(rows)}</div></div>"


def sidebar(state: StationState) -> str:
    with st.sidebar:
        ui.sidebar_brand("03", SYSTEM, f"{GROUP} · 11 data structures", ACCENT)
        pages = ["Station Overview", "Intake & Shelving", "Pickup Queue", "Reminders", "Search",
                 "Delivery Route", "Pickup Groups", "Data Structures", "About"]
        page = st.radio("Navigate", pages, label_visibility="collapsed")
        st.markdown("---")
        ui.sidebar_status([
            ("Current day", f"Day {state.day}"),
            ("Awaiting pickup", f"{len(state.pending())} parcels"),
            ("Shelf occupancy", f"{sum(1 for c in state.cells() if c.code)} / 32"),
            ("Pickup queue", f"{len(state.pick_queue)} people"),
        ])
        st.markdown("---")
        if st.button("Advance one day →", use_container_width=True):
            state.day += 1
            state._log(f"Time advanced to day {state.day}", "Time")
            st.toast(f"Day {state.day} — remember to clear overdue parcels")
            st.rerun()
        if st.button("Undo last pickup", use_container_width=True):
            flash(*state.undo_pickup())
        ui.download_json({
            "day": state.day,
            "parcels": [p.__dict__ for p in state.parcels.values()],
            "shelf": {c.cell_id: c.code for c in state.cells()},
        }, "station-state.json", "Export system snapshot")
        st.caption("English edition · local Streamlit · data resets on refresh")
        # The Chinese edition label is HTML-encoded so this file stays free of Chinese characters.
        st.markdown('<a href="https://g3.algo.43.135.50.247.sslip.io" target="_blank">&#20013;&#25991;&#29256; ↗</a>',
                    unsafe_allow_html=True)
    return page


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------
def page_dashboard(state: StationState) -> None:
    ui.hero("GROUP 03 · PARCEL", SYSTEM,
            "Intake, shelving, queues, reminders, delivery, and proxy pickup — a parcel station is a small symphony of data structures.",
            ["14 seed parcels", "32 shelf slots", "11 data structures", f"Day {state.day}"])
    overdue = [p for p in state.pending() if state.is_overdue(p)]
    occupied = sum(1 for c in state.cells() if c.code)
    ui.kpis([
        {"label": "Awaiting pickup", "value": len(state.pending()), "sub": f"{len(overdue)} overdue", "accent": True},
        {"label": "Shelf occupancy", "value": occupied, "unit": "/ 32", "sub": "4 zones × 8 slots"},
        {"label": "Pickup queue", "value": len(state.pick_queue), "sub": "FIFO"},
        {"label": "Intake today", "value": sum(1 for p in state.parcels.values() if p.arrived == state.day), "unit": " parcels"},
    ])
    left, right = st.columns([1.1, 1])
    with left:
        ui.section("Intake volume · last 7 days", "Bars run high to low so peak days stand out")
        ui.bar_view([(f"D-{6 - i}", v) for i, v in enumerate([18, 24, 21, 30, 27, 35, 29])], " parcels")
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        ui.section("Longest waiting · top 5", "A min-heap ordered by arrival day; the root has waited longest")
        oldest = sorted(state.pending(), key=lambda p: p.arrived)[:5]
        ui.table_view(["Pickup code", "Recipient", "Slot", "Waiting"], [
            (p.code, p.name, p.cell or "-", f"{state.days_waiting(p)} days") for p in oldest
        ])
    with right:
        ui.section("Overdue alerts", "Anything over 3 days is flagged red; send reminders from the Reminders page")
        for p in overdue[:6]:
            st.markdown(f"- **{p.code}** {p.name} · {p.cell} · waiting {state.days_waiting(p)} days")
        if not overdue:
            ui.empty("No overdue parcels")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        ui.section("Parcel activity", "A singly linked list, appended in chronological order")
        ui.log_view([{"time": f"Day {e['day']}", "text": e["text"], "tag": e.get("tag", "")}
                     for e in list(state.flow)[::-1]], 7)
    st.markdown(shelf_html(state), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Intake and shelving
# ---------------------------------------------------------------------------
def page_intake(state: StationState) -> None:
    ui.hero("INTAKE", "Intake & Shelving",
            "Scan the label → register in a hash table → index by trie and BST → find a free slot in the dynamic array → queue reminders in the heap.",
            ["HashTable", "Trie", "BST", "DynamicArray", "MinHeap"])
    c1, c2 = st.columns([1, 1.2])
    with c1:
        ui.section("New parcel intake", "Automatically assigns the first free shelf slot")
        with st.form("intake"):
            name = st.text_input("Recipient", "Ava Patel")
            phone = st.text_input("Phone", "139****7788")
            dorm = st.text_input("Dorm", "Dorm 2-302")
            carrier = st.selectbox("Carrier", ["SF Express", "ZTO", "YTO", "JD", "Yunda"])
            weight = st.number_input("Weight (kg)", 0.1, 30.0, 2.0, step=0.1)
            go = st.form_submit_button("Add to shelves", type="primary", use_container_width=True)
        if go:
            if not name.strip() or not dorm.strip():
                st.error("Recipient and dorm are required")
            else:
                flash(*state.add_parcel(name.strip(), phone, dorm.strip(), carrier, float(weight)))
    with c2:
        ui.section("Shelf allocation strategy", "First free slot; O(32) linear scan")
        free = [c for c in state.cells() if c.code is None]
        ui.kpis([
            {"label": "Free slots", "value": len(free), "accent": True},
            {"label": "Zone A", "value": sum(1 for c in free if c.zone == "A")},
            {"label": "Zone B", "value": sum(1 for c in free if c.zone == "B")},
            {"label": "Zones C/D", "value": sum(1 for c in free if c.zone in ("C", "D"))},
        ])
        st.caption("To switch to weight-based zoning, change the selection rule in free_cell(); no other business logic needs to change.")
    st.markdown(shelf_html(state), unsafe_allow_html=True)
    ui.section("Parcels on shelves", f"{len(state.pending())} parcels")
    rows = []
    for p in sorted(state.pending(), key=lambda p: p.arrived):
        rows.append((p.code, p.name, p.dorm, p.carrier, f"{p.weight} kg", p.cell or "-", STATUS[p.status][0],
                     f"{state.days_waiting(p)} days"))
    ui.table_view(["Pickup code", "Recipient", "Dorm", "Carrier", "Weight", "Slot", "Status", "On shelf"], rows)


# ---------------------------------------------------------------------------
# Pickup queue
# ---------------------------------------------------------------------------
def page_pickup(state: StationState) -> None:
    ui.hero("PICKUP", "Pickup Queue",
            "Students scan in to join the line and the desk serves from the front; the slot is freed immediately, with one undo kept on the stack.",
            ["Queue", "Stack", "HashTable", "DynamicArray"])
    ui.kpis([
        {"label": "In queue", "value": len(state.pick_queue), "accent": True},
        {"label": "Awaiting pickup", "value": len(state.pending())},
        {"label": "Picked up today", "value": sum(1 for p in state.parcels.values() if p.picked_day == state.day)},
        {"label": "Undo available", "value": len(state.undo)},
    ])
    c1, c2 = st.columns(2)
    with c1:
        ui.section("Scan into the queue", "First come, first served — no cutting in line")
        with st.form("enqueue"):
            code = st.text_input("Pickup code", "100003")
            go = st.form_submit_button("Join pickup queue", type="primary", use_container_width=True)
        if go:
            flash(*state.enqueue_pickup(code.strip()))
    with c2:
        ui.section("Desk counter", "Dequeue from the front, verify, then mark as picked up")
        if st.button("Call next pickup", type="primary", use_container_width=True):
            flash(*state.serve_pickup())
        st.caption("If the parcel at the front was already collected, it is skipped automatically and reported as an anomaly.")

    ui.section("Current pickup queue", "Circular queue · the front of the line is served first")
    q = state.pick_queue.to_list()
    if q:
        ui.queue_html([f"{i['name']} · {i['code']}" for i in q])
    else:
        ui.empty("The queue is empty")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    ui.section("Activity log", "Every pickup is pushed onto the stack for a one-step undo")
    ui.log_view([{"time": f"Day {e['day']}", "text": e["text"], "tag": e.get("tag", "")}
                 for e in list(state.flow)[::-1]], 8)
    with st.expander("See the code: what changes during a pickup"):
        st.code(
            """item = pick_queue.dequeue()      # Queue: remove from the front
p = parcels.get(item["code"])     # Hash: O(1) parcel lookup
p.status = "picked"
set_cell(p.cell, None)            # Array: free the shelf slot
undo.push({...})                  # Stack: record an undoable action
flow.append(...)                  # Linked list: append to the log""",
            language="python",
        )


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------
def page_remind(state: StationState) -> None:
    ui.hero("REMINDERS", "Reminders",
            "Overdue parcels enter from the left as urgent, regular ones queue on the right, and the heap root is always the parcel that has waited longest.",
            ["Deque", "MinHeap", "Queue"])
    overdue = [p for p in state.pending() if state.is_overdue(p)]
    ui.kpis([
        {"label": "Reminder queue", "value": len(state.remind_deque), "accent": True},
        {"label": "Overdue parcels", "value": len(overdue)},
        {"label": "Longest wait", "value": max((state.days_waiting(p) for p in state.pending()), default=0), "unit": " days"},
        {"label": "Returned", "value": sum(1 for p in state.parcels.values() if p.status == "returned")},
    ])
    c1, c2 = st.columns(2)
    with c1:
        ui.section("Add a reminder manually", "Overdue parcels automatically take the urgent (left) end")
        with st.form("remind"):
            code = st.text_input("Pickup code", overdue[0].code if overdue else "100003")
            urgent = st.checkbox("Urgent (insert at the front)", value=True)
            go = st.form_submit_button("Add to reminder queue", type="primary", use_container_width=True)
        if go:
            flash(*state.remind(code.strip(), urgent))
        if st.button("Scan for overdue parcels", use_container_width=True):
            n = state.notify_due()
            flash(n > 0, f"Queued {n} overdue {'parcel' if n == 1 else 'parcels'} "
                         f"as {'an urgent reminder' if n == 1 else 'urgent reminders'}")
    with c2:
        ui.section("Send reminders", "Pop from the left of the deque (urgent first)")
        if st.button("Send next reminder", type="primary", use_container_width=True):
            flash(*state.send_reminder())
        if st.button("Return longest-waiting parcel", use_container_width=True):
            flash(*state.return_oldest())
        st.caption("Returning pops the heap root for real and frees the matching shelf slot.")
    ui.section("Reminder queue", "Left = urgent · right = regular")
    st.markdown(ui.deque_html([f"{i['name']} · {i['code']}{'!' if i['urgent'] else ''}"
                               for i in state.remind_deque.to_list()]), unsafe_allow_html=True)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    ui.section("Overdue heap", "Ordered by arrival day ascending; the root has waited longest")
    items = [(pr, f"{code} {state.parcels.get(code).name}")
             for pr, code in state.overdue_heap.to_list()
             if state.parcels.get(code) and state.parcels.get(code).status in ("pending", "notified")]
    st.markdown(ui.heap_html(items[:15], priority_fmt="Day {}"), unsafe_allow_html=True)
    st.caption("Picked-up and returned parcels may still sit in the heap (lazy deletion); status is checked when popping.")


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------
def page_query(state: StationState) -> None:
    ui.hero("SEARCH", "Search",
            "Three indexes, three jobs: hash for codes, trie for names, BST for weight ranges.",
            ["HashTable", "Trie", "BST", "LinkedList"])
    tab1, tab2, tab3 = st.tabs(["Code · hash", "Recipient · trie", "Weight range · BST"])
    with tab1:
        code = st.text_input("Pickup code", "100007", key="q_code")
        p = state.parcels.get(code)
        if p:
            ui.card(
                f"<h4>{ui.esc(p.name)} · {ui.esc(p.carrier)}</h4>"
                f"<p>Pickup code {p.code} · {p.dorm} · {p.weight} kg · arrived day {p.arrived} · "
                f"slot {p.cell or 'released'} · status {STATUS[p.status][0]}</p>"
            )
            ui.section("Activity for this parcel", "Filtered from the singly linked list")
            ui.log_view([{"time": f"Day {e['day']}", "text": e["text"], "tag": e.get("tag", "")}
                         for e in state.flow if p.code in e["text"]][::-1], 8)
        else:
            ui.empty("No parcel found for that pickup code")
    with tab2:
        prefix = st.text_input("Recipient name or prefix", "Alice", key="q_name")
        hits = state.name_trie.autocomplete(prefix, 8)
        st.caption(f"{len(hits)} matching {'recipient' if len(hits) == 1 else 'recipients'}; the trie descends one character at a time.")
        for name, code in hits:
            p = state.parcels.get(code)
            st.markdown(f"- **{name}** · {code} · {p.dorm if p else ''} · {STATUS[p.status][0] if p else ''}")
        if not hits:
            ui.empty("No matching recipients")
        ui.visual_label("Recipient entries")
        st.markdown(ui.trie_html(state.name_trie.words(30), prefix), unsafe_allow_html=True)
    with tab3:
        lo, hi = st.slider("Weight range (kg)", 0.0, 20.0, (2.0, 8.0), step=0.5, key="q_weight")
        results = state.weight_bst.range_query((lo, ""), (hi, "\uffff"))
        st.caption(f"BST returned {len(results)} {'parcel' if len(results) == 1 else 'parcels'}; tree height {state.weight_bst.height()}.")
        ui.table_view(["Recipient", "Weight", "Pickup code"], [
            (name, f"{key[0]} kg", key[1]) for key, name in results
        ])
        ui.visual_label("Weight BST · key = (weight, pickup code)")
        st.markdown(ui.bst_html(state.weight_bst.levels()), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Delivery route
# ---------------------------------------------------------------------------
def page_route(state: StationState) -> None:
    ui.hero("DELIVERY", "Delivery Route",
            "The station, dorms, and cafeteria form a weighted graph; Dijkstra finds the shortest walking route.",
            ["Graph", "Dijkstra", "BFS", "UnionFind"])
    nodes = state.route_graph.nodes()
    c1, c2 = st.columns(2)
    with c1:
        start = st.selectbox("Start", nodes, index=0, key="r_start")
    with c2:
        target = st.selectbox("Destination", nodes, index=3, key="r_target")
    if st.button("Plan delivery route", type="primary", use_container_width=True):
        path, dist = state.route_graph.shortest_path(start, target)
        st.session_state.g3_path = (path, dist)
    path, dist = st.session_state.get("g3_path", ([], 0))
    if path:
        st.success(f"Shortest route: {' → '.join(path)} · about {dist:g} minutes")
    ui.visual_label("Campus delivery graph")
    st.markdown(ui.graph_html(nodes, state.route_graph.edges(), highlight_nodes=[start, target], path=path),
                unsafe_allow_html=True)
    ui.section("Connectivity check", "If construction closes a road, the graph can split into separate components")
    comps = state.route_graph.components()
    ui.table_view(["Component", "Nodes"], [(f"#{i + 1}", ", ".join(c)) for i, c in enumerate(comps)])


# ---------------------------------------------------------------------------
# Pickup groups
# ---------------------------------------------------------------------------
def page_groups(state: StationState) -> None:
    ui.hero("PICKUP GROUPS", "Pickup Groups",
            "Roommates and neighbours on the same floor can collect for each other. Union-find merges every 'can collect for me' pair into a group.",
            ["UnionFind", "Path Compression"])
    ui.kpis([
        {"label": "Dorms", "value": len(state.dorm_groups)},
        {"label": "Pickup groups", "value": state.dorm_groups.group_count, "accent": True},
        {"label": "Largest group", "value": max((len(v) for v in state.dorm_groups.groups().values()), default=0), "unit": " dorms"},
        {"label": "Merges", "value": sum(1 for e in state.flow if e.get("tag") == "Group")},
    ])
    ui.section("Current pickup groups", "Any member of a group can collect for the others")
    st.markdown(ui.union_html(state.dorm_groups.groups()), unsafe_allow_html=True)
    dorms = sorted(state.dorm_groups.parent.keys())
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        a = st.selectbox("Dorm A", dorms, key="g_a")
    with c2:
        b = st.selectbox("Dorm B", dorms, index=1, key="g_b")
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("Merge pickup groups", type="primary", use_container_width=True):
            flash(*state.merge_dorms(a, b))
    st.caption(f"connected({a}, {b}) = {state.dorm_groups.connected(a, b)}")
    ui.note("Union-find supports merging but not splitting. If the station ever needs to dissolve a pickup relationship, "
            "it would have to use a graph or a union-find variant with deletion — a natural extension for this group to explore.",
            title="Design note")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
def page_structures(state: StationState) -> None:
    ui.hero("DATA STRUCTURES", "11 data structures at a glance",
            "From the shelf to the delivery route, every structure maps to a real station operation.",
            ["Array", "Linked List", "Stack", "Queue", "Deque", "Hash", "Heap", "BST", "Trie", "Graph", "Union-Find"])
    with st.expander("① Dynamic array · 4×8 shelf", expanded=True):
        st.markdown(ui.array_html([f"{c.cell_id}:{c.code or 'free'}" for c in state.cells()], max_cells=16),
                    unsafe_allow_html=True)
        st.caption(f"4 outer rows with 8 slots each; size={len(state.shelf)}, capacity per row={state.shelf[0].capacity}")
    with st.expander("② Singly linked list · parcel activity"):
        st.markdown(ui.linked_html([f"Day {e['day']} {e['text']}" for e in list(state.flow)[-5:]]),
                    unsafe_allow_html=True)
    with st.expander("③ Stack · undo pickup"):
        st.markdown(ui.stack_html([f"Pickup {a['code']}" for a in state.undo.to_list()]), unsafe_allow_html=True)
    with st.expander("④ Queue · pickup line"):
        st.markdown(ui.queue_html([f"{i['name']} · {i['code']}" for i in state.pick_queue.to_list()]),
                    unsafe_allow_html=True)
        st.caption(f"size={len(state.pick_queue)} · capacity={state.pick_queue.capacity}")
    with st.expander("⑤ Deque · reminders"):
        st.markdown(ui.deque_html([f"{i['name']}{'!' if i['urgent'] else ''}" for i in state.remind_deque.to_list()]),
                    unsafe_allow_html=True)
    with st.expander("⑥ Hash table · pickup-code index"):
        st.markdown(ui.hash_html(state.parcels.buckets(), 12), unsafe_allow_html=True)
        st.caption(f"{len(state.parcels)} parcels · {state.parcels.capacity} buckets · load factor {state.parcels.load_factor:.2f}")
    with st.expander("⑦ Min-heap · longest wait"):
        st.markdown(ui.heap_html([(p.arrived, f"{p.code} {p.name}") for p in state.pending()][:15],
                                 priority_fmt="Day {}"), unsafe_allow_html=True)
    with st.expander("⑧ Binary search tree · weight index"):
        st.markdown(ui.bst_html(state.weight_bst.levels()), unsafe_allow_html=True)
        st.caption(f"Tree height {state.weight_bst.height()}")
    with st.expander("⑨ Trie · recipients"):
        st.markdown(ui.trie_html(state.name_trie.words(30), ""), unsafe_allow_html=True)
    with st.expander("⑩ Graph · campus delivery"):
        st.markdown(ui.graph_html(state.route_graph.nodes(), state.route_graph.edges()), unsafe_allow_html=True)
    with st.expander("⑪ Union-find · pickup groups"):
        st.markdown(ui.union_html(state.dorm_groups.groups()), unsafe_allow_html=True)


ROLES = [
    ("Team lead / project manager", "Scheduling, integration, demo coordination", "Plan + weekly reports + final defense"),
    ("Linear structures lead", "Array, linked list, stack, queue, deque", "First 5 classes in ds_core.py + tests"),
    ("Search structures lead", "Hash table, heap, BST", "Next 3 classes in ds_core.py + tests"),
    ("Non-linear structures lead", "Trie, graph, union-find", "Last 3 classes in ds_core.py + tests"),
    ("Station operations engineer", "Intake, shelving, pickup, returns", "Business functions + flow diagrams"),
    ("UI engineer", "Shelf map, queue, reminder panels", "UI components + screenshots"),
    ("Data engineer", "Seed parcels, state consistency, export", "Seed data + export"),
    ("QA engineer", "Full shelves, duplicate pickups, undo conflicts", "tests/ + defect log"),
    ("Deployment engineer", "Local run, dependencies, demo environment", "Launch scripts + deployment notes"),
    ("Docs / demo", "README, handbook, slides", "Documentation + 8-minute demo"),
]

MAP = [
    ("Dynamic array", "shelf", "4×8 shelf"),
    ("Singly linked list", "flow", "Parcel activity log"),
    ("Stack", "undo", "Undo pickup"),
    ("Queue", "pick_queue", "FIFO pickup line"),
    ("Deque", "remind_deque", "Urgent at the front / regular at the back"),
    ("Hash table", "parcels", "Pickup code → parcel"),
    ("Min-heap", "overdue_heap", "Return the longest-waiting parcel first"),
    ("BST", "weight_bst", "Weight range queries"),
    ("Trie", "name_trie", "Recipient prefix search"),
    ("Graph", "route_graph", "Shortest campus delivery route"),
    ("Union-find", "dorm_groups", "Dorm pickup groups"),
]


def page_about(state: StationState) -> None:
    ui.hero("GROUP 03 · PLAYBOOK", "About Group 3",
            f"{SUBTITLE} — one station, ten roles. Get the parcels moving first, then let the data structures do the talking.",
            ["8–10 people", "4 weekly sprints", "Runs locally"])
    ui.section("Roles & responsibilities", "In an 8-person team, docs merge into the lead role; in a 9-person team, deployment merges into QA")
    ui.table_view(["Role", "Responsibilities", "Deliverable"], ROLES)
    ui.section("Data structure map", "Defense spot-check sheet")
    ui.table_view(["Structure", "Where in the code", "Station use case"], MAP)
    ui.section("Four-week iteration", "")
    ui.table_view(["Week", "Goal", "Acceptance signal"], [
        ("Week 1", "Get it running, read the code, claim roles", "Everyone can demo intake and pickup once"),
        ("Week 2", "Close the loop: intake → queue → pickup → undo", "Main flow runs 5 times without errors"),
        ("Week 3", "Reminders / search / routes / proxy pickup", "Edge cases pass"),
        ("Week 4", "Polish, document, demo", "8-minute defense"),
    ])
    st.info("Run locally: pip install -r requirements.txt && streamlit run app_en.py (or double-click run_en.bat on Windows)")


def main() -> None:
    state = get_state()
    show_flash()
    page = sidebar(state)
    if page == "Station Overview":
        page_dashboard(state)
    elif page == "Intake & Shelving":
        page_intake(state)
    elif page == "Pickup Queue":
        page_pickup(state)
    elif page == "Reminders":
        page_remind(state)
    elif page == "Search":
        page_query(state)
    elif page == "Delivery Route":
        page_route(state)
    elif page == "Pickup Groups":
        page_groups(state)
    elif page == "Data Structures":
        page_structures(state)
    else:
        page_about(state)


main()
