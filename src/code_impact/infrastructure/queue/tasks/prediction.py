"""Prediction pipeline Celery tasks — implemented in Steps 5-8."""

from code_impact.infrastructure.queue.celery_app import celery_app


@celery_app.task(name="prediction.run_pipeline", bind=True, max_retries=2)
def run_prediction_pipeline_task(self, prediction_id: str) -> dict:
    """
    Full prediction pipeline:
    1. Parse diff
    2. Update graph
    3. GNN inference
    4. Historical search
    5. Reviewer recommendation
    6. LLM explanation
    """
    return {"status": "queued", "prediction_id": prediction_id}
