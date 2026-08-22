"""Runtime execution metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeMetrics:
    """Track basic runtime execution metrics."""

    executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    cancelled_executions: int = 0
    total_tokens: int = 0

    def record_success(self) -> None:
        """Record a successful execution."""

        self.executions += 1
        self.successful_executions += 1

    def record_failure(self) -> None:
        """Record a failed execution."""

        self.executions += 1
        self.failed_executions += 1

    def record_cancellation(self) -> None:
        """Record a cancelled execution."""

        self.executions += 1
        self.cancelled_executions += 1

    def record_tokens(self, count: int) -> None:
        """Add consumed tokens to the total."""

        if count < 0:
            raise ValueError(
                "Token count cannot be negative."
            )

        self.total_tokens += count

    def reset(self) -> None:
        """Reset all metrics."""

        self.executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.cancelled_executions = 0
        self.total_tokens = 0