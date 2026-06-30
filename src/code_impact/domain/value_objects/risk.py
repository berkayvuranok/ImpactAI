"""Risk-related value objects with validation."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RiskScore:
    """Risk score on a 0-100 scale."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 100.0:
            msg = f"Risk score must be in [0, 100], got {self.value}"
            raise ValueError(msg)

    @property
    def level(self) -> str:
        if self.value < 25:
            return "low"
        if self.value < 50:
            return "medium"
        if self.value < 75:
            return "high"
        return "critical"


@dataclass(frozen=True, slots=True)
class RegressionProbability:
    """Probability of regression in [0, 1]."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            msg = f"Regression probability must be in [0, 1], got {self.value}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    """Model confidence in [0, 1]."""

    value: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            msg = f"Confidence must be in [0, 1], got {self.value}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class AffectedFilePrediction:
    """Prediction for a single affected file."""

    file_path: str
    break_probability: float
    node_importance: float
    rank: int
    explanation: str | None = None

    def __post_init__(self) -> None:
        if not 0.0 <= self.break_probability <= 1.0:
            msg = f"Break probability must be in [0, 1], got {self.break_probability}"
            raise ValueError(msg)
        if self.rank < 1:
            msg = f"Rank must be >= 1, got {self.rank}"
            raise ValueError(msg)
