import time
from typing import Dict, List
from collections import defaultdict
from dataclasses import dataclass, field

@dataclass
class Metric:
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class MetricsCollector:
    def __init__(self):
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._timings: Dict[str, List[float]] = defaultdict(list)

    def counter_inc(self, name: str, value: int = 1):
        self._counters[name] += value

    def counter_get(self, name: str) -> int:
        return self._counters.get(name, 0)

    def gauge_set(self, name: str, value: float):
        self._gauges[name] = value

    def gauge_get(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    def histogram_observe(self, name: str, value: float):
        self._histograms[name].append(value)
        if len(self._histograms[name]) > 1000:
            self._histograms[name] = self._histograms[name][-1000:]

    def timing(self, name: str, duration_ms: float):
        self._timings[name].append(duration_ms)
        if len(self._timings[name]) > 1000:
            self._timings[name] = self._timings[name][-1000:]

    def get_metrics(self) -> Dict:
        result = {}
        for name, val in self._counters.items():
            result[f"counter_{name}"] = val
        for name, val in self._gauges.items():
            result[f"gauge_{name}"] = val
        for name, vals in self._histograms.items():
            if vals:
                result[f"histogram_{name}_count"] = len(vals)
                result[f"histogram_{name}_sum"] = sum(vals)
                result[f"histogram_{name}_avg"] = sum(vals) / len(vals)
        for name, vals in self._timings.items():
            if vals:
                result[f"timing_{name}_avg_ms"] = sum(vals) / len(vals)
                result[f"timing_{name}_p95_ms"] = sorted(vals)[int(len(vals) * 0.95)]
        return result

    def reset(self):
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._timings.clear()

metrics = MetricsCollector()