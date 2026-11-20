"""ds_core.py —— 从零实现的 11 种数据结构（教学版）

本文件不依赖任何第三方库，四个小组系统共用。
每个类都尽量保留“教科书结构”，并在方法上标注时间复杂度，
方便同学一边点界面、一边对照代码。

覆盖：
1. DynamicArray 动态数组
2. LinkedList   单链表
3. Stack        栈
4. Queue        循环队列
5. Deque        双端队列
6. HashTable    哈希表（拉链法）
7. MinHeap      小顶堆（优先队列）
8. BST          二叉搜索树
9. Trie         字典树 / 前缀树
10. Graph       图（邻接表，BFS / DFS / Dijkstra）
11. UnionFind   并查集（路径压缩 + 按大小合并）

约定：所有结构都提供 to_list() 或等价方法，界面层只读展示，
业务层负责修改，二者不混在一起。
"""
from __future__ import annotations

import heapq
import math
from collections import deque as _py_deque
from typing import Any, Callable, Iterable, Iterator

_LANG = "zh"


def set_lang(lang: str) -> None:
    """Switch exception messages between Chinese and English."""
    global _LANG
    _LANG = "en" if str(lang).lower().startswith("en") else "zh"


def _t(zh: str, en: str) -> str:
    return en if _LANG == "en" else zh


# ---------------------------------------------------------------------------
# 1. 动态数组
# ---------------------------------------------------------------------------
class DynamicArray:
    """连续内存 + 逻辑长度 + 物理容量；扩容时容量翻倍。

    append 均摊 O(1)，按下标访问 O(1)，中间插入/删除 O(n)。
    """

    def __init__(self, capacity: int = 8, items: Iterable[Any] | None = None) -> None:
        self._capacity = max(1, int(capacity))
        self._data: list[Any] = [None] * self._capacity
        self._size = 0
        if items:
            for item in items:
                self.append(item)

    # -- 只读属性 ---------------------------------------------------------
    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def size(self) -> int:
        return self._size

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity if self._capacity else 0.0

    # -- 基本操作 ---------------------------------------------------------
    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        for i in range(self._size):
            yield self._data[i]

    def __getitem__(self, index: int) -> Any:
        self._check_index(index)
        if index < 0:
            index += self._size
            self._check_index(index)
        return self._data[index]

    def __setitem__(self, index: int, value: Any) -> None:
        self._check_index(index)
        if index < 0:
            index += self._size
            self._check_index(index)
        self._data[index] = value

    def _check_index(self, index: int) -> None:
        if not -self._size <= index < self._size:
            raise IndexError(_t(f"下标越界：{index}，当前长度 {self._size}", f"Index out of range: {index}, size {self._size}"))

    def _grow(self) -> None:
        old = self._data
        self._capacity *= 2
        self._data = [None] * self._capacity
        for i in range(self._size):
            self._data[i] = old[i]

    def _shrink(self) -> None:
        if self._capacity > 8 and self._size <= self._capacity // 4:
            self._capacity //= 2
            self._data = self._data[: self._capacity] + [None] * (self._capacity - self._size)

    def append(self, value: Any) -> None:
        """尾部追加，均摊 O(1)。"""
        if self._size == self._capacity:
            self._grow()
        self._data[self._size] = value
        self._size += 1

    def insert(self, index: int, value: Any) -> None:
        """在 index 前插入，O(n)。index == size 表示追加。"""
        if index < 0:
            index += self._size
        if not 0 <= index <= self._size:
            raise IndexError(_t(f"插入下标越界：{index}", f"Insert index out of range: {index}"))
        if self._size == self._capacity:
            self._grow()
        for i in range(self._size, index, -1):
            self._data[i] = self._data[i - 1]
        self._data[index] = value
        self._size += 1

    def pop(self, index: int = -1) -> Any:
        """删除并返回下标元素，O(n)。"""
        if self._size == 0:
            raise IndexError(_t("数组为空", "Array is empty"))
        if index < 0:
            index += self._size
        self._check_index(index)
        value = self._data[index]
        for i in range(index, self._size - 1):
            self._data[i] = self._data[i + 1]
        self._data[self._size - 1] = None
        self._size -= 1
        self._shrink()
        return value

    def remove(self, value: Any) -> bool:
        for i in range(self._size):
            if self._data[i] == value:
                self.pop(i)
                return True
        return False

    def index_of(self, value: Any) -> int:
        for i in range(self._size):
            if self._data[i] == value:
                return i
        return -1

    def to_list(self) -> list[Any]:
        return list(self._data[: self._size])

    def __repr__(self) -> str:
        return f"DynamicArray({self.to_list()}, size={self._size}/{self._capacity})"


