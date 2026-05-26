import { useEffect, useMemo, useState } from "react";
import { fetchResearchProfile, updateResearchProfile } from "../services/researchProfile";
import type { ResearchProfileRead } from "../types/researchProfile";
import type { ResearchProfileUpdatePayload } from "../services/researchProfile";

function arrayToTextarea(values: string[]) {
  return (values || []).join("\n");
}

function textareaToArray(text: string) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

type FormState = {
  researcher_name: string;
  title: string; // empty string means null
  institution: string; // empty string means null
  primary_research_focus: string;

  research_domains_text: string;
  methods_text: string;
  target_funders_text: string;
  preferred_outputs_text: string;
  keywords_text: string;
};

export function ResearchProfilePage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [profile, setProfile] = useState<ResearchProfileRead | null>(null);

  const [form, setForm] = useState<FormState | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const current = await fetchResearchProfile();
        if (cancelled) return;
        setProfile(current);
        setForm({
          researcher_name: current.researcher_name,
          title: current.title ?? "",
          institution: current.institution ?? "",
          primary_research_focus: current.primary_research_focus,

          research_domains_text: arrayToTextarea(current.research_domains),
          methods_text: arrayToTextarea(current.methods),
          target_funders_text: arrayToTextarea(current.target_funders),
          preferred_outputs_text: arrayToTextarea(current.preferred_outputs),
          keywords_text: arrayToTextarea(current.keywords),
        });
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : "Unable to load profile");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const canSave = useMemo(() => {
    if (!form || !profile) return false;
    return (
      form.researcher_name.trim().length > 0 &&
      form.primary_research_focus.trim().length > 0
    );
  }, [form, profile]);

  async function onSave() {
    if (!profile || !form) return;
    if (!canSave) return;

    setSaving(true);
    setError(null);
    try {
      const payload: ResearchProfileUpdatePayload = {
        researcher_name: form.researcher_name.trim(),
        title: form.title.trim() === "" ? null : form.title.trim(),
        institution: form.institution.trim() === "" ? null : form.institution.trim(),
        primary_research_focus: form.primary_research_focus.trim(),
        research_domains: textareaToArray(form.research_domains_text),
        methods: textareaToArray(form.methods_text),
        target_funders: textareaToArray(form.target_funders_text),
        preferred_outputs: textareaToArray(form.preferred_outputs_text),
        keywords: textareaToArray(form.keywords_text),
      };

      const updated = await updateResearchProfile(profile.id, payload);
      setProfile(updated);
      setForm({
        researcher_name: updated.researcher_name,
        title: updated.title ?? "",
        institution: updated.institution ?? "",
        primary_research_focus: updated.primary_research_focus,

        research_domains_text: arrayToTextarea(updated.research_domains),
        methods_text: arrayToTextarea(updated.methods),
        target_funders_text: arrayToTextarea(updated.target_funders),
        preferred_outputs_text: arrayToTextarea(updated.preferred_outputs),
        keywords_text: arrayToTextarea(updated.keywords),
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="page">
      <h1>Research Profile</h1>

      {loading && <p>Loading...</p>}
      {error && (
        <p className="error">
          {error}
        </p>
      )}

      {!loading && profile && form && (
        <section className="card">
          <div className="card-header">
            <h2>Current profile</h2>
            <span className="meta">
              ID: {profile.id} • Updated: {new Date(profile.updated_at).toLocaleString()}
            </span>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              void onSave();
            }}
          >
            <div className="form-grid">
              <label className="field">
                <span>Researcher name</span>
                <input
                  value={form.researcher_name}
                  onChange={(e) =>
                    setForm({ ...form, researcher_name: e.target.value })
                  }
                />
              </label>

              <label className="field">
                <span>Title</span>
                <input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </label>

              <label className="field">
                <span>Institution</span>
                <input
                  value={form.institution}
                  onChange={(e) =>
                    setForm({ ...form, institution: e.target.value })
                  }
                />
              </label>

              <label className="field full">
                <span>Primary research focus</span>
                <input
                  value={form.primary_research_focus}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      primary_research_focus: e.target.value,
                    })
                  }
                />
              </label>

              <label className="field full">
                <span>Research domains (one per line)</span>
                <textarea
                  rows={4}
                  value={form.research_domains_text}
                  onChange={(e) =>
                    setForm({ ...form, research_domains_text: e.target.value })
                  }
                />
              </label>

              <label className="field full">
                <span>Methods (one per line)</span>
                <textarea
                  rows={4}
                  value={form.methods_text}
                  onChange={(e) => setForm({ ...form, methods_text: e.target.value })}
                />
              </label>

              <label className="field full">
                <span>Target funders (one per line)</span>
                <textarea
                  rows={3}
                  value={form.target_funders_text}
                  onChange={(e) =>
                    setForm({ ...form, target_funders_text: e.target.value })
                  }
                />
              </label>

              <label className="field full">
                <span>Preferred outputs (one per line)</span>
                <textarea
                  rows={3}
                  value={form.preferred_outputs_text}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      preferred_outputs_text: e.target.value,
                    })
                  }
                />
              </label>

              <label className="field full">
                <span>Keywords (one per line)</span>
                <textarea
                  rows={4}
                  value={form.keywords_text}
                  onChange={(e) =>
                    setForm({ ...form, keywords_text: e.target.value })
                  }
                />
              </label>
            </div>

            <div className="form-actions">
              <button className="button" type="submit" disabled={!canSave || saving}>
                {saving ? "Saving..." : "Save profile"}
              </button>
            </div>
          </form>
        </section>
      )}
    </main>
  );
}

