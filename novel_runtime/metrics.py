from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.responses import Response

llm_calls_total = Counter(
    "nwr_llm_calls_total", "Total LLM calls",
    ["agent", "status"],
)

llm_tokens_total = Counter(
    "nwr_llm_tokens_total", "Total LLM tokens used",
    ["agent", "type"],
)

llm_latency_seconds = Histogram(
    "nwr_llm_latency_seconds", "LLM call latency in seconds",
    ["agent"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

task_duration_seconds = Histogram(
    "nwr_task_duration_seconds", "Task execution duration in seconds",
    ["task_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, float("inf")),
)

chapter_status_count = Gauge(
    "nwr_chapter_status_count", "Chapter count by status",
    ["project", "status"],
)


def metrics_endpoint(request):
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)
