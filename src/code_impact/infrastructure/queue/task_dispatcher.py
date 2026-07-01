"""Task dispatch abstraction — Celery in production, sync/mock in tests."""

from typing import Protocol


class ITaskDispatcher(Protocol):
    def dispatch_sync_repository(
        self,
        repository_id: str,
        job_id: str,
        full_sync: bool,
        since_sha: str | None,
    ) -> None: ...

    def dispatch_build_graph(
        self,
        repository_id: str,
        commit_sha: str,
    ) -> None: ...

    def dispatch_index_embeddings(
        self,
        repository_id: str,
        reindex: bool = False,
        include_issues: bool = True,
    ) -> None: ...

    def dispatch_run_prediction(self, prediction_id: str) -> None: ...


class CeleryTaskDispatcher:
    def dispatch_sync_repository(
        self,
        repository_id: str,
        job_id: str,
        full_sync: bool,
        since_sha: str | None,
    ) -> None:
        from code_impact.infrastructure.queue.tasks.analysis import sync_repository_task

        sync_repository_task.delay(repository_id, job_id, full_sync, since_sha)

    def dispatch_build_graph(self, repository_id: str, commit_sha: str) -> None:
        from code_impact.infrastructure.queue.tasks.analysis import build_graph_task

        build_graph_task.delay(repository_id, commit_sha)

    def dispatch_index_embeddings(
        self,
        repository_id: str,
        reindex: bool = False,
        include_issues: bool = True,
    ) -> None:
        from code_impact.infrastructure.queue.tasks.embedding import index_embeddings_task

        index_embeddings_task.delay(repository_id, reindex, include_issues)

    def dispatch_run_prediction(self, prediction_id: str) -> None:
        from code_impact.infrastructure.queue.tasks.prediction import run_prediction_pipeline_task

        run_prediction_pipeline_task.delay(prediction_id)


class InlineTaskDispatcher:
    """Runs tasks inline — useful for tests and local dev without Celery."""

    def dispatch_sync_repository(
        self,
        repository_id: str,
        job_id: str,
        full_sync: bool,
        since_sha: str | None,
    ) -> None:
        from code_impact.infrastructure.queue.tasks.analysis import sync_repository_task

        sync_repository_task.apply(args=[repository_id, job_id, full_sync, since_sha])

    def dispatch_build_graph(self, repository_id: str, commit_sha: str) -> None:
        from code_impact.infrastructure.queue.tasks.analysis import build_graph_task

        build_graph_task.apply(args=[repository_id, commit_sha])

    def dispatch_index_embeddings(
        self,
        repository_id: str,
        reindex: bool = False,
        include_issues: bool = True,
    ) -> None:
        from code_impact.infrastructure.queue.tasks.embedding import index_embeddings_task

        index_embeddings_task.apply(args=[repository_id, reindex, include_issues])

    def dispatch_run_prediction(self, prediction_id: str) -> None:
        from code_impact.infrastructure.queue.tasks.prediction import run_prediction_pipeline_task

        run_prediction_pipeline_task.apply(args=[prediction_id])