# ---------------------------------------------------------------------------
# 2. 单链表
# ---------------------------------------------------------------------------
class _ListNode:
    __slots__ = ("value", "next")

    def __init__(self, value: Any, next: "_ListNode | None" = None) -> None:
        self.value = value
        self.next = next


class LinkedList:
    """单链表；维护 head / tail / size，尾插 O(1)。

    “按值删除”需要先找到前驱，O(n)；头插 O(1)。
    """

    def __init__(self, items: Iterable[Any] | None = None) -> None:
        self.head: _ListNode | None = None
        self.tail: _ListNode | None = None
        self._size = 0
        if items:
            for item in items:
                self.append(item)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[Any]:
        node = self.head
        while node:
            yield node.value
            node = node.next

    def append(self, value: Any) -> None:
        node = _ListNode(value)
        if self.tail is None:
            self.head = self.tail = node
        else:
            self.tail.next = node
            self.tail = node
        self._size += 1

    def prepend(self, value: Any) -> None:
        node = _ListNode(value, self.head)
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1

    def remove(self, value: Any) -> bool:
        prev, cur = None, self.head
        while cur:
            if cur.value == value:
                if prev is None:
                    self.head = cur.next
                else:
                    prev.next = cur.next
                if cur is self.tail:
                    self.tail = prev
                self._size -= 1
                return True
            prev, cur = cur, cur.next
        return False

    def find(self, predicate: Callable[[Any], bool]) -> Any | None:
        for value in self:
            if predicate(value):
                return value
        return None

    def to_list(self) -> list[Any]:
        return list(self)

    def last(self, n: int = 5) -> list[Any]:
        """返回最近 n 条（链表尾部在“最近”一侧）。"""
        values = self.to_list()
        return values[-n:][::-1]


# ---------------------------------------------------------------------------
# 3. 栈
# ---------------------------------------------------------------------------
class Stack:
    """后进先出（LIFO）。内部用 DynamicArray，push/pop 均摊 O(1)。"""

    def __init__(self, items: Iterable[Any] | None = None) -> None:
        self._items = DynamicArray(items=list(items or []))

    def __len__(self) -> int:
        return len(self._items)

    def push(self, value: Any) -> None:
        self._items.append(value)

    def pop(self) -> Any:
        if not self._items:
            raise IndexError(_t("栈为空", "Stack is empty"))
        return self._items.pop()

    def peek(self) -> Any | None:
        return self._items[-1] if self._items else None

    def is_empty(self) -> bool:
        return len(self._items) == 0

    def to_list(self) -> list[Any]:
        """返回从栈底到栈顶的列表。"""
        return self._items.to_list()

    def top_first(self, n: int = 8) -> list[Any]:
        return list(reversed(self._items.to_list()))[:n]


