import { useEffect, useState } from "react";
import { generateAiSummary } from "../services/opportunities";
import type { OpportunityAISummary } from "../types/aiSummary";

type OpportunityAISummarySectionProps = {
  opportunityId: number;
  initialSummary: OpportunityAISummary | null;
};

export function OpportunityAISummarySection({
  opportunityId,
  initialSummary,
}: OpportunityAISummarySectionProps) {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<OpportunityAISummary | null>(initialSummary);

  useEffect(() => {
    setSummary(initialSummary);
  }, [initialSummary]);

  async function onGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const result = await generateAiSummary(opportunityId);
      setSummary(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to generate AI summary");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <section className="card section-gap">
      <div className="card-header">
        <h2>AI summary</h2>
        <button
          className="button"
          type="button"
          onClick={() => void onGenerate()}
          disabled={generating}
        >
          {generating ? "Generating..." : "Generate AI Summary"}
        </button>
      </div>

      <p className="meta">
        Uses your configured LLM provider (OpenAI or Gemini) with the opportunity, research
        profile, and saved literature.
      </p>

      {error && <p className="error">{error}</p>}

      {!summary && !error && (
        <p className="meta">No AI summary yet. Click Generate AI Summary to create one.</p>
      )}

      {summary && (
        <dl className="details ai-summary-details">
          <div className="full">
            <dt>Opportunity summary</dt>
            <dd className="prose">{summary.opportunity_summary}</dd>
          </div>
          <div className="full">
            <dt>Why it fits your profile</dt>
            <dd className="prose">{summary.why_it_fits}</dd>
          </div>
          <div className="full">
            <dt>Concerns</dt>
            <dd className="prose">{summary.concerns}</dd>
          </div>
          <div className="full">
            <dt>Recommended framing</dt>
            <dd className="prose">{summary.recommended_framing}</dd>
          </div>
          <div className="full">
            <dt>Recommended next actions</dt>
            <dd className="prose">{summary.recommended_next_actions}</dd>
          </div>
          <div className="full">
            <dt>Possible proposal title</dt>
            <dd className="prose proposal-title">{summary.possible_proposal_title}</dd>
          </div>
        </dl>
      )}
    </section>
  );
}
