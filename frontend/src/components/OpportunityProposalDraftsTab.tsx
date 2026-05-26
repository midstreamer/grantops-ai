import { useCallback, useEffect, useState } from "react";
import {
  exportProposalDraftToGoogleDoc,
  generateConceptNote,
  listOpportunityDrafts,
  updateProposalDraft,
} from "../services/proposalDrafts";
import type { ProposalDraftRead } from "../types/proposalDraft";

type OpportunityProposalDraftsTabProps = {
  opportunityId: number;
};

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

export function OpportunityProposalDraftsTab({
  opportunityId,
}: OpportunityProposalDraftsTabProps) {
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exportingDoc, setExportingDoc] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<ProposalDraftRead[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editContent, setEditContent] = useState("");

  const selectedDraft = drafts.find((d) => d.id === selectedId) ?? null;

  const syncEditor = useCallback((draft: ProposalDraftRead | null) => {
    setEditTitle(draft?.title ?? "");
    setEditContent(draft?.content ?? "");
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOpportunityDrafts(opportunityId);
      setDrafts(data);
      setSelectedId((prev) => {
        if (prev != null && data.some((d) => d.id === prev)) return prev;
        return data[0]?.id ?? null;
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load proposal drafts");
    } finally {
      setLoading(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    syncEditor(selectedDraft);
  }, [selectedDraft, syncEditor]);

  async function onGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const draft = await generateConceptNote(opportunityId);
      setDrafts((prev) => [draft, ...prev.filter((d) => d.id !== draft.id)]);
      setSelectedId(draft.id);
      syncEditor(draft);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to generate concept note");
    } finally {
      setGenerating(false);
    }
  }

  async function onExportGoogleDoc() {
    if (!selectedDraft) return;
    setExportingDoc(true);
    setError(null);
    try {
      const updated = await exportProposalDraftToGoogleDoc(selectedDraft.id);
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      syncEditor(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to export to Google Docs");
    } finally {
      setExportingDoc(false);
    }
  }

  async function onSave() {
    if (!selectedDraft) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateProposalDraft(opportunityId, selectedDraft.id, {
        title: editTitle.trim() || selectedDraft.title,
        content: editContent,
      });
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      syncEditor(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save draft");
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2>Proposal drafts</h2>
        <button
          className="button"
          type="button"
          onClick={() => void onGenerate()}
          disabled={generating || loading}
        >
          {generating ? "Generating concept note..." : "Generate Concept Note"}
        </button>
      </div>

      <p className="meta">
        AI-generated concept notes use your research profile, opportunity details, fit
        analysis, and saved literature. Edit and save drafts here before exporting to your
        proposal workflow.
      </p>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Loading drafts...</p>
      ) : drafts.length === 0 ? (
        <p className="meta">
          No proposal drafts yet. Click Generate Concept Note to create one with your
          configured LLM provider.
        </p>
      ) : (
        <div className="drafts-layout">
          <aside className="drafts-sidebar">
            <h3 className="drafts-sidebar-title">Saved drafts</h3>
            <ul className="drafts-list">
              {drafts.map((draft) => (
                <li key={draft.id}>
                  <button
                    type="button"
                    className={
                      draft.id === selectedId ? "draft-item active" : "draft-item"
                    }
                    onClick={() => setSelectedId(draft.id)}
                  >
                    <span className="draft-item-title">{draft.title}</span>
                    <span className="draft-item-meta">
                      {draft.draft_type.replace(/_/g, " ")} ·{" "}
                      {formatTimestamp(draft.updated_at)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          {selectedDraft && (
            <div className="draft-editor">
              <label className="field">
                <span>Title</span>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                />
              </label>

              <label className="field">
                <span>Content</span>
                <textarea
                  className="draft-content"
                  rows={24}
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                />
              </label>

              <div className="actions">
                <button
                  className="button"
                  type="button"
                  onClick={() => void onSave()}
                  disabled={saving || generating || exportingDoc}
                >
                  {saving ? "Saving..." : "Save draft"}
                </button>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => void onExportGoogleDoc()}
                  disabled={saving || generating || exportingDoc}
                >
                  {exportingDoc ? "Exporting..." : "Export to Google Docs"}
                </button>
              </div>

              {selectedDraft.google_doc_url && (
                <p className="meta">
                  <a
                    className="link"
                    href={selectedDraft.google_doc_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open Google Doc
                  </a>
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
