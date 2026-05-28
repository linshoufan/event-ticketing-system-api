"""簡單的 in-memory TTL cache。

用途：跨服務呼叫（Account / Event）的短期結果快取，避免單一 request 內
重複打對方 API。設計上是 best-effort：
- 不是 thread-safe（FastAPI 在單一 worker 內是 async，沒有 thread race）
- 不會主動清理過期 entry（每次 get 才檢查 + 偶爾 prune）
- pod 重啟就清空

之後流量起來會換成 Redis（直接替換這個檔案的介面即可）。
"""
import time
from threading import Lock
from typing import Any, Callable


class TTLCache:
    def __init__(self, default_ttl: float = 30.0, max_size: int = 1000):
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < time.time():
                # 過期 → 刪掉並回傳 None
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        with self._lock:
            if len(self._store) >= self._max_size:
                # 簡易 prune：清掉已過期的；若全部都沒過期，清掉最舊的一筆
                now = time.time()
                expired = [k for k, (exp, _) in self._store.items() if exp < now]
                if expired:
                    for k in expired:
                        self._store.pop(k, None)
                else:
                    oldest = min(self._store, key=lambda k: self._store[k][0])
                    self._store.pop(oldest, None)
            self._store[key] = (time.time() + (ttl or self._default_ttl), value)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def get_or_set(self, key: str, loader: Callable[[], Any], ttl: float | None = None) -> Any:
        """常用 pattern：有就回傳，沒有就跑 loader 取得後存進去。"""
        cached = self.get(key)
        if cached is not None:
            return cached
        value = loader()
        self.set(key, value, ttl=ttl)
        return value