export type ScheduledSearchRead = {
  id: number;
  name: string;
  query: string;
  rows: number;
  frequency: "weekly";
  active: boolean;
  last_run_at: string | null;
  created_at: string;
};

export type ScheduledSearchCreate = {
  name: string;
  query: string;
  rows: number;
  frequency: "weekly";
  active: boolean;
};

export type ScheduledSearchUpdate = Partial<ScheduledSearchCreate>;
