"""Context Window Budget  Token tracking with tiered model selection.

Implements cost discipline:
- Tier 1 (Bulk): gemini-flash, mistral  cheap, fast
- Tier 2 (Synthesis): claude-3-sonnet, gpt-4-turbo  expensive, accurate
"""
from typing import Optional, Dict, List
from datetime import datetime
import json


# Model pricing (per 1M tokens, approximate USD)
MODEL_PRICING = {
    # Tier 1: Bulk/Cheap
    "gemini-flash": {"input": 0.075, "output": 0.30, "tier": "bulk"},
    "mistral-small": {"input": 0.15, "output": 0.20, "tier": "bulk"},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50, "tier": "bulk"},
    # Tier 2: Synthesis/Expensive
    "claude-3-sonnet": {"input": 3.00, "output": 15.00, "tier": "synthesis"},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00, "tier": "synthesis"},
    "claude-3-opus": {"input": 15.00, "output": 75.00, "tier": "synthesis"},
}


class ContextWindowBudget:
    """Track token usage and enforce cost discipline."""
    
    def __init__(self, max_budget_usd: float = 10.00, max_tokens: int = 500000, warning_threshold: float = 0.5):
        self.max_budget_usd = max_budget_usd
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.tokens_used = 0
        self.tokens_input = 0
        self.tokens_output = 0
        self.cost_usd = 0.0
        self.request_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.model_usage: Dict[str, dict] = {}
        self.request_log: List[dict] = []
    
    def select_model(self, task_type: str) -> str:
        """Select model based on task type (cost discipline)."""
        if task_type == "bulk":
            return "gemini-flash"
        elif task_type == "synthesis":
            return "claude-3-sonnet"
        return "gemini-flash"
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count: 1 token  4 characters."""
        return len(text) // 4
    
    def can_spend(self, input_tokens: int, output_tokens: int, model: str) -> bool:
        """Check if we can afford this LLM call."""
        total_tokens = input_tokens + output_tokens
        if (self.tokens_used + total_tokens) > self.max_tokens:
            return False
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-flash"])
        cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        if (self.cost_usd + cost) > self.max_budget_usd:
            return False
        return True
    
    def spend(self, input_tokens: int, output_tokens: int, model: str, task_type: str = "bulk") -> None:
        """Record token usage and cost."""
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["gemini-flash"])
        cost = (input_tokens / 1_000_000 * pricing["input"]) + (output_tokens / 1_000_000 * pricing["output"])
        self.tokens_input += input_tokens
        self.tokens_output += output_tokens
        self.tokens_used += input_tokens + output_tokens
        self.cost_usd += cost
        self.request_count += 1
        if model not in self.model_usage:
            self.model_usage[model] = {"tokens": 0, "cost": 0.0, "requests": 0}
        self.model_usage[model]["tokens"] += input_tokens + output_tokens
        self.model_usage[model]["cost"] += cost
        self.model_usage[model]["requests"] += 1
        self.request_log.append({"timestamp": datetime.now().isoformat(), "model": model, "task_type": task_type, "input_tokens": input_tokens, "output_tokens": output_tokens, "cost_usd": round(cost, 4)})
        if self.tokens_used > (self.max_tokens * self.warning_threshold):
            print(f" Token budget warning: {self.tokens_used}/{self.max_tokens} ({round((self.tokens_used/self.max_tokens)*100, 1)}%)")
        if self.cost_usd > (self.max_budget_usd * self.warning_threshold):
            print(f" Cost budget warning: ${self.cost_usd:.2f}/${self.max_budget_usd:.2f}")
    
    def record_cache_hit(self) -> None:
        self.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        self.cache_misses += 1
    
    def get_stats(self) -> dict:
        return {
            "tokens": {"used": self.tokens_used, "input": self.tokens_input, "output": self.tokens_output, "max": self.max_tokens, "usage_percent": round((self.tokens_used / self.max_tokens) * 100, 2)},
            "cost": {"used_usd": round(self.cost_usd, 4), "max_usd": self.max_budget_usd, "usage_percent": round((self.cost_usd / self.max_budget_usd) * 100, 2)},
            "requests": {"total": self.request_count, "cache_hits": self.cache_hits, "cache_misses": self.cache_misses, "cache_hit_rate": round((self.cache_hits / (self.cache_hits + self.cache_misses)) * 100, 2) if (self.cache_hits + self.cache_misses) > 0 else 0},
            "by_model": self.model_usage,
        }
