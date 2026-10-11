"""
NPT Fleet: Real-Time Financial Governor & Token Telemetry (ADR-018)
Tracks cumulative input/output tokens and estimated USD expenditure across agent turns,
and enforces hard circuit breakers against user-declared spending caps.
"""

import re
from typing import Optional, Dict, Any, List


class SpendingCapExceededException(Exception):
    """Raised when cumulative token expenditure reaches or exceeds the declared spending cap."""
    pass


# Google GenAI Pricing Matrix (USD per 1,000,000 tokens)
MODEL_PRICING = {
    "gemini-3.8-flash": {"prompt": 0.075, "candidate": 0.30, "cached": 0.01875},
    "gemini-2.5-flash": {"prompt": 0.075, "candidate": 0.30, "cached": 0.01875},
    "gemini-1.5-flash": {"prompt": 0.075, "candidate": 0.30, "cached": 0.01875},
    "gemini-3.5-flash": {"prompt": 0.075, "candidate": 0.30, "cached": 0.01875},
    "gemini-1.5-pro": {"prompt": 1.25, "candidate": 5.00, "cached": 0.3125},
    "gemini-2.5-pro": {"prompt": 1.25, "candidate": 5.00, "cached": 0.3125},
}
DEFAULT_PRICING = {"prompt": 0.075, "candidate": 0.30, "cached": 0.01875}


class CostTracker:
    """
    Session-level and run-level token accumulator and financial governor.
    """

    def __init__(self, spending_cap_usd: Optional[float] = None):
        self.spending_cap_usd: Optional[float] = spending_cap_usd
        self.total_prompt_tokens: int = 0
        self.total_candidate_tokens: int = 0
        self.total_cached_tokens: int = 0
        self.total_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.turns_recorded: int = 0

    @staticmethod
    def parse_spending_cap(text: str) -> Optional[float]:
        """
        Extracts spending cap dollar amounts from user prompts or CLI arguments.
        Matches patterns like:
          'spending cap of $0.50'
          'spending cap of 0.50'
          '--spending-cap 0.50'
          '$0.50 spending cap'
        """
        if not text:
            return None
        patterns = [
            r"spending\s+cap\s+(?:of\s+)?\$?(\d*\.?\d+)",
            r"--spending-cap(?:=|\s+)\$?(\d*\.?\d+)",
            r"\$?(\d*\.?\d+)\s+spending\s+cap",
            r"budget\s+(?:of\s+)?\$?(\d*\.?\d+)",
            r"cap\s+(?:of\s+)?\$?(\d*\.?\d+)"
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    pass
        return None

    def record_turn_usage(self, usage_metadata: Any, model_name: str) -> Dict[str, Any]:
        """
        Extracts token counts from Gemini response usage_metadata and calculates USD cost.
        """
        prompt_tokens = getattr(usage_metadata, "prompt_token_count", 0) or 0
        candidate_tokens = getattr(usage_metadata, "candidates_token_count", 0) or 0
        cached_tokens = getattr(usage_metadata, "cached_content_token_count", 0) or 0
        total_turn_tokens = getattr(usage_metadata, "total_token_count", 0) or (prompt_tokens + candidate_tokens)

        # Lookup model pricing rates
        normalized_model = model_name.lower().strip()
        rates = DEFAULT_PRICING
        for m_key, m_rates in MODEL_PRICING.items():
            if m_key in normalized_model:
                rates = m_rates
                break

        # Calculate cost: uncached prompt + cached prompt + candidates
        uncached_prompt = max(0, prompt_tokens - cached_tokens)
        turn_cost = (
            (uncached_prompt / 1_000_000.0) * rates["prompt"]
            + (cached_tokens / 1_000_000.0) * rates["cached"]
            + (candidate_tokens / 1_000_000.0) * rates["candidate"]
        )

        self.total_prompt_tokens += prompt_tokens
        self.total_candidate_tokens += candidate_tokens
        self.total_cached_tokens += cached_tokens
        self.total_tokens += total_turn_tokens
        self.total_cost_usd += turn_cost
        self.turns_recorded += 1

        summary = {
            "turn_prompt_tokens": prompt_tokens,
            "turn_candidate_tokens": candidate_tokens,
            "turn_cached_tokens": cached_tokens,
            "turn_total_tokens": total_turn_tokens,
            "turn_cost_usd": turn_cost,
            "cumulative_tokens": self.total_tokens,
            "cumulative_cost_usd": self.total_cost_usd,
            "spending_cap_usd": self.spending_cap_usd,
            "turns_recorded": self.turns_recorded
        }

        # Check circuit breaker
        if self.spending_cap_usd is not None and self.total_cost_usd >= self.spending_cap_usd:
            raise SpendingCapExceededException(
                f"[FINANCIAL CIRCUIT BREAKER TRIPPED] Cumulative spend (${self.total_cost_usd:.4f}) "
                f"reached or exceeded the declared spending cap (${self.spending_cap_usd:.2f}) "
                f"after {self.turns_recorded} turns ({self.total_tokens:,} total tokens). Workflow halted."
            )

        return summary

    def get_telemetry_string(self, turn_summary: Dict[str, Any]) -> str:
        """Formats a single-line telemetry string for console output."""
        cap_str = f" / Cap: ${self.spending_cap_usd:.2f}" if self.spending_cap_usd else ""
        cached_str = f" (Cached: {turn_summary['turn_cached_tokens']:,})" if turn_summary['turn_cached_tokens'] > 0 else ""
        return (
            f"  -> [TOKEN TELEMETRY] Turn: {turn_summary['turn_total_tokens']:,} tokens "
            f"(In: {turn_summary['turn_prompt_tokens']:,}{cached_str}, Out: {turn_summary['turn_candidate_tokens']:,}) | "
            f"Turn Cost: ${turn_summary['turn_cost_usd']:.4f} | "
            f"Run Total: ${self.total_cost_usd:.4f}{cap_str}"
        )
