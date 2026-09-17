from dataclasses import dataclass


@dataclass(frozen=True)
class TargetRule:
    ticker: str
    target_weight: float
    calc_mode: str
    threshold: float

    @property
    def min_weight(self) -> float:
        if self.calc_mode == "RELATIVE":
            delta = self.target_weight * (self.threshold / 100.0)
            return self.target_weight - delta
        return self.target_weight - self.threshold

    @property
    def max_weight(self) -> float:
        if self.calc_mode == "RELATIVE":
            delta = self.target_weight * (self.threshold / 100.0)
            return self.target_weight + delta
        return self.target_weight + self.threshold


@dataclass(frozen=True)
class Alert:
    ticker: str
    actual_weight: float
    target_weight: float
    min_weight: float
    max_weight: float
    mode_str: str
    current_price: float

    @property
    def direction(self) -> str:
        return "🔺" if self.actual_weight > self.max_weight else "🔻"
