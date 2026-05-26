export type ProposalDraftRead = {
  id: number;
  opportunity_id: number;
  title: string;
  draft_type: string;
  content: string;
  google_doc_url: string | null;
  created_at: string;
  updated_at: string;
};

export type ProposalDraftUpdate = {
  title?: string;
  content?: string;
};
