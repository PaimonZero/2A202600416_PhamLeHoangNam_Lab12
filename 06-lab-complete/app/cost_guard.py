"""
Cost Guard Module

Tracks LLM API usage costs and enforces daily budget limits.
Default: $5 USD daily budget per user
Pricing: GPT-4o-mini ($0.00015/1K input, $0.0006/1K output)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, Optional
from enum import Enum

from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CostStatus(str, Enum):
    """Cost check status."""
    OK = "ok"
    WARNING = "warning"  # >= 80% of budget
    EXCEEDED = "exceeded"  # > 100% of budget


@dataclass
class UsageRecord:
    """Daily usage record for a user."""
    user_id: str
    day: date
    input_tokens: int = 0
    output_tokens: int = 0
    
    # Pricing in USD
    INPUT_PRICE_PER_1K = 0.00015
    OUTPUT_PRICE_PER_1K = 0.0006
    
    @property
    def total_cost_usd(self) -> float:
        """Calculate total cost for this record."""
        input_cost = (self.input_tokens / 1000) * self.INPUT_PRICE_PER_1K
        output_cost = (self.output_tokens / 1000) * self.OUTPUT_PRICE_PER_1K
        return round(input_cost + output_cost, 6)
    
    def __str__(self) -> str:
        return f"Usage({self.user_id}, {self.day}): {self.input_tokens} in + {self.output_tokens} out = ${self.total_cost_usd}"


class CostGuard:
    """
    Tracks usage costs and enforces daily budget.
    """
    
    def __init__(self, daily_budget_usd: float = 5.0, warn_at_pct: float = 0.8):
        """
        Initialize cost guard.
        
        Args:
            daily_budget_usd: Daily budget per user in USD
            warn_at_pct: Warning threshold as percentage (0.8 = 80%)
        """
        self.daily_budget = daily_budget_usd
        self.warn_threshold = warn_at_pct
        
        # Store usage by user_id -> UsageRecord
        self.usage: Dict[str, UsageRecord] = {}
    
    def check_and_record(
        self,
        user_id: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, any]:
        """
        Check if usage is within budget and record if allowed.
        
        Args:
            user_id: User identifier
            input_tokens: Input tokens for this request
            output_tokens: Output tokens for this request
        
        Returns:
            dict: Status info with cost, remaining, threshold
        
        Raises:
            HTTPException: 402 Payment Required if budget exceeded
        """
        today = date.today()
        key = f"{user_id}:{today}"
        
        # Get or create today's record
        if key not in self.usage:
            self.usage[key] = UsageRecord(user_id=user_id, day=today)
        
        record = self.usage[key]
        
        # Calculate new total if we add this request
        new_record = UsageRecord(
            user_id=user_id,
            day=today,
            input_tokens=record.input_tokens + input_tokens,
            output_tokens=record.output_tokens + output_tokens
        )
        new_cost = new_record.total_cost_usd
        
        # Check budget
        if new_cost > self.daily_budget:
            remaining = max(0, self.daily_budget - record.total_cost_usd)
            logger.warning(
                f"Budget exceeded for {user_id}: "
                f"${new_cost:.4f} > ${self.daily_budget} "
                f"(remaining: ${remaining:.4f})"
            )
            raise HTTPException(
                status_code=402,
                detail=f"Daily budget exceeded. ${remaining:.4f} remaining. Reset tomorrow."
            )
        
        # Record the usage
        record.input_tokens += input_tokens
        record.output_tokens += output_tokens
        
        # Determine status
        cost_pct = new_cost / self.daily_budget if self.daily_budget > 0 else 0
        if cost_pct >= 1.0:
            status = CostStatus.EXCEEDED
        elif cost_pct >= self.warn_threshold:
            status = CostStatus.WARNING
        else:
            status = CostStatus.OK
        
        remaining = self.daily_budget - new_cost
        
        logger.debug(
            f"Cost recorded for {user_id}: "
            f"${new_cost:.4f}/${self.daily_budget} "
            f"({int(cost_pct*100)}%) - Status: {status}"
        )
        
        return {
            "status": status,
            "cost_usd": round(new_cost, 6),
            "daily_budget_usd": self.daily_budget,
            "remaining_usd": round(remaining, 6),
            "usage_pct": round(cost_pct * 100, 2),
            "tokens": {
                "input": record.input_tokens,
                "output": record.output_tokens
            }
        }
    
    def get_usage(self, user_id: str, target_date: Optional[date] = None) -> Optional[UsageRecord]:
        """
        Get usage record for user on specific date.
        
        Args:
            user_id: User identifier
            target_date: Date to check (default today)
        
        Returns:
            UsageRecord or None if not found
        """
        target_date = target_date or date.today()
        key = f"{user_id}:{target_date}"
        return self.usage.get(key)
    
    def reset_user_today(self, user_id: str) -> None:
        """
        Reset usage for user today (admin operation).
        
        Args:
            user_id: User identifier
        """
        today = date.today()
        key = f"{user_id}:{today}"
        if key in self.usage:
            del self.usage[key]
            logger.info(f"Usage reset for {user_id} on {today}")


# Global instance
_cost_guard: CostGuard = None


def get_cost_guard(daily_budget_usd: float = 5.0) -> CostGuard:
    """
    Get or initialize global cost guard instance.
    
    Args:
        daily_budget_usd: Daily budget per user
    
    Returns:
        CostGuard: Global instance
    """
    global _cost_guard
    if _cost_guard is None:
        _cost_guard = CostGuard(daily_budget_usd)
    return _cost_guard
