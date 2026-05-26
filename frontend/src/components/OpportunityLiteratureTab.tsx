import { useCallback, useEffect, useState } from "react";
import {
  findSupportingLiterature,
  getOpportunityLiterature,
  literatureDoiUrl,
} from "../services/literature";
import type { LiteratureItemRead } from "../types/literature";

type OpportunityLiteratureTabProps = {
  opportunityId: number;
};

export function OpportunityLiteratureTab({ opportunityId }: OpportunityLiteratureTabProps) {
  const [loading, setLoading] = useState(true);
  const [finding, setFinding] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<LiteratureItemRead[]>([]);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getOpportunityLiterature(opportunityId);
      setItems(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load literature");
    } finally {
      setLoading(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onFind() {
    setFinding(true);
    setError(null);
    try {
      const saved = await findSupportingLiterature(opportunityId);
      setItems(saved);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to find literature");
    } finally {
      setFinding(false);
    }
  }

  return (
    <section className="card">
      <div className="card-header">
        <h2>Supporting literature</h2>
        <button
          className="button"
          type="button"
          onClick={() => void onFind()}
          disabled={finding || loading}
        >
          {finding ? "Searching OpenAlex..." : "Find Supporting Literature"}
        </button>
      </div>

      <p className="meta">
        Searches OpenAlex using the opportunity title, matched fit keywords, and your research
        profile keywords.
      </p>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p>Loading literature...</p>
      ) : items.length === 0 ? (
        <p className="meta">No literature saved yet. Click Find Supporting Literature to search.</p>
      ) : (
        <ul className="literature-list">
          {items.map((work) => {
            const link = literatureDoiUrl(work.doi, work.url);
            return (
              <li key={work.id} className="literature-item">
                <h3 className="literature-title">{work.title}</h3>
                <div className="literature-meta">
                  {work.publication_year != null && <span>{work.publication_year}</span>}
                  {work.venue && <span>{work.venue}</span>}
                  {work.cited_by_count != null && (
                    <span>Cited by {work.cited_by_count}</span>
                  )}
                </div>
                {work.authors.length > 0 && (
                  <p className="literature-authors">{work.authors.join(", ")}</p>
                )}
                {work.abstract && <p className="literature-abstract">{work.abstract}</p>}
                {link && (
                  <a className="link" href={link} target="_blank" rel="noreferrer">
                    {work.doi ? `DOI: ${work.doi}` : "View publication"}
                  </a>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
