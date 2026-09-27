const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface Account {
  account_id: string;
  label: number;
  abuse_probability: number;
  risk_score: number;
  risk_level: string;
  decision: string;
  case_status?: string | null;
  primary_signal: string;
}

export interface RiskResponse {
  account_id: string;
  abuse_probability: number;
  risk_score: number;
  risk_level: string;
  decision: string;
  reasons: string[];
}

export interface Stats {
  total_accounts: number;
  abuse_accounts: number;
  normal_accounts: number;
  critical_accounts: number;
  high_risk_accounts: number;
  medium_risk_accounts: number;
  low_risk_accounts: number;
  review_count: number;
  monitor_count: number;
  allow_count: number;
  total_transactions: number;
  detected_rings_count?: number;
  total_flagged_volume?: number;
}

export interface AbuseRing {
  ring_id: string;
  name: string;
  threat_level: string;
  risk_score: number;
  avg_risk_score: number;
  accounts_count: number;
  primary_account: string;
  member_accounts: string[];
  internal_transactions: number;
  internal_volume: number;
  critical_members_count: number;
  high_risk_members_count: number;
  primary_pattern: string;
  suspicious_indicators: string[];
}

export interface Node {
  id: string;
  type: string;
  risk_score?: number;
  risk_level?: string;
  abuse_probability?: number;
  decision?: string;
  entity_type?: string;
}

export interface Edge {
  source: string;
  target: string;
  type: string;
  amount?: number;
  timestamp?: string;
}

export interface Network {
  nodes: Node[];
  edges: Edge[];
}

export interface Transaction {
  transaction_id: string;
  sender_id: string;
  receiver_id: string;
  amount: string | number;
  timestamp: string;
  direction: string;
  counterparty?: string;
  counterparty_risk_level?: string;
  counterparty_risk_score?: number;
  is_suspicious?: boolean;
  suspicious_reason?: string | null;
}

export interface InvestigationCase {
  account_id: string;
  status: string | null;
  updated_at: string | null;
  notes?: string | null;
  investigator?: string | null;
}

export interface AuditEvent {
  timestamp: string;
  event_type: string;
  account_id: string;
  action: string;
  previous_status: string | null;
  new_status: string | null;
  notes?: string | null;
  investigator?: string | null;
}

export interface EvidenceItem {
  id: string;
  category: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  value?: number | string | null;
  related_accounts: string[];
  relationship_type?: string | null;
}

export interface EvidenceCategories {
  identity: EvidenceItem[];
  network: EvidenceItem[];
  behavioral: EvidenceItem[];
  temporal: EvidenceItem[];
}

export interface TransactionSummary {
  total: number;
  incoming: number;
  outgoing: number;
  total_sent: number;
  total_received: number;
}

export interface NetworkSummary {
  related_accounts: number;
  transaction_connections: number;
  shared_entity_connections: number;
  total_connections: number;
}

export interface TimelineEvent {
  timestamp: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  account_id: string;
  related_account_id?: string | null;
  amount?: number | null;
}

export interface InvestigationContext {
  account_id: string;
  risk: RiskResponse;
  evidence: EvidenceCategories;
  transaction_summary: TransactionSummary;
  network_summary: NetworkSummary;
  case: InvestigationCase;
  timeline: TimelineEvent[];
  investigator_brief: InvestigatorBrief;
  audit_history: AuditEvent[];
}

export interface InvestigatorBrief {
  headline: string;
  summary: string;
  key_findings: string[];
  strongest_accounts: string[];
  recommended_action: string;
  confidence: string;
}

export type CaseAction =
  | "reviewed"
  | "dismissed"
  | "escalated"
  | "restricted"
  | "note_added"
  | "open";

export async function fetchRings(): Promise<AbuseRing[]> {
  const res = await fetch(`${API_BASE}/rings`);

  if (!res.ok) {
    throw new Error("Failed to fetch abuse rings");
  }

  return res.json();
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats`);

  if (!res.ok) {
    throw new Error("Failed to fetch stats");
  }

  return res.json();
}

export async function fetchAccounts(): Promise<Account[]> {
  const res = await fetch(`${API_BASE}/accounts`);

  if (!res.ok) {
    throw new Error("Failed to fetch accounts");
  }

  return res.json();
}

export async function fetchAccountRisk(
  accountId: string,
): Promise<RiskResponse> {
  const res = await fetch(
    `${API_BASE}/accounts/${accountId}`,
  );

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Account not found");
    }

    throw new Error("Failed to fetch account risk");
  }

  return res.json();
}

export async function fetchAccountNetwork(
  accountId: string,
): Promise<Network> {
  const res = await fetch(
    `${API_BASE}/accounts/${accountId}/network`,
  );

  if (!res.ok) {
    throw new Error("Failed to fetch account network");
  }

  return res.json();
}

export async function fetchAccountTransactions(
  accountId: string,
): Promise<Transaction[]> {
  const res = await fetch(
    `${API_BASE}/accounts/${accountId}/transactions`,
  );

  if (!res.ok) {
    throw new Error(
      "Failed to fetch account transactions",
    );
  }

  return res.json();
}

export async function fetchAccountCase(
  accountId: string,
): Promise<InvestigationCase> {
  const res = await fetch(
    `${API_BASE}/accounts/${accountId}/case`,
  );

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Account not found");
    }

    throw new Error(
      "Failed to fetch investigation case",
    );
  }

  return res.json();
}

export async function fetchAccountInvestigation(
  accountId: string,
): Promise<InvestigationContext> {
  const res = await fetch(
    `${API_BASE}/accounts/${accountId}/investigation`,
  );

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Account not found");
    }

    throw new Error(
      "Failed to fetch investigation context",
    );
  }

  return res.json();
}

export async function updateAccountCase(
  accountId: string,
  action: CaseAction,
  notes?: string,
  investigator?: string,
): Promise<InvestigationCase> {
  const res = await fetch(
    `${API_BASE}/accounts/${accountId}/case`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
        notes: notes || undefined,
        investigator: investigator || undefined,
      }),
    },
  );

  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("Account not found");
    }

    if (res.status === 400) {
      throw new Error(
        "Invalid investigation action",
      );
    }

    throw new Error(
      "Failed to update investigation case",
    );
  }

  return res.json();
}