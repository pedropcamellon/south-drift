import asyncio
import logging

from temporalio.client import Client
from temporalio.contrib.langgraph import LangGraphPlugin
from temporalio.worker import Worker

from app.config import settings
from app.graph import build_chartreview_graph
from app.workflow import ChartReviewWorkflow

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info(
        "Connecting chart-review worker to Temporal: address=%s namespace=%s task_queue=%s",
        settings.temporal_address,
        settings.temporal_namespace,
        settings.chartreview_task_queue,
    )
    client = await Client.connect(settings.temporal_address, namespace=settings.temporal_namespace)
    plugin = LangGraphPlugin(graphs={"chartreview": build_chartreview_graph()})
    worker = Worker(
        client,
        task_queue=settings.chartreview_task_queue,
        workflows=[ChartReviewWorkflow],
        plugins=[plugin],
    )
    logger.info("Chart-review worker is polling Temporal")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
