"""End-to-end prediction pipeline orchestration."""

from __future__ import annotations

from uuid import UUID, uuid4

from code_impact.domain.entities import GraphSnapshot, Prediction, PredictionExplanation
from code_impact.domain.exceptions import EntityNotFoundError
from code_impact.domain.repositories import IGraphRepository, IPredictionRepository
from code_impact.domain.services import (
    DiffAnalysisResult,
    IEmbeddingService,
    IGNNPredictor,
    IHistoricalSearch,
    IReviewerRecommender,
)
from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService
from code_impact.ml.risk.classical_risk_classifier import ClassicalRiskClassifier
from code_impact.ml.risk.ensemble_fusion import EnsembleFusionService


class PredictionPipelineService:
    """Runs GNN + classical ML + historical search + reviewer recommendation."""

    def __init__(
        self,
        prediction_repo: IPredictionRepository,
        graph_repo: IGraphRepository,
        diff_service: DiffAnalysisService,
        gnn_predictor: IGNNPredictor,
        historical_search: IHistoricalSearch,
        reviewer_recommender: IReviewerRecommender,
        embedding_service: IEmbeddingService,
        classical_classifier: ClassicalRiskClassifier | None = None,
        ensemble: EnsembleFusionService | None = None,
    ) -> None:
        self._predictions = prediction_repo
        self._graphs = graph_repo
        self._diff_service = diff_service
        self._gnn = gnn_predictor
        self._search = historical_search
        self._reviewers = reviewer_recommender
        self._embeddings = embedding_service
        self._classical = classical_classifier or ClassicalRiskClassifier()
        self._ensemble = ensemble or EnsembleFusionService()

    async def run(self, prediction_id: UUID) -> Prediction:
        prediction = await self._predictions.get_by_id(prediction_id)
        if not prediction:
            raise EntityNotFoundError("Prediction", prediction_id)

        prediction.mark_processing()
        await self._predictions.update(prediction)

        try:
            diff_text = str(prediction.input_payload.get("diff", ""))
            enriched = await self._diff_service.analyze(diff_text)
            diff_result = self._to_diff_result(enriched)

            graph = await self._graphs.get_latest_snapshot(prediction.repository_id)
            if graph is None:
                graph = self._empty_graph(prediction.repository_id)

            hist_embedding = await self._embeddings.embed_text(diff_text[:4000])
            similar_commits = await self._search.find_similar_commits(
                prediction.repository_id,
                hist_embedding,
                top_k=10,
            )
            similar_bugs = await self._search.find_similar_bugs(
                prediction.repository_id,
                hist_embedding,
                top_k=5,
            )

            gnn_result = await self._gnn.predict(graph, diff_result, hist_embedding)
            classical_result = self._classical.predict(diff_result, similar_commits)
            fused = self._ensemble.fuse(gnn_result, classical_result, similar_commits)
            reviewers = await self._reviewers.recommend(
                prediction.repository_id,
                fused.affected_files,
            )

            explanation = PredictionExplanation(
                root_cause="Automated pre-LLM summary — full narrative in Step 7",
                risk_explanation=(
                    f"Ensemble risk {fused.risk_score.value:.1f}/100 "
                    f"(GNN={gnn_result.risk_score.value:.1f}, "
                    f"classical={classical_result.risk_score.value:.1f})"
                ),
                affected_files_explanation=(
                    f"{len(fused.affected_files)} files ranked by break probability"
                ),
                reviewer_explanation=(
                    f"{len(reviewers)} reviewers matched by ownership/expertise"
                    if reviewers
                    else "No reviewer profiles configured"
                ),
                attention_summary={
                    "fusion_weights": fused.fusion_weights,
                    "component_scores": fused.component_scores,
                    "similar_bug_count": len(similar_bugs),
                },
            )

            prediction.mark_completed(
                risk_score=fused.risk_score,
                regression_probability=fused.regression_probability,
                confidence_score=fused.confidence_score,
                affected_files=fused.affected_files,
                similar_commits=similar_commits,
                suggested_reviewers=reviewers,
                explanation=explanation,
                output_payload={
                    "fusion_weights": fused.fusion_weights,
                    "component_scores": fused.component_scores,
                    "similar_bugs": similar_bugs,
                    "gnn_node_importance": gnn_result.node_importance,
                },
            )
        except Exception as exc:
            prediction.mark_failed(str(exc))

        return await self._predictions.update(prediction)

    @staticmethod
    def _to_diff_result(enriched) -> DiffAnalysisResult:
        return DiffAnalysisResult(
            changed_files=enriched.changed_files,
            added_lines=enriched.added_lines,
            deleted_lines=enriched.deleted_lines,
            modified_functions=enriched.modified_functions,
            renamed_files=enriched.renamed_files,
            complexity_delta=enriched.complexity_delta,
            deleted_code_ratio=enriched.deleted_code_ratio,
            raw_diff=enriched.raw_diff,
        )

    @staticmethod
    def _empty_graph(repository_id: UUID) -> GraphSnapshot:
        return GraphSnapshot(
            id=uuid4(),
            repository_id=repository_id,
            commit_sha="unknown",
            node_count=0,
            edge_count=0,
            storage_path="",
        )
