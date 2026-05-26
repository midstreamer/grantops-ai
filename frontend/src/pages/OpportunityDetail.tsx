import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  formatDate,
  RECOMMENDATION_OPTIONS,
  recommendationClass,
  STATUS_OPTIONS,
} from "../constants/opportunity";
import { OpportunityAISummarySection } from "../components/OpportunityAISummarySection";
import { OpportunityLiteratureTab } from "../components/OpportunityLiteratureTab";
import { OpportunityProposalDraftsTab } from "../components/OpportunityProposalDraftsTab";
import {
  deleteOpportunity,
  getOpportunity,
  scoreOpportunity,
  updateOpportunity,
} from "../services/opportunities";
import type { OpportunityAISummary } from "../types/aiSummary";
import type {
  FitScoreBreakdown,
  GrantOpportunityRead,
  OpportunityScoreResult,
  OpportunityRecommendation,
  OpportunityStatus,
} from "../types/opportunity";

type DetailTab = "overview" | "literature" | "drafts";

export function OpportunityDetailPage() {
  const params = useParams();
  const navigate = useNavigate();
  const id = useMemo(() => Number(params.id), [params.id]);

  const [activeTab, setActiveTab] = useState<DetailTab>("overview");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [scoring, setScoring] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [item, setItem] = useState<GrantOpportunityRead | null>(null);
  const [scoreData, setScoreData] = useState<OpportunityScoreResult | null>(null);

  const [status, setStatus] = useState<OpportunityStatus>("new");
  const [recommendation, setRecommendation] =
    useState<OpportunityRecommendation>("unreviewed");
  const [nextAction, setNextAction] = useState("");
  const [notes, setNotes] = useState("");
  const [aiSummary, setAiSummary] = useState<OpportunityAISummary | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getOpportunity(id);
        if (cancelled) return;
        setItem(data);
        setStatus(data.status);
        setRecommendation(data.recommendation);
        setNextAction(data.next_action ?? "");
        setNotes(data.notes ?? "");
        const fitAnalysis = data.raw_data?.fit_analysis as OpportunityScoreResult | undefined;
        setScoreData(fitAnalysis ?? null);
        const savedSummary = data.raw_data?.ai_summary as OpportunityAISummary | undefined;
        setAiSummary(savedSummary ?? null);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Unable to load opportunity");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (Number.isFinite(id)) {
      void load();
    } else {
      setLoading(false);
      setError("Invalid opportunity id");
    }
    return () => {
      cancelled = true;
    };
  }, [id]);

  const breakdown = scoreData?.breakdown as FitScoreBreakdown | undefined;

  async function onSaveWorkflow() {
    if (!item) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateOpportunity(item.id, {
        status,
        recommendation,
        next_action: nextAction.trim() ? nextAction.trim() : null,
      });
      setItem(updated);
      setStatus(updated.status);
      setRecommendation(updated.recommendation);
      setNextAction(updated.next_action ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save changes");
    } finally {
      setSaving(false);
    }
  }

  async function onSaveNotes() {
    if (!item) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateOpportunity(item.id, {
        notes: notes.trim() ? notes.trim() : null,
      });
      setItem(updated);
      setNotes(updated.notes ?? "");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save notes");
    } finally {
      setSaving(false);
    }
  }

  async function onScore() {
    if (!item) return;
    setScoring(true);
    setError(null);
    try {
      const result = await scoreOpportunity(item.id);
      setItem(result.opportunity);
      setStatus(result.opportunity.status);
      setRecommendation(result.opportunity.recommendation);
      setNextAction(result.opportunity.next_action ?? "");
      setScoreData(result.score);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to score opportunity");
    } finally {
      setScoring(false);
    }
  }

  async function onDelete() {
    if (!item) return;
    const ok = window.confirm("Delete this opportunity?");
    if (!ok) return;
    setSaving(true);
    setError(null);
    try {
      await deleteOpportunity(item.id);
      navigate("/opportunities");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to delete opportunity");
      setSaving(false);
    }
  }

  const rawDisplay = useMemo(() => {
    if (!item?.raw_data) return "{}";
    try {
      return JSON.stringify(item.raw_data, null, 2);
    } catch {
      return String(item.raw_data);
    }
  }, [item?.raw_data]);

  return (
    <main className="page page-wide">
      <div className="detail-header">
        <h1>Opportunity</h1>
        <Link className="link" to="/opportunities">
          ← Back to list
        </Link>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && item && (
        <>
          <nav className="detail-tabs">
            <button
              type="button"
              className={activeTab === "overview" ? "detail-tab active" : "detail-tab"}
              onClick={() => setActiveTab("overview")}
            >
              Overview
            </button>
            <button
              type="button"
              className={activeTab === "literature" ? "detail-tab active" : "detail-tab"}
              onClick={() => setActiveTab("literature")}
            >
              Literature
            </button>
            <button
              type="button"
              className={activeTab === "drafts" ? "detail-tab active" : "detail-tab"}
              onClick={() => setActiveTab("drafts")}
            >
              Proposal Drafts
            </button>
          </nav>

          {activeTab === "literature" ? (
            <OpportunityLiteratureTab opportunityId={item.id} />
          ) : activeTab === "drafts" ? (
            <OpportunityProposalDraftsTab opportunityId={item.id} />
          ) : (
            <>
          <section className="card">
            <div className="card-header">
              <h2>Summary</h2>
              <span className={recommendationClass(item.recommendation)}>
                {item.recommendation}
              </span>
            </div>

            <h3 className="detail-title">{item.title}</h3>
            <p className="meta">
              {item.source}
              {item.source_id ? ` · ${item.source_id}` : ""} · ID {item.id}
            </p>

            <dl className="details">
              <div>
                <dt>Agency</dt>
                <dd>{item.agency ?? "—"}</dd>
              </div>
              <div>
                <dt>Program</dt>
                <dd>{item.program ?? "—"}</dd>
              </div>
              <div>
                <dt>Deadline</dt>
                <dd>{formatDate(item.deadline)}</dd>
              </div>
              <div>
                <dt>Posted</dt>
                <dd>{formatDate(item.posted_date)}</dd>
              </div>
              <div>
                <dt>Fit score</dt>
                <dd>{item.fit_score ?? "—"}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{item.status}</dd>
              </div>
              <div>
                <dt>Opportunity status</dt>
                <dd>{item.opportunity_status ?? "—"}</dd>
              </div>
              <div>
                <dt>Award range</dt>
                <dd>
                  {item.award_floor != null || item.award_ceiling != null
                    ? `${item.award_floor ?? "?"} – ${item.award_ceiling ?? "?"}`
                    : "—"}
                </dd>
              </div>
              <div className="full">
                <dt>Description</dt>
                <dd className="prose">{item.description ?? "—"}</dd>
              </div>
              <div className="full">
                <dt>Eligibility</dt>
                <dd className="prose">{item.eligibility ?? "—"}</dd>
              </div>
              {item.url && (
                <div className="full">
                  <dt>URL</dt>
                  <dd>
                    <a className="link" href={item.url} target="_blank" rel="noreferrer">
                      {item.url}
                    </a>
                  </dd>
                </div>
              )}
              {item.fit_summary && (
                <div className="full">
                  <dt>Fit summary</dt>
                  <dd className="prose">{item.fit_summary}</dd>
                </div>
              )}
            </dl>
          </section>

          <OpportunityAISummarySection
            opportunityId={item.id}
            initialSummary={aiSummary}
          />

          <section className="card section-gap">
            <div className="card-header">
              <h2>Fit analysis</h2>
              <button
                className="button"
                type="button"
                onClick={() => void onScore()}
                disabled={scoring || saving}
              >
                {scoring ? "Scoring..." : "Score"}
              </button>
            </div>

            {!scoreData ? (
              <p className="meta">Not scored yet. Run Score to generate fit analysis.</p>
            ) : (
              <>
                <div className="fit-score-row">
                  <span className="fit-score-big">{scoreData.fit_score}</span>
                  <span className="meta">/ 100</span>
                  <span className={recommendationClass(scoreData.recommendation)}>
                    {scoreData.recommendation}
                  </span>
                </div>

                <p className="prose">{scoreData.fit_summary}</p>

                {breakdown && (
                  <dl className="details breakdown-grid">
                    <div>
                      <dt>Topic</dt>
                      <dd>
                        {breakdown.topic_alignment}/30
                      </dd>
                    </div>
                    <div>
                      <dt>Method</dt>
                      <dd>
                        {breakdown.method_alignment}/15
                      </dd>
                    </div>
                    <div>
                      <dt>Funder</dt>
                      <dd>
                        {breakdown.funder_relevance}/10
                      </dd>
                    </div>
                    <div>
                      <dt>Eligibility</dt>
                      <dd>
                        {breakdown.eligibility_fit}/15
                      </dd>
                    </div>
                    <div>
                      <dt>Deadline</dt>
                      <dd>
                        {breakdown.deadline_feasibility}/10
                      </dd>
                    </div>
                    <div>
                      <dt>Budget</dt>
                      <dd>
                        {breakdown.budget_fit}/5
                      </dd>
                    </div>
                    <div>
                      <dt>Collaboration</dt>
                      <dd>
                        {breakdown.collaboration_potential}/10
                      </dd>
                    </div>
                    <div>
                      <dt>Career value</dt>
                      <dd>
                        {breakdown.academic_career_value}/5
                      </dd>
                    </div>
                  </dl>
                )}

                <dl className="details">
                  <div className="full">
                    <dt>Matched keywords</dt>
                    <dd>
                      {scoreData.matched_keywords.length > 0
                        ? scoreData.matched_keywords.join(", ")
                        : "—"}
                    </dd>
                  </div>
                  <div className="full">
                    <dt>Concerns</dt>
                    <dd>
                      {scoreData.concerns.length > 0
                        ? scoreData.concerns.join(" · ")
                        : "None"}
                    </dd>
                  </div>
                </dl>
              </>
            )}
          </section>

          <section className="card section-gap">
            <div className="card-header">
              <h2>Raw source data</h2>
            </div>
            <pre className="json-block">{rawDisplay}</pre>
          </section>

          <section className="card section-gap">
            <div className="card-header">
              <h2>Notes</h2>
            </div>
            <label className="field full">
              <span>Private notes</span>
              <textarea
                rows={5}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Meeting notes, PI feedback, strategy..."
              />
            </label>
            <div className="form-actions">
              <button
                className="button"
                type="button"
                onClick={() => void onSaveNotes()}
                disabled={saving}
              >
                {saving ? "Saving..." : "Save notes"}
              </button>
            </div>
          </section>

          <section className="card section-gap">
            <div className="card-header">
              <h2>Next actions</h2>
            </div>

            <div className="form-grid">
              <label className="field">
                <span>Status</span>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as OpportunityStatus)}
                >
                  {STATUS_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>Recommendation</span>
                <select
                  value={recommendation}
                  onChange={(e) =>
                    setRecommendation(e.target.value as OpportunityRecommendation)
                  }
                >
                  {RECOMMENDATION_OPTIONS.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field full">
                <span>Next action</span>
                <input
                  value={nextAction}
                  onChange={(e) => setNextAction(e.target.value)}
                  placeholder="e.g., Draft aims / schedule PI call"
                />
              </label>

              {scoreData?.recommended_next_action && (
                <div className="full">
                  <p className="meta">
                    Suggested from fit scoring: {scoreData.recommended_next_action}
                  </p>
                </div>
              )}
            </div>

            <div className="form-actions" style={{ gap: "0.75rem" }}>
              <button
                className="button"
                type="button"
                onClick={() => void onSaveWorkflow()}
                disabled={saving}
              >
                {saving ? "Saving..." : "Save workflow"}
              </button>
              <button
                className="button button-secondary"
                type="button"
                onClick={() => void onDelete()}
                disabled={saving}
              >
                Delete
              </button>
            </div>
          </section>
            </>
          )}
        </>
      )}
    </main>
  );
}