# ---------------------------------------------------------------------------
# 4. 循环队列
# ---------------------------------------------------------------------------
class Queue:
    """数组实现的循环队列；head/tail 指针避免整体搬移。

    入队/出队均摊 O(1)，容量不足时翻倍。
    """

    def __init__(self, capacity: int = 8) -> None:
        self._capacity = max(2, int(capacity))
        self._data: list[Any] = [None] * self._capacity
        self._head = 0
        self._tail = 0
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def _resize(self, new_capacity: int) -> None:
        new_data: list[Any] = [None] * new_capacity
        for i in range(self._size):
            new_data[i] = self._data[(self._head + i) % self._capacity]
        self._data = new_data
        self._capacity = new_capacity
        self._head = 0
        self._tail = self._size

    def enqueue(self, value: Any) -> None:
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._data[self._tail] = value
        self._tail = (self._tail + 1) % self._capacity
        self._size += 1

    def dequeue(self) -> Any:
        if self._size == 0:
            raise IndexError(_t("队列为空", "Queue is empty"))
        value = self._data[self._head]
        self._data[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        return value

    def peek(self) -> Any | None:
        return self._data[self._head] if self._size else None

    def to_list(self) -> list[Any]:
        """从队头到队尾。"""
        return [self._data[(self._head + i) % self._capacity] for i in range(self._size)]


# ---------------------------------------------------------------------------
# 5. 双端队列
# ---------------------------------------------------------------------------
class Deque:
    """两端都可以插入/删除的队列；此处用循环数组实现。

    两端操作均摊 O(1)。
    """

    def __init__(self, capacity: int = 8) -> None:
        self._capacity = max(2, int(capacity))
        self._data: list[Any] = [None] * self._capacity
        self._head = 0
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self._size == 0

    @property
    def capacity(self) -> int:
        return self._capacity

    def _resize(self, new_capacity: int) -> None:
        new_data: list[Any] = [None] * new_capacity
        for i in range(self._size):
            new_data[i] = self._data[(self._head + i) % self._capacity]
        self._data = new_data
        self._capacity = new_capacity
        self._head = 0

    def appendleft(self, value: Any) -> None:
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._head = (self._head - 1) % self._capacity
        self._data[self._head] = value
        self._size += 1

    def append(self, value: Any) -> None:
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._data[(self._head + self._size) % self._capacity] = value
        self._size += 1

    def popleft(self) -> Any:
        if self._size == 0:
            raise IndexError(_t("双端队列为空", "Deque is empty"))
        value = self._data[self._head]
        self._data[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._size -= 1
        return value

    def pop(self) -> Any:
        if self._size == 0:
            raise IndexError(_t("双端队列为空", "Deque is empty"))
        index = (self._head + self._size - 1) % self._capacity
        value = self._data[index]
        self._data[index] = None
        self._size -= 1
        return value

    def peekleft(self) -> Any | None:
        return self._data[self._head] if self._size else None

    def peekright(self) -> Any | None:
        return self._data[(self._head + self._size - 1) % self._capacity] if self._size else None

    def to_list(self) -> list[Any]:
        """从左端到右端。"""
        return [self._data[(self._head + i) % self._capacity] for i in range(self._size)]


# ---------------------------------------------------------------------------
# 6. 哈希表（拉链法）
# ---------------------------------------------------------------------------
class HashTable:
    """拉链法哈希表；负载因子超过 0.75 时容量翻倍。

    平均 O(1) 查找/插入/删除；最坏 O(n)（全部冲突）。
    """

    def __init__(self, capacity: int = 8) -> None:
        self._capacity = max(4, int(capacity))
        self._buckets: list[list[tuple[Any, Any]]] = [[] for _ in range(self._capacity)]
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: Any) -> bool:
        return self.get(key, _MISSING) is not _MISSING

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity

    def _bucket_index(self, key: Any) -> int:
        return hash(key) % self._capacity

    def put(self, key: Any, value: Any) -> None:
        bucket = self._buckets[self._bucket_index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1
        if self.load_factor > 0.75:
            self._resize(self._capacity * 2)

    def get(self, key: Any, default: Any = None) -> Any:
        for k, v in self._buckets[self._bucket_index(key)]:
            if k == key:
                return v
        return default

    def delete(self, key: Any) -> bool:
        bucket = self._buckets[self._bucket_index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def _resize(self, new_capacity: int) -> None:
        old = self._buckets
        self._capacity = new_capacity
        self._buckets = [[] for _ in range(new_capacity)]
        self._size = 0
        for bucket in old:
            for k, v in bucket:
                self.put(k, v)

    def keys(self) -> list[Any]:
        return [k for bucket in self._buckets for k, _ in bucket]

    def values(self) -> list[Any]:
        return [v for bucket in self._buckets for _, v in bucket]

    def items(self) -> list[tuple[Any, Any]]:
        return [pair for bucket in self._buckets for pair in bucket]

    def bucket_sizes(self) -> list[int]:
        return [len(b) for b in self._buckets]

    def buckets(self) -> list[list[tuple[Any, Any]]]:
        return [list(b) for b in self._buckets]


_MISSING = object()


# ---------------------------------------------------------------------------
# 7. 小顶堆
# ---------------------------------------------------------------------------
class MinHeap:
    """数组实现的小顶堆；父节点 <= 子节点。

    push / pop 均为 O(log n)，peek O(1)。
    相同优先级按入堆顺序（seq）稳定排序，避免比较业务对象。
    """

    def __init__(self) -> None:
        self._data: list[tuple[float, int, Any]] = []
        self._seq = 0

    def __len__(self) -> int:
        return len(self._data)

    def is_empty(self) -> bool:
        return not self._data

    def push(self, priority: float, item: Any) -> None:
        self._seq += 1
        self._data.append((priority, self._seq, item))
        self._sift_up(len(self._data) - 1)

    def peek(self) -> Any | None:
        return self._data[0][2] if self._data else None

    def peek_priority(self) -> float | None:
        return self._data[0][0] if self._data else None

    def pop(self) -> Any:
        if not self._data:
            raise IndexError(_t("堆为空", "Heap is empty"))
        root = self._data[0]
        last = self._data.pop()
        if self._data:
            self._data[0] = last
            self._sift_down(0)
        return root[2]

    def _sift_up(self, index: int) -> None:
        while index > 0:
            parent = (index - 1) // 2
            if self._data[parent][:2] <= self._data[index][:2]:
                break
            self._data[parent], self._data[index] = self._data[index], self._data[parent]
            index = parent

    def _sift_down(self, index: int) -> None:
        n = len(self._data)
        while True:
            left = index * 2 + 1
            right = left + 1
            smallest = index
            if left < n and self._data[left][:2] < self._data[smallest][:2]:
                smallest = left
            if right < n and self._data[right][:2] < self._data[smallest][:2]:
                smallest = right
            if smallest == index:
                break
            self._data[index], self._data[smallest] = self._data[smallest], self._data[index]
            index = smallest

    def to_list(self) -> list[tuple[float, Any]]:
        """按堆数组顺序返回 (priority, item)，不是有序结果。"""
        return [(p, item) for p, _, item in self._data]

    def sorted_items(self) -> list[tuple[float, Any]]:
        """返回有序副本，O(n log n)，仅用于展示。"""
        return [(p, item) for p, _, item in sorted(self._data, key=lambda x: x[:2])]


# ---------------------------------------------------------------------------
# 8. 二叉搜索树
# ---------------------------------------------------------------------------
class _BSTNode:
    __slots__ = ("key", "value", "left", "right")

    def __init__(self, key: Any, value: Any) -> None:
        self.key = key
        self.value = value
        self.left: "_BSTNode | None" = None
        self.right: "_BSTNode | None" = None


class BST:
    """按 key 排序的二叉搜索树；中序遍历得到有序序列。

    平均 O(log n)，最坏 O(n)（退化成链表）。
    """

    def __init__(self) -> None:
        self.root: _BSTNode | None = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, key: Any, value: Any) -> None:
        if self.root is None:
            self.root = _BSTNode(key, value)
            self._size = 1
            return
        node = self.root
        while True:
            if key == node.key:
                node.value = value
                return
            if key < node.key:
                if node.left is None:
                    node.left = _BSTNode(key, value)
                    self._size += 1
                    return
                node = node.left
            else:
                if node.right is None:
                    node.right = _BSTNode(key, value)
                    self._size += 1
                    return
                node = node.right

    def search(self, key: Any) -> Any | None:
        node = self.root
        while node:
            if key == node.key:
                return node.value
            node = node.left if key < node.key else node.right
        return None

    def delete(self, key: Any) -> bool:
        self.root, removed = self._delete(self.root, key)
        if removed:
            self._size -= 1
        return removed

    def _delete(self, node: _BSTNode | None, key: Any) -> tuple[_BSTNode | None, bool]:
        if node is None:
            return None, False
        if key < node.key:
            node.left, removed = self._delete(node.left, key)
            return node, removed
        if key > node.key:
            node.right, removed = self._delete(node.right, key)
            return node, removed
        # 找到目标
        if node.left is None:
            return node.right, True
        if node.right is None:
            return node.left, True
        successor = node.right
        while successor.left:
            successor = successor.left
        node.key, node.value = successor.key, successor.value
        node.right, _ = self._delete(node.right, successor.key)
        return node, True

    def inorder(self) -> list[tuple[Any, Any]]:
        out: list[tuple[Any, Any]] = []

        def walk(node: _BSTNode | None) -> None:
            if not node:
                return
            walk(node.left)
            out.append((node.key, node.value))
            walk(node.right)

        walk(self.root)
        return out

    def range_query(self, low: Any, high: Any) -> list[tuple[Any, Any]]:
        """闭区间 [low, high]，利用 BST 性质剪枝。"""
        out: list[tuple[Any, Any]] = []

        def walk(node: _BSTNode | None) -> None:
            if not node:
                return
            if low < node.key:
                walk(node.left)
            if low <= node.key <= high:
                out.append((node.key, node.value))
            if node.key < high:
                walk(node.right)

        walk(self.root)
        return out

    def height(self) -> int:
        def walk(node: _BSTNode | None) -> int:
            if not node:
                return 0
            return 1 + max(walk(node.left), walk(node.right))

        return walk(self.root)

    def levels(self) -> list[list[tuple[Any, Any] | None]]:
        """按层返回节点，空位用 None 补齐，便于界面画树。"""
        if not self.root:
            return []
        levels: list[list[tuple[Any, Any] | None]] = []
        current: list[_BSTNode | None] = [self.root]
        while any(current):
            levels.append([(n.key, n.value) if n else None for n in current])
            nxt: list[_BSTNode | None] = []
            for n in current:
                if n is None:
                    nxt.extend([None, None])
                else:
                    nxt.extend([n.left, n.right])
            current = nxt
        return levels


# ---------------------------------------------------------------------------
# 9. 字典树
# ---------------------------------------------------------------------------
class _TrieNode:
    __slots__ = ("children", "is_end", "payload")

    def __init__(self) -> None:
        self.children: dict[str, "_TrieNode"] = {}
        self.is_end = False
        self.payload: Any = None


class Trie:
    """前缀树；插入/查询 O(L)，L 为字符串长度。"""

    def __init__(self) -> None:
        self.root = _TrieNode()
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, word: str, payload: Any = None) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = _TrieNode()
            node = node.children[ch]
        if not node.is_end:
            self._size += 1
        node.is_end = True
        node.payload = payload

    def search(self, word: str) -> Any | None:
        node = self._find_node(word)
        return node.payload if node and node.is_end else None

    def contains(self, word: str) -> bool:
        node = self._find_node(word)
        return bool(node and node.is_end)

    def starts_with(self, prefix: str) -> bool:
        return self._find_node(prefix) is not None

    def _find_node(self, text: str) -> _TrieNode | None:
        node = self.root
        for ch in text:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def autocomplete(self, prefix: str, limit: int = 8) -> list[tuple[str, Any]]:
        node = self._find_node(prefix)
        if node is None:
            return []
        out: list[tuple[str, Any]] = []

        def walk(cur: _TrieNode, path: str) -> None:
            if len(out) >= limit:
                return
            if cur.is_end:
                out.append((prefix + path, cur.payload))
            for ch in sorted(cur.children):
                walk(cur.children[ch], path + ch)
                if len(out) >= limit:
                    return

        walk(node, "")
        return out

    def words(self, limit: int = 50) -> list[str]:
        out: list[str] = []

        def walk(cur: _TrieNode, path: str) -> None:
            if len(out) >= limit:
                return
            if cur.is_end and path:
                out.append(path)
            for ch in sorted(cur.children):
                walk(cur.children[ch], path + ch)
                if len(out) >= limit:
                    return

        walk(self.root, "")
        return out


# ---------------------------------------------------------------------------
# 10. 图（邻接表）
# ---------------------------------------------------------------------------
class Graph:
    """带权无向图 / 有向图；邻接表存储。

    BFS / DFS O(V+E)，Dijkstra O((V+E) log V)。
    """

    def __init__(self, directed: bool = False) -> None:
        self.directed = directed
        self._adj: dict[Any, dict[Any, float]] = {}

    def add_node(self, node: Any) -> None:
        self._adj.setdefault(node, {})

    def add_edge(self, u: Any, v: Any, weight: float = 1.0) -> None:
        self.add_node(u)
        self.add_node(v)
        self._adj[u][v] = weight
        if not self.directed:
            self._adj[v][u] = weight

    def remove_edge(self, u: Any, v: Any) -> bool:
        removed = False
        if v in self._adj.get(u, {}):
            del self._adj[u][v]
            removed = True
        if not self.directed and u in self._adj.get(v, {}):
            del self._adj[v][u]
            removed = True
        return removed

    def nodes(self) -> list[Any]:
        return list(self._adj.keys())

    def neighbors(self, node: Any) -> dict[Any, float]:
        return dict(self._adj.get(node, {}))

    def edges(self) -> list[tuple[Any, Any, float]]:
        seen: set[tuple[Any, Any]] = set()
        out: list[tuple[Any, Any, float]] = []
        for u, nbrs in self._adj.items():
            for v, w in nbrs.items():
                key = (u, v) if self.directed else tuple(sorted((u, v), key=str))
                if key in seen:
                    continue
                seen.add(key)
                out.append((u, v, w))
        return out

    def degree(self, node: Any) -> int:
        return len(self._adj.get(node, {}))

    def bfs(self, start: Any) -> list[Any]:
        if start not in self._adj:
            return []
        visited = {start}
        order: list[Any] = []
        q = _py_deque([start])
        while q:
            node = q.popleft()
            order.append(node)
            for nxt in sorted(self._adj[node], key=str):
                if nxt not in visited:
                    visited.add(nxt)
                    q.append(nxt)
        return order

    def dfs(self, start: Any) -> list[Any]:
        if start not in self._adj:
            return []
        visited: set[Any] = set()
        order: list[Any] = []

        def walk(node: Any) -> None:
            visited.add(node)
            order.append(node)
            for nxt in sorted(self._adj[node], key=str):
                if nxt not in visited:
                    walk(nxt)

        walk(start)
        return order

    def dijkstra(self, start: Any, target: Any | None = None) -> tuple[dict[Any, float], dict[Any, Any | None]]:
        """返回 (距离表, 前驱表)。距离为 inf 表示不可达。"""
        if start not in self._adj:
            return {}, {}
        dist: dict[Any, float] = {node: math.inf for node in self._adj}
        prev: dict[Any, Any | None] = {node: None for node in self._adj}
        dist[start] = 0.0
        heap: list[tuple[float, int, Any]] = [(0.0, 0, start)]
        seq = 0
        settled: set[Any] = set()
        while heap:
            d, _, node = heapq.heappop(heap)
            if node in settled:
                continue
            settled.add(node)
            if target is not None and node == target:
                break
            for nxt, weight in self._adj[node].items():
                nd = d + weight
                if nd < dist.get(nxt, math.inf):
                    dist[nxt] = nd
                    prev[nxt] = node
                    seq += 1
                    heapq.heappush(heap, (nd, seq, nxt))
        return dist, prev

    def shortest_path(self, start: Any, target: Any) -> tuple[list[Any], float]:
        dist, prev = self.dijkstra(start, target)
        if target not in dist or math.isinf(dist[target]):
            return [], math.inf
        path: list[Any] = []
        cur: Any | None = target
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
        return path, dist[target]

    def components(self) -> list[list[Any]]:
        seen: set[Any] = set()
        groups: list[list[Any]] = []
        for start in self._adj:
            if start in seen:
                continue
            comp = self.bfs(start)
            seen.update(comp)
            groups.append(comp)
        return groups


# ---------------------------------------------------------------------------
# 11. 并查集
# ---------------------------------------------------------------------------
class UnionFind:
    """路径压缩 + 按大小合并；均摊 O(α(n))，近似 O(1)。"""

    def __init__(self) -> None:
        self.parent: dict[Any, Any] = {}
        self.size: dict[Any, int] = {}
        self._groups = 0

    def __len__(self) -> int:
        return len(self.parent)

    def add(self, item: Any) -> None:
        if item not in self.parent:
            self.parent[item] = item
            self.size[item] = 1
            self._groups += 1

    def find(self, item: Any) -> Any:
        self.add(item)
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        # 路径压缩
        while self.parent[item] != item:
            nxt = self.parent[item]
            self.parent[item] = root
            item = nxt
        return root

    def union(self, a: Any, b: Any) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self._groups -= 1
        return True

    def connected(self, a: Any, b: Any) -> bool:
        return self.find(a) == self.find(b)

    @property
    def group_count(self) -> int:
        return self._groups

    def groups(self) -> dict[Any, list[Any]]:
        out: dict[Any, list[Any]] = {}
        for item in list(self.parent):
            root = self.find(item)
            out.setdefault(root, []).append(item)
        return out

    def group_of(self, item: Any) -> list[Any]:
        root = self.find(item)
        return [x for x in self.parent if self.find(x) == root]


# ---------------------------------------------------------------------------
# 演示数据的小工具
# ---------------------------------------------------------------------------
def fmt_money(value: float) -> str:
    return f"¥{value:,.2f}"


def human_duration(minutes: float) -> str:
    minutes = int(round(minutes))
    if minutes < 60:
        return f"{minutes} 分钟"
    hours, mins = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} 小时 {mins} 分"
    days, hours = divmod(hours, 24)
    return f"{days} 天 {hours} 小时"


__all__ = [
    "DynamicArray",
    "LinkedList",
    "Stack",
    "Queue",
    "Deque",
    "HashTable",
    "MinHeap",
    "BST",
    "Trie",
    "Graph",
    "UnionFind",
    "set_lang",
    "fmt_money",
    "human_duration",
]
