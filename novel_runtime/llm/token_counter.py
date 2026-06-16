from __future__ import annotations


class TokenCounter:
    def __init__(self):
        try:
            import tiktoken
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        if self.encoding:
            return len(self.encoding.encode(text))
        return len(text) // 4

    def count_messages_tokens(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += 4
            for key, value in msg.items():
                total += self.count_tokens(str(value))
                if key == "name":
                    total += -1
        total += 2
        return total


class TokenBudgetManager:
    def __init__(
        self,
        total_budget: int = 8000,
        allocation: dict | None = None,
        priority_order: list[str] | None = None,
    ):
        self.total_budget = total_budget
        self.allocation = allocation or {}
        self.priority_order = priority_order or []
        self.counter = TokenCounter()

    def allocate(self, sections: dict[str, str]) -> dict[str, str]:
        result = {}
        total_tokens = 0
        token_counts = {}

        for name, content in sections.items():
            tokens = self.counter.count_tokens(content)
            token_counts[name] = tokens
            total_tokens += tokens

        if total_tokens <= self.total_budget:
            return dict(sections)

        priority_order = list(self.priority_order)
        for name in sections:
            if name not in priority_order:
                priority_order.append(name)

        for name in reversed(priority_order):
            if total_tokens <= self.total_budget:
                continue

            content = sections[name]
            if name not in result:
                budget = int(self.allocation.get(name, 500) * 0.8)
                current_tokens = token_counts[name]

                if current_tokens <= budget or current_tokens <= 20:
                    result[name] = content
                    total_tokens -= current_tokens
                else:
                    truncated = self._truncate_to_budget(content, max(50, budget))
                    truncated_tokens = self.counter.count_tokens(truncated)
                    result[name] = truncated
                    total_tokens -= current_tokens - truncated_tokens

        for name in sections:
            if name not in result:
                result[name] = self._truncate_to_budget(sections[name], 50)

        return result

    def _truncate_to_budget(self, text: str, max_tokens: int) -> str:
        tokens = self.counter.count_tokens(text)
        if tokens <= max_tokens:
            return text
        for sep in ["\n", "。", ".", "!", "？", "！"]:
            parts = text.rsplit(sep, 1)
            if len(parts) > 1 and self.counter.count_tokens(parts[0]) <= max_tokens:
                return parts[0] + "..." + "(已截断，预算不足)"
        return text[:max_tokens * 4] + "..." + "(已截断，预算不足)"

    def summarize_section(self, content: str, level: str) -> str:
        if level == "full" or not content:
            return content
        lines = content.split("\n")
        if level == "reduced":
            if len(lines) <= 2:
                return content
            result = [lines[0]]
            for i in range(1, len(lines) - 1):
                line = lines[i].strip()
                if line and len(line) > 20:
                    if "。" in line:
                        parts = line.split("。")
                        result.append(parts[0] + "。")
                    elif "." in line:
                        parts = line.split(".")
                        result.append(parts[0] + ".")
                    else:
                        result.append(line[:30] + "...")
                else:
                    result.append(line)
            result.append(lines[-1])
            return "\n".join(result)
        if level == "minimal":
            kept = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                if any(c in line for c in ["#", ":", "目标", "位置", "当前", "名称"]):
                    kept.append(line[:80])
            return "\n".join(kept[:10])
        return content

    def get_budget_summary(self, sections: dict[str, str]) -> dict:
        summary = {}
        for name, content in sections.items():
            tokens = self.counter.count_tokens(content)
            budget = self.allocation.get(name, 500)
            summary[name] = {
                "tokens": tokens,
                "budget": budget,
                "percentage": round((tokens / budget) * 100, 1) if budget else 0,
                "truncated": tokens > budget,
            }
        return summary
