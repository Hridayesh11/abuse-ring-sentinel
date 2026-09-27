import { useEffect, useMemo, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  fetchAccountInvestigation,
  fetchAccountNetwork,
  fetchAccountTransactions,
  updateAccountCase,
} from "../api";
import type {
  CaseAction,
  EvidenceItem,
  InvestigationContext,
  Network,
  Transaction,
} from "../api";
import {
  ArrowLeft,
  AlertTriangle,
  ShieldCheck,
  Activity,
  Search,
  FileText,
  Fingerprint,
  Network as NetworkIcon,
  Clock,
  CheckCircle,
  Users,
  Ban,
  MessageSquare,
  ArrowDownLeft,
  ArrowUpRight,
  X,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";
import AbuseRingGraph from "../components/AbuseRingGraph";

function Toast({
  message,
  type,
  onClose,
}: {
  message: string;
  type: "success" | "error" | "info";
  onClose: () => void;
}) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3500);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="toast">
      {type === "success" ? (
        <CheckCircle className="text-low" size={18} />
      ) : type === "error" ? (
        <AlertTriangle className="text-critical" size={18} />
      ) : (
        <Activity className="text-medium" size={18} />
      )}
      <span className="text-sm font-medium">{message}</span>
    </div>
  );
}

function evidenceSeverityClass(severity: string): string {
  if (severity === "high") {
    return "text-critical";
  }

  if (severity === "medium") {
    return "text-high";
  }

  return "text-low";
}

function evidenceSeverityLabel(severity: string): string {
  return severity.toUpperCase();
}

function formatTimestamp(timestamp: string): string {
  if (!timestamp) {
    return "Unknown time";
  }

  const date = new Date(timestamp);

  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatAmount(
  amount: number | string | null | undefined,
): string {
  if (amount === null || amount === undefined) {
    return "—";
  }

  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (Number.isNaN(num)) return String(amount);

  return num.toLocaleString(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function EvidenceCard({
  item,
  onAccountClick,
}: {
  item: EvidenceItem;
  onAccountClick: (accountId: string) => void;
}) {
  return (
    <div
      className="p-4 rounded border mb-3"
      style={{
        borderColor: "var(--border-color)",
        backgroundColor: "var(--bg-surface-hover)",
      }}
    >
      <div className="flex justify-between items-start gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h5 className="font-semibold text-sm">
              {item.title}
            </h5>

            <span
              className={`text-xs font-semibold ${evidenceSeverityClass(
                item.severity,
              )}`}
            >
              {evidenceSeverityLabel(item.severity)}
            </span>
          </div>

          <p className="text-sm text-secondary">
            {item.description}
          </p>
        </div>

        {item.value !== null &&
          item.value !== undefined && (
            <span className="font-mono text-sm font-semibold whitespace-nowrap">
              {typeof item.value === "number"
                ? item.value.toLocaleString()
                : item.value}
            </span>
          )}
      </div>

      {item.related_accounts.length > 0 && (
        <div
          className="mt-3 pt-3 border-t"
          style={{
            borderColor: "var(--border-color)",
          }}
        >
          <div className="flex items-center gap-2 text-xs text-secondary mb-2">
            <Users size={13} />
            {item.relationship_type
              ? `Connected through shared ${item.relationship_type}`
              : "Related Accounts"
            }
          </div>

          <div className="flex flex-wrap gap-2">
            {item.related_accounts.map((relatedAccount) => (
              <button
                key={relatedAccount}
                type="button"
                className="badge badge-outline text-text-primary"
                style={{
                  cursor: "pointer",
                  borderColor: "var(--border-color)",
                }}
                onClick={() =>
                  onAccountClick(relatedAccount)
                }
                title={`Investigate ${relatedAccount}`}
              >
                {relatedAccount}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function EvidenceSection({
  title,
  icon,
  items,
  emptyMessage,
  onAccountClick,
}: {
  title: string;
  icon: React.ReactNode;
  items: EvidenceItem[];
  emptyMessage: string;
  onAccountClick: (accountId: string) => void;
}) {
  return (
    <div>
      <h4 className="text-sm font-semibold text-secondary uppercase tracking-wider mb-3 flex items-center gap-2">
        {icon}
        {title}
        <span className="badge badge-outline text-xs ml-auto">
          {items.length} {items.length === 1 ? 'signal' : 'signals'}
        </span>
      </h4>

      {items.length > 0 ? (
        <div>
          {items.map((item) => (
            <EvidenceCard
              key={item.id}
              item={item}
              onAccountClick={onAccountClick}
            />
          ))}
        </div>
      ) : (
        <p className="text-sm text-secondary mb-4 italic p-3 rounded border border-dashed border-border-color">
          {emptyMessage}
        </p>
      )}
    </div>
  );
}

export default function Investigation() {
  const { accountId } = useParams<{
    accountId: string;
  }>();

  const navigate = useNavigate();

  const [searchId, setSearchId] = useState("");
  const [investigation, setInvestigation] =
    useState<InvestigationContext | null>(null);
  const [network, setNetwork] =
    useState<Network | null>(null);
  const [transactions, setTransactions] =
    useState<Transaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] =
    useState<string | null>(null);

  const [toast, setToast] = useState<{
    message: string;
    type: "success" | "error" | "info";
  } | null>(null);

  const [caseStatus, setCaseStatus] =
    useState<string | null>(null);
  const [savingAction, setSavingAction] =
    useState(false);

  // Active navigation tab
  const [activeTab, setActiveTab] = useState<
    "overview" | "evidence" | "network" | "transactions" | "timeline" | "audit" | "all"
  >("overview");

  // Action modal state
  const [actionModal, setActionModal] = useState<{
    open: boolean;
    action: CaseAction | null;
    title: string;
    description: string;
  }>({
    open: false,
    action: null,
    title: "",
    description: "",
  });

  const [modalNote, setModalNote] = useState("");
  const [modalInvestigator, setModalInvestigator] = useState("Lead Risk Analyst - Fraud Ops");

  // Transaction filter states
  const [txDirectionFilter, setTxDirectionFilter] = useState<"ALL" | "incoming" | "outgoing">("ALL");
  const [txSuspiciousOnly, setTxSuspiciousOnly] = useState(false);
  const [txSearch, setTxSearch] = useState("");

  useEffect(() => {
    if (!accountId) {
      return;
    }

    let isMounted = true;
    setSearchId(accountId);
    setCaseStatus(null);

    async function load() {
      if (isMounted) {
        setLoading(true);
        setError(null);
      }

      try {
        if (!accountId) {
          return;
        }

        const [
          investigationData,
          networkData,
          transactionsData,
        ] = await Promise.all([
          fetchAccountInvestigation(accountId),
          fetchAccountNetwork(accountId),
          fetchAccountTransactions(accountId).catch(() => []),
        ]);

        if (isMounted) {
          setInvestigation(investigationData);
          setNetwork(networkData);
          setTransactions(transactionsData);
          setCaseStatus(
            investigationData.case.status,
          );
        }
      } catch (err: unknown) {
        if (isMounted) {
          const message =
            err instanceof Error
              ? err.message
              : "Failed to load account investigation";

          setError(message);
          setInvestigation(null);
          setNetwork(null);
          setTransactions([]);
          setCaseStatus(null);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [accountId]);

  const handleSearch = (
    e: React.FormEvent,
  ) => {
    e.preventDefault();

    if (searchId.trim()) {
      navigate(
        `/investigation/${searchId.trim()}`,
      );
    }
  };

  const caseLabel = (
    status: string | null,
  ) => {
    if (status === "reviewed") {
      return "Reviewed";
    }

    if (status === "dismissed") {
      return "Dismissed";
    }

    if (status === "escalated") {
      return "Escalated";
    }

    if (status === "restricted") {
      return "Restricted";
    }

    return "Open";
  };

  const auditActionLabel = (
    action: string,
  ) => {
    if (action === "reviewed") {
      return "Marked as Reviewed";
    }

    if (action === "dismissed") {
      return "Cleared / Dismissed";
    }

    if (action === "escalated") {
      return "Escalated to Fraud Ops";
    }

    if (action === "restricted") {
      return "Account Restricted / Frozen";
    }

    if (action === "note_added") {
      return "Investigation Note Added";
    }

    if (action === "open") {
      return "Case Reopened";
    }

    return `Case Action: ${action}`;
  };

  const auditStatusLabel = (
    status: string | null,
  ) => {
    return caseLabel(status);
  };

  const openActionPrompt = (action: CaseAction) => {
    let title = "";
    let description = "";
    let defaultNote = "";

    switch (action) {
      case "escalated":
        title = "Escalate to Fraud Operations";
        description = "Mark this account as confirmed abuse and escalate to fraud operations for ring containment.";
        defaultNote = "Confirmed multi-signal identity overlap and high reciprocal ring transactions. Requesting account freeze.";
        break;
      case "restricted":
        title = "Restrict Account / Freeze Transactions";
        description = "Temporarily suspend account settlement and restrict outward transactions pending ring investigation.";
        defaultNote = "Account restricted due to shared hardware device linkage with critical syndicate accounts.";
        break;
      case "reviewed":
        title = "Mark Case as Reviewed";
        description = "Log that this account has been formally reviewed by risk operations.";
        defaultNote = "Forensic evidence and network topology inspected. Monitoring active.";
        break;
      case "dismissed":
        title = "Dismiss / Clear Account";
        description = "Clear risk flags as benign activity or false positive.";
        defaultNote = "Activity verified with merchant documentation. Safe to process.";
        break;
      case "note_added":
        title = "Add Investigation Case Note";
        description = "Log an immutable observation to the persistent audit history without altering case state.";
        defaultNote = "";
        break;
      case "open":
        title = "Reopen Investigation Case";
        description = "Revert case to unreviewed open status for renewed inquiry.";
        defaultNote = "New transaction activity detected. Reopening investigation.";
        break;
    }

    setModalNote(defaultNote);
    setActionModal({
      open: true,
      action,
      title,
      description,
    });
  };

  const handleActionSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!accountId || savingAction || !actionModal.action) {
      return;
    }

    const action = actionModal.action;
    const note = modalNote.trim();
    const investigator = modalInvestigator.trim() || "Lead Risk Analyst";

    setSavingAction(true);

    try {
      const updated = await updateAccountCase(
        accountId,
        action,
        note || undefined,
        investigator,
      );

      setCaseStatus(updated.status);
      setActionModal((prev) => ({ ...prev, open: false }));

      /*
       * Re-fetch the investigation context so the UI
       * receives the persisted audit history rather
       * than constructing a local/fake audit event.
       */
      const refreshedInvestigation =
        await fetchAccountInvestigation(accountId);

      setInvestigation(refreshedInvestigation);
      setCaseStatus(
        refreshedInvestigation.case.status,
      );

      setToast({
        message: action === "note_added" 
          ? "Investigation note logged to audit trail"
          : `Case status updated to ${caseLabel(updated.status)}`,
        type:
          action === "escalated" || action === "restricted"
            ? "error"
            : "success",
      });
    } catch (err: unknown) {
      setToast({
        message:
          err instanceof Error
            ? err.message
            : "Failed to save investigation action",
        type: "error",
      });
    } finally {
      setSavingAction(false);
    }
  };

  const pivotToAccount = (
    relatedAccountId: string,
  ) => {
    navigate(
      `/investigation/${relatedAccountId}`,
    );
  };

  // Filtered transactions for the dedicated transactions tab
  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      if (txDirectionFilter !== "ALL" && tx.direction !== txDirectionFilter) {
        return false;
      }
      if (txSuspiciousOnly && !tx.is_suspicious) {
        return false;
      }
      if (txSearch.trim()) {
        const query = txSearch.trim().toLowerCase();
        const cp = (tx.counterparty || (tx.direction === "outgoing" ? tx.receiver_id : tx.sender_id)).toLowerCase();
        const id = tx.transaction_id.toLowerCase();
        if (!cp.includes(query) && !id.includes(query)) {
          return false;
        }
      }
      return true;
    });
  }, [transactions, txDirectionFilter, txSuspiciousOnly, txSearch]);

  const totalEvidenceCount = useMemo(() => {
    if (!investigation) return 0;
    const { identity, network, behavioral, temporal } = investigation.evidence;
    return identity.length + network.length + behavioral.length + temporal.length;
  }, [investigation]);

  const suspiciousTxCount = useMemo(() => {
    return transactions.filter((tx) => tx.is_suspicious).length;
  }, [transactions]);

  return (
    <div style={{ position: "relative" }}>
      {toast && (
        <div className="toast-container">
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        </div>
      )}

      {/* Action Confirmation Modal */}
      {actionModal.open && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
                  {actionModal.action === "escalated" ? (
                    <AlertTriangle size={20} className="text-critical" />
                  ) : actionModal.action === "restricted" ? (
                    <Ban size={20} className="text-critical" />
                  ) : actionModal.action === "reviewed" ? (
                    <ShieldCheck size={20} className="text-high" />
                  ) : (
                    <MessageSquare size={20} className="text-low" />
                  )}
                  {actionModal.title}
                </h3>
                <p className="text-xs text-secondary mt-1">
                  {actionModal.description}
                </p>
              </div>
              <button
                type="button"
                className="text-secondary hover:text-white"
                onClick={() => setActionModal((prev) => ({ ...prev, open: false }))}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleActionSubmit} className="flex-col gap-4">
              <div>
                <label className="text-xs font-semibold text-secondary uppercase tracking-wider block mb-1">
                  Investigator Identity / Source
                </label>
                <input
                  type="text"
                  className="search-input"
                  style={{ width: "100%" }}
                  value={modalInvestigator}
                  onChange={(e) => setModalInvestigator(e.target.value)}
                  placeholder="e.g. Lead Risk Analyst (Fraud Ops)"
                />
              </div>

              <div className="mt-3">
                <label className="text-xs font-semibold text-secondary uppercase tracking-wider block mb-1">
                  Investigation Rationale / Reason (Logged to Audit Trail)
                </label>
                <textarea
                  className="search-input"
                  style={{ width: "100%", height: 90, resize: "vertical", fontFamily: "inherit" }}
                  value={modalNote}
                  onChange={(e) => setModalNote(e.target.value)}
                  placeholder="Explain why this action is being taken for persistent forensic record..."
                  required={actionModal.action === "note_added"}
                />
              </div>

              <div className="flex justify-end gap-2 mt-4">
                <button
                  type="button"
                  className="btn btn-outline"
                  onClick={() => setActionModal((prev) => ({ ...prev, open: false }))}
                  disabled={savingAction}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className={
                    actionModal.action === "escalated" || actionModal.action === "restricted"
                      ? "btn btn-critical"
                      : "btn btn-primary"
                  }
                  disabled={savingAction}
                >
                  {savingAction ? "Persisting Action..." : "Confirm & Save Audit Entry"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Top Header & Search Bar */}
      <div className="flex justify-between items-center mb-6 flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="flex items-center gap-2 text-secondary hover:text-white transition"
          >
            <ArrowLeft size={20} />
            Dashboard
          </button>

          <h1
            className="page-title"
            style={{ marginBottom: 0 }}
          >
            Forensic Investigation Console
          </h1>
        </div>

        <form
          onSubmit={handleSearch}
          className="flex gap-2"
        >
          <input
            type="text"
            placeholder="Search Account ID (e.g. ACC_00001)..."
            className="search-input"
            style={{ minWidth: 260 }}
            value={searchId}
            onChange={(e) =>
              setSearchId(e.target.value)
            }
          />

          <button
            type="submit"
            className="btn btn-primary"
            style={{ padding: "0.5rem 1rem" }}
          >
            <Search size={16} />
            Inspect
          </button>
        </form>
      </div>

      {!accountId && !loading && (
        <div
          className="card text-center"
          style={{ padding: "6rem 2rem" }}
        >
          <Search
            size={48}
            className="text-secondary mx-auto mb-4 opacity-50"
          />

          <h2 className="text-xl font-semibold mb-2">
            Select an Account for Forensic Investigation
          </h2>

          <p className="text-secondary max-w-md mx-auto mb-6">
            Enter an account ID above or click any candidate from the Executive Dashboard queue to inspect structured evidence, network graph, and audit actions.
          </p>

          <div className="flex justify-center gap-3 flex-wrap">
            <button
              className="btn btn-outline"
              onClick={() => navigate("/investigation/ACC_00001")}
            >
              Inspect ACC_00001 (Ring 001 Hub)
            </button>
            <button
              className="btn btn-outline"
              onClick={() => navigate("/investigation/ACC_00009")}
            >
              Inspect ACC_00009 (Ring 002 Hub)
            </button>
            <button
              className="btn btn-outline"
              onClick={() => navigate("/investigation/ACC_00153")}
            >
              Inspect ACC_00153 (Score 100 Hub)
            </button>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex-col gap-6">
          <div
            className="skeleton"
            style={{ height: 200 }}
          />

          <div
            className="skeleton"
            style={{ height: 400 }}
          />
        </div>
      )}

      {error && (
        <div
          className="card border-critical mb-6"
          style={{
            borderColor: "var(--color-critical)",
          }}
        >
          <div className="flex items-center gap-3 text-critical">
            <AlertTriangle size={24} />

            <h2 className="text-lg font-bold">
              Account Not Found or Error
            </h2>
          </div>

          <p className="mt-2 text-secondary">
            {error}
          </p>

          <button
            type="button"
            className="btn btn-outline mt-4"
            onClick={() => navigate("/")}
          >
            Return to Executive Dashboard
          </button>
        </div>
      )}

      {investigation &&
        !loading &&
        !error && (
          <div className="flex-col gap-6">
            {/* =========================================================
                RISK HEADER & INVESTIGATOR ACTIONS
            ========================================================= */}
            <div
              className="card border mb-6"
              style={{
                borderColor:
                  investigation.risk.risk_score >= 80
                    ? "rgba(239, 68, 68, 0.5)"
                    : investigation.risk.risk_score >= 60
                      ? "rgba(249, 115, 22, 0.5)"
                      : "var(--border-color)",
              }}
            >
              <div className="flex justify-between items-start mb-6 flex-wrap gap-4">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="card-title text-2xl font-bold font-mono">
                      {investigation.account_id}
                    </h2>
                    <span
                      className={`badge ${investigation.risk.risk_level.toLowerCase()}`}
                      style={{
                        fontSize: "0.875rem",
                        padding: "0.375rem 0.75rem",
                      }}
                    >
                      {investigation.risk.risk_level} RISK
                    </span>
                  </div>

                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span
                      className={`badge badge-outline ${
                        investigation.risk.decision === "REVIEW"
                          ? "text-high"
                          : investigation.risk.decision === "ALLOW"
                            ? "text-low"
                            : "text-medium"
                      }`}
                    >
                      AI POLICY DECISION: {investigation.risk.decision}
                    </span>

                    <span
                      className={`badge badge-outline ${
                        caseStatus === "escalated"
                          ? "text-critical"
                          : caseStatus === "restricted"
                            ? "text-critical"
                            : caseStatus === "reviewed"
                              ? "text-low"
                              : "text-secondary"
                      }`}
                    >
                      <CheckCircle size={12} className="mr-1" />
                      CASE STATUS: {caseLabel(caseStatus)}
                    </span>

                    {investigation.case.updated_at && (
                      <span className="text-xs text-secondary ml-2">
                        Updated {formatTimestamp(investigation.case.updated_at)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Investigator Action Bar */}
                <div className="flex gap-2 flex-wrap justify-end">
                  <button
                    className="btn btn-outline"
                    disabled={savingAction}
                    onClick={() => openActionPrompt("reviewed")}
                    title="Mark case as reviewed"
                  >
                    <ShieldCheck size={16} className="text-low" />
                    Mark Reviewed
                  </button>

                  <button
                    className="btn btn-outline"
                    style={{ borderColor: "rgba(239, 68, 68, 0.4)" }}
                    disabled={savingAction}
                    onClick={() => openActionPrompt("restricted")}
                    title="Freeze account payouts and restrict transfers"
                  >
                    <Ban size={16} className="text-critical" />
                    Restrict Account
                  </button>

                  <button
                    className="btn btn-critical"
                    disabled={savingAction}
                    onClick={() => openActionPrompt("escalated")}
                    title="Escalate to fraud operations as confirmed abuse"
                  >
                    <AlertTriangle size={16} />
                    Escalate Abuse
                  </button>

                  <button
                    className="btn btn-outline"
                    disabled={savingAction}
                    onClick={() => openActionPrompt("dismissed")}
                    title="Clear risk as false positive"
                  >
                    <CheckCircle size={16} className="text-low" />
                    Dismiss / Clear
                  </button>

                  <button
                    className="btn btn-outline"
                    disabled={savingAction}
                    onClick={() => openActionPrompt("note_added")}
                    title="Log note to persistent audit history"
                  >
                    <MessageSquare size={16} />
                    Add Note
                  </button>

                  {caseStatus && (
                    <button
                      className="btn btn-outline"
                      disabled={savingAction}
                      onClick={() => openActionPrompt("open")}
                    >
                      Reopen
                    </button>
                  )}
                </div>
              </div>

              {/* KPI Score Cards */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                <div className="stat-card">
                  <span className="stat-label">ML Abuse Probability</span>
                  <span
                    className={`stat-value font-mono ${
                      investigation.risk.abuse_probability >= 0.8
                        ? 'text-critical'
                        : investigation.risk.abuse_probability >= 0.5
                          ? 'text-high'
                          : 'text-low'
                    }`}
                  >
                    {(investigation.risk.abuse_probability * 100).toFixed(1)}%
                  </span>
                  <div className="risk-score-bar mt-2">
                    <div
                      className="risk-score-bar-fill"
                      style={{
                        width: `${investigation.risk.abuse_probability * 100}%`,
                        background: investigation.risk.abuse_probability >= 0.8
                          ? 'linear-gradient(90deg, #dc2626, #ef4444)'
                          : investigation.risk.abuse_probability >= 0.5
                            ? 'linear-gradient(90deg, #ea580c, #f97316)'
                            : 'linear-gradient(90deg, #1d4ed8, #3b82f6)',
                      }}
                    />
                  </div>
                </div>

                <div className="stat-card">
                  <span className="stat-label">Composite Risk Score</span>
                  <span
                    className={`stat-value font-mono ${
                      investigation.risk.risk_score >= 80
                        ? 'text-critical'
                        : investigation.risk.risk_score >= 60
                          ? 'text-high'
                          : 'text-low'
                    }`}
                  >
                    {investigation.risk.risk_score}
                    <span className="text-sm text-secondary font-normal" style={{ fontFamily: 'inherit' }}>{' '}/ 100</span>
                  </span>
                  <div className="risk-score-bar mt-2">
                    <div
                      className="risk-score-bar-fill"
                      style={{
                        width: `${investigation.risk.risk_score}%`,
                        background: investigation.risk.risk_score >= 80
                          ? 'linear-gradient(90deg, #dc2626, #ef4444)'
                          : investigation.risk.risk_score >= 60
                            ? 'linear-gradient(90deg, #ea580c, #f97316)'
                            : 'linear-gradient(90deg, #1d4ed8, #3b82f6)',
                      }}
                    />
                  </div>
                </div>

                <div className="stat-card">
                  <span className="stat-label">Risk Signals Identified</span>
                  <span className="stat-value font-mono text-medium">
                    {investigation.risk.reasons.length}
                    <span className="text-sm text-secondary font-normal" style={{ fontFamily: 'inherit' }}>{' '}signals</span>
                  </span>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {investigation.risk.reasons.slice(0, 2).map((r, i) => (
                      <span key={i} className="badge badge-outline text-text-secondary" style={{ fontSize: '0.65rem', padding: '0.15rem 0.4rem' }}>
                        {r.length > 32 ? r.slice(0, 32) + '...' : r}
                      </span>
                    ))}
                    {investigation.risk.reasons.length > 2 && (
                      <span className="text-xs text-secondary self-center">+{investigation.risk.reasons.length - 2} more</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* =========================================================
                WORKFLOW TABS
            ========================================================= */}
            <div className="tabs-nav">
              <button
                type="button"
                className={`tab-btn ${activeTab === "overview" ? "active" : ""}`}
                onClick={() => setActiveTab("overview")}
              >
                <Activity size={16} />
                Overview & Brief
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "evidence" ? "active" : ""}`}
                onClick={() => setActiveTab("evidence")}
              >
                <FileText size={16} />
                Evidence & Signals
                <span className="badge badge-outline text-xs" style={{ padding: "0.1rem 0.4rem" }}>
                  {totalEvidenceCount}
                </span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "network" ? "active" : ""}`}
                onClick={() => setActiveTab("network")}
              >
                <NetworkIcon size={16} />
                Abuse Ring Network
                {network && (
                  <span className="badge badge-outline text-xs" style={{ padding: "0.1rem 0.4rem" }}>
                    {network.nodes.length}
                  </span>
                )}
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "transactions" ? "active" : ""}`}
                onClick={() => setActiveTab("transactions")}
              >
                <ArrowDownLeft size={16} />
                Transactions
                <span className="badge badge-outline text-xs" style={{ padding: "0.1rem 0.4rem" }}>
                  {transactions.length}
                </span>
                {suspiciousTxCount > 0 && (
                  <span className="badge critical text-xs" style={{ padding: "0.1rem 0.4rem" }}>
                    {suspiciousTxCount} alert{suspiciousTxCount > 1 ? "s" : ""}
                  </span>
                )}
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "timeline" ? "active" : ""}`}
                onClick={() => setActiveTab("timeline")}
              >
                <Clock size={16} />
                Activity Timeline
                <span className="badge badge-outline text-xs" style={{ padding: "0.1rem 0.4rem" }}>
                  {investigation.timeline.length}
                </span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "audit" ? "active" : ""}`}
                onClick={() => setActiveTab("audit")}
              >
                <ShieldCheck size={16} />
                Audit Trail & Actions
                <span className="badge badge-outline text-xs" style={{ padding: "0.1rem 0.4rem" }}>
                  {investigation.audit_history.length}
                </span>
              </button>

              <button
                type="button"
                className={`tab-btn ${activeTab === "all" ? "active" : ""}`}
                onClick={() => setActiveTab("all")}
                style={{ marginLeft: "auto" }}
              >
                Full Dossier (All)
              </button>
            </div>

            {/* =========================================================
                TAB: OVERVIEW & BRIEF
            ========================================================= */}
            {(activeTab === "overview" || activeTab === "all") && (
              <div className="flex-col gap-6">
                {/* Investigator Brief */}
                <div
                  className="brief-card mb-6"
                >
                  <div className="flex items-start justify-between gap-4 mb-4 flex-wrap">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <ShieldAlert size={20} className="text-critical" />
                        <h2 className="card-title text-lg font-bold">
                          Investigator Briefing & AI Risk Synthesis
                        </h2>
                      </div>

                      <h3 className="font-semibold text-lg text-text-primary mb-2">
                        {investigation.investigator_brief.headline}
                      </h3>

                      <p className="text-secondary text-sm max-w-4xl leading-relaxed">
                        {investigation.investigator_brief.summary}
                      </p>
                    </div>

                    <span
                      className="badge badge-outline"
                      style={{
                        color:
                          investigation.investigator_brief.confidence === "HIGH"
                            ? "var(--color-critical)"
                            : investigation.investigator_brief.confidence === "MEDIUM"
                              ? "var(--color-high)"
                              : "var(--color-low)",
                        borderColor: "currentColor",
                        whiteSpace: "nowrap",
                      }}
                    >
                      {investigation.investigator_brief.confidence} CONFIDENCE
                    </span>
                  </div>

                  <div className="grid-2 gap-6 mt-4 pt-4 border-t" style={{ borderColor: "var(--border-color)" }}>
                    <div>
                      <span className="stat-label">
                        Forensic Key Findings
                      </span>

                      <ul className="mt-2 space-y-2">
                        {investigation.investigator_brief.key_findings.map(
                          (finding, index) => (
                            <li
                              key={`${finding}-${index}`}
                              className="text-sm flex items-start gap-2"
                            >
                              <span
                                className="mt-1"
                                style={{
                                  color: "var(--color-critical)",
                                }}
                              >
                                •
                              </span>
                              <span>{finding}</span>
                            </li>
                          ),
                        )}
                      </ul>
                    </div>

                    <div>
                      <span className="stat-label">
                        Strongest Linked Accounts
                      </span>

                      {investigation.investigator_brief.strongest_accounts.length > 0 ? (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {investigation.investigator_brief.strongest_accounts.map(
                            (relatedAccount) => (
                              <button
                                key={relatedAccount}
                                type="button"
                                className="badge badge-outline text-text-primary"
                                style={{
                                  cursor: "pointer",
                                  borderColor: "var(--border-color)",
                                }}
                                onClick={() =>
                                  pivotToAccount(relatedAccount)
                                }
                                title={`Investigate ${relatedAccount}`}
                              >
                                {relatedAccount}
                              </button>
                            ),
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-secondary mt-2">
                          No strongly linked accounts identified.
                        </p>
                      )}

                      <div className="mt-4">
                        <span className="stat-label">
                          Recommended Investigator Action
                        </span>

                        <div className="font-semibold text-text-primary mt-1 flex items-center gap-2">
                          <CheckCircle size={16} className="text-low" />
                          {investigation.investigator_brief.recommended_action}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Summary Metrics */}
                <div className="grid-2 mb-6">
                  <div
                    className="card"
                    style={{
                      padding: "1.25rem",
                      backgroundColor: "var(--bg-surface-hover)",
                    }}
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <Activity size={18} className="text-low" />
                      <h3 className="font-semibold">
                        Transaction Activity Summary
                      </h3>
                    </div>

                    <div className="grid-2 gap-3">
                      <div>
                        <span className="stat-label">Total Transactions</span>
                        <div className="font-mono font-semibold text-lg">
                          {investigation.transaction_summary.total}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Incoming</span>
                        <div className="font-mono font-semibold text-low text-lg">
                          {investigation.transaction_summary.incoming}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Outgoing</span>
                        <div className="font-mono font-semibold text-high text-lg">
                          {investigation.transaction_summary.outgoing}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Total Sent</span>
                        <div className="font-mono font-semibold">
                          ${investigation.transaction_summary.total_sent.toLocaleString(
                            undefined,
                            {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            },
                          )}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Total Received</span>
                        <div className="font-mono font-semibold">
                          ${investigation.transaction_summary.total_received.toLocaleString(
                            undefined,
                            {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            },
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div
                    className="card"
                    style={{
                      padding: "1.25rem",
                      backgroundColor: "var(--bg-surface-hover)",
                    }}
                  >
                    <div className="flex items-center gap-2 mb-4">
                      <NetworkIcon size={18} className="text-critical" />
                      <h3 className="font-semibold">
                        Network Graph Connectivity
                      </h3>
                    </div>

                    <div className="grid-2 gap-3">
                      <div>
                        <span className="stat-label">Related Accounts</span>
                        <div className="font-mono font-semibold text-lg">
                          {investigation.network_summary.related_accounts}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Transaction Edges</span>
                        <div className="font-mono font-semibold text-lg">
                          {investigation.network_summary.transaction_connections}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Shared Entity Links</span>
                        <div className="font-mono font-semibold text-lg text-critical">
                          {investigation.network_summary.shared_entity_connections}
                        </div>
                      </div>

                      <div>
                        <span className="stat-label">Total Connections</span>
                        <div className="font-mono font-semibold text-lg">
                          {investigation.network_summary.total_connections}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* =========================================================
                TAB: STRUCTURED EVIDENCE
            ========================================================= */}
            {(activeTab === "evidence" || activeTab === "all") && (
              <div className="card mb-6">
                <div className="card-header border-b pb-4 mb-4" style={{ borderColor: "var(--border-color)" }}>
                  <div>
                    <h2 className="card-title text-lg flex items-center gap-2">
                      <FileText size={20} className="text-critical" />
                      Structured Forensic Evidence
                    </h2>
                    <p className="text-secondary text-sm mt-1">
                      Identified abuse signals categorized by identity correlation, transaction topology, behavioral velocity, and temporal concentration.
                    </p>
                  </div>
                </div>

                <div className="grid-2 gap-6">
                  <EvidenceSection
                    title="Identity Linkage"
                    icon={<Fingerprint size={16} className="text-critical" />}
                    items={investigation.evidence.identity}
                    emptyMessage="No anomalous identity linkage detected."
                    onAccountClick={pivotToAccount}
                  />

                  <EvidenceSection
                    title="Graph & Ring Topology"
                    icon={<NetworkIcon size={16} className="text-critical" />}
                    items={investigation.evidence.network}
                    emptyMessage="No anomalous graph topology detected."
                    onAccountClick={pivotToAccount}
                  />

                  <EvidenceSection
                    title="Behavioral Anomalies"
                    icon={<Activity size={16} className="text-high" />}
                    items={investigation.evidence.behavioral}
                    emptyMessage="No anomalous behavioral transaction patterns detected."
                    onAccountClick={pivotToAccount}
                  />

                  <EvidenceSection
                    title="Temporal Concentration"
                    icon={<Clock size={16} className="text-medium" />}
                    items={investigation.evidence.temporal}
                    emptyMessage="No anomalous temporal concentration detected."
                    onAccountClick={pivotToAccount}
                  />
                </div>
              </div>
            )}

            {/* =========================================================
                TAB: ABUSE RING NETWORK
            ========================================================= */}
            {(activeTab === "network" || activeTab === "all") && (
              <div className="card mb-6">
                <div
                  className="card-header border-b pb-4 mb-4"
                  style={{
                    borderColor: "var(--border-color)",
                  }}
                >
                  <div>
                    <h2 className="card-title text-lg flex items-center gap-2">
                      <NetworkIcon size={20} className="text-critical" />
                      Abuse Ring Network Topology
                    </h2>
                    <p className="text-secondary text-sm mt-1">
                      Interactive network visualization mapping transaction money-flows and shared identity devices/IPs. Click any node to inspect details or pivot.
                    </p>
                  </div>
                </div>

                {network ? (
                  <AbuseRingGraph
                    network={network}
                    mainAccountId={investigation.account_id}
                  />
                ) : (
                  <div className="loading-container">
                    <p>Loading network topology graph...</p>
                  </div>
                )}

                {/* Graph Legend */}
                <div
                  className="flex gap-6 mt-4 text-xs flex-wrap p-4 bg-bg-surface-hover rounded border"
                  style={{
                    borderColor: "var(--border-color)",
                  }}
                >
                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        backgroundColor: "#ef4444",
                        borderRadius: "50%",
                        boxShadow: "0 0 8px rgba(239,68,68,0.7)",
                      }}
                    />
                    <span>Subject Focus Account</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        backgroundColor: "#f97316",
                        borderRadius: "50%",
                      }}
                    />
                    <span>High/Critical Risk Member</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        border: "2px solid #a855f7",
                      }}
                    />
                    <span>Shared Hardware Device</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        border: "2px solid #06b6d4",
                      }}
                    />
                    <span>Shared IP Address</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        width: 10,
                        height: 10,
                        border: "2px solid #f43f5e",
                      }}
                    />
                    <span>Shared Payment Instrument</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        height: 2,
                        width: 20,
                        backgroundColor: "rgba(255,255,255,0.4)",
                      }}
                    />
                    <span>Transaction Edge</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <div
                      style={{
                        height: 2,
                        width: 20,
                        borderTop: "2px dashed rgba(168, 85, 247, 0.7)",
                      }}
                    />
                    <span>Shared Entity Edge</span>
                  </div>
                </div>
              </div>
            )}

            {/* =========================================================
                TAB: TRANSACTIONS LOG
            ========================================================= */}
            {(activeTab === "transactions" || activeTab === "all") && (
              <div className="card mb-6">
                <div
                  className="card-header border-b pb-4 mb-4"
                  style={{
                    borderColor: "var(--border-color)",
                  }}
                >
                  <div className="flex justify-between items-center w-full flex-wrap gap-4">
                    <div>
                      <h2 className="card-title text-lg flex items-center gap-2">
                        <ArrowDownLeft size={20} className="text-low" />
                        Account Transactions & Money Flows
                      </h2>
                      <p className="text-secondary text-sm mt-1">
                        Detailed ledger of all incoming and outgoing transactions, counterparty risk ratings, and suspicious activity flags.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="badge badge-outline text-xs">
                        {filteredTransactions.length} of {transactions.length} transactions
                      </span>
                    </div>
                  </div>
                </div>

                {/* Filters */}
                <div className="flex gap-3 flex-wrap mb-4">
                  <div style={{ flex: "1 1 200px" }}>
                    <input
                      type="text"
                      className="search-input"
                      style={{ width: "100%" }}
                      placeholder="Search counterparty or txn ID..."
                      value={txSearch}
                      onChange={(e) => setTxSearch(e.target.value)}
                    />
                  </div>

                  <div>
                    <select
                      className="search-input"
                      value={txDirectionFilter}
                      onChange={(e) => setTxDirectionFilter(e.target.value as any)}
                    >
                      <option value="ALL">All Directions</option>
                      <option value="incoming">Incoming Only</option>
                      <option value="outgoing">Outgoing Only</option>
                    </select>
                  </div>

                  <label className="flex items-center gap-2 text-sm text-secondary cursor-pointer select-none px-2 py-1 border rounded border-border-color">
                    <input
                      type="checkbox"
                      checked={txSuspiciousOnly}
                      onChange={(e) => setTxSuspiciousOnly(e.target.checked)}
                    />
                    <span>Suspicious Only</span>
                  </label>
                </div>

                {filteredTransactions.length === 0 ? (
                  <div className="text-center py-12 border border-dashed rounded" style={{ borderColor: "var(--border-color)" }}>
                    <ArrowDownLeft size={32} className="text-secondary mx-auto mb-2 opacity-50" />
                    <p className="text-secondary">No transactions match the selected filters.</p>
                  </div>
                ) : (
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Date / Time</th>
                          <th>Direction</th>
                          <th>Counterparty</th>
                          <th>Counterparty Risk</th>
                          <th>Amount</th>
                          <th>Suspicious Indicators</th>
                          <th>Transaction ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredTransactions.map((tx) => {
                          const isOutgoing = tx.direction === "outgoing";
                          const cp = tx.counterparty || (isOutgoing ? tx.receiver_id : tx.sender_id);

                          return (
                            <tr key={tx.transaction_id}>
                              <td className="text-secondary whitespace-nowrap">
                                {formatTimestamp(tx.timestamp)}
                              </td>

                              <td>
                                <span
                                  className={`badge ${
                                    isOutgoing ? "high" : "low"
                                  }`}
                                  style={{ fontSize: "0.75rem", padding: "0.2rem 0.5rem" }}
                                >
                                  {isOutgoing ? (
                                    <>
                                      <ArrowUpRight size={12} className="mr-1 inline" />
                                      OUTGOING
                                    </>
                                  ) : (
                                    <>
                                      <ArrowDownLeft size={12} className="mr-1 inline" />
                                      INCOMING
                                    </>
                                  )}
                                </span>
                              </td>

                              <td>
                                <button
                                  type="button"
                                  className="font-mono text-sm font-semibold hover:underline flex items-center gap-1"
                                  onClick={() => pivotToAccount(cp)}
                                  title={`Investigate ${cp}`}
                                >
                                  {cp}
                                  <ExternalLink size={12} className="opacity-60" />
                                </button>
                              </td>

                              <td>
                                <span
                                  className={`badge ${
                                    tx.counterparty_risk_level === "CRITICAL"
                                      ? "critical"
                                      : tx.counterparty_risk_level === "HIGH"
                                        ? "high"
                                        : "badge-outline text-secondary"
                                  }`}
                                >
                                  {tx.counterparty_risk_level || "NORMAL"}
                                </span>
                              </td>

                              <td className="font-mono font-semibold">
                                ${formatAmount(tx.amount)}
                              </td>

                              <td>
                                {tx.is_suspicious ? (
                                  <span className="text-xs text-critical flex items-center gap-1 font-medium">
                                    <AlertTriangle size={13} />
                                    {tx.suspicious_reason || "Flagged in abuse ring"}
                                  </span>
                                ) : (
                                  <span className="text-xs text-secondary">
                                    Normal flow
                                  </span>
                                )}
                              </td>

                              <td className="font-mono text-xs text-secondary">
                                {tx.transaction_id}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* =========================================================
                TAB: ACTIVITY TIMELINE
            ========================================================= */}
            {(activeTab === "timeline" || activeTab === "all") && (
              <div className="card mb-6">
                <div
                  className="card-header border-b pb-4 mb-0"
                  style={{
                    borderColor: "var(--border-color)",
                  }}
                >
                  <h2 className="card-title text-lg flex items-center gap-2">
                    <Clock size={20} className="text-low" />
                    Investigation Activity Timeline
                  </h2>
                  <p className="text-secondary text-sm mt-1">
                    Unified chronological event stream including transaction activity, observable evidence milestones, and case state actions.
                  </p>
                </div>

                {investigation.timeline.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText
                      size={32}
                      className="text-secondary mx-auto mb-2 opacity-50"
                    />
                    <p className="text-secondary">
                      No timeline events found for this account.
                    </p>
                  </div>
                ) : (
                  <div className="table-container mt-4">
                    <table>
                      <thead>
                        <tr>
                          <th>Date / Time</th>
                          <th>Type</th>
                          <th>Event</th>
                          <th>Related Account</th>
                          <th>Details</th>
                        </tr>
                      </thead>

                      <tbody>
                        {investigation.timeline.map((event, index) => {
                          const eventType =
                            event.type === "transaction"
                              ? "TRANSACTION"
                              : event.type === "case_action"
                                ? "CASE ACTION"
                                : "EVIDENCE";

                          const eventTypeClass =
                            event.type === "case_action"
                              ? "text-high"
                              : event.type === "evidence"
                                ? "text-critical"
                                : "text-secondary";

                          return (
                            <tr key={`${event.timestamp}-${event.type}-${index}`}>
                              <td className="text-secondary whitespace-nowrap">
                                {formatTimestamp(event.timestamp)}
                              </td>

                              <td>
                                <span
                                  className={`badge badge-outline ${eventTypeClass}`}
                                  style={{
                                    borderColor: "currentColor",
                                  }}
                                >
                                  {eventType}
                                </span>
                              </td>

                              <td>
                                <div className="font-semibold text-text-primary">
                                  {event.title}
                                </div>
                              </td>

                              <td>
                                {event.related_account_id ? (
                                  <button
                                    type="button"
                                    className="font-mono text-sm hover:underline"
                                    onClick={() =>
                                      pivotToAccount(event.related_account_id!)
                                    }
                                    title={`Investigate ${event.related_account_id}`}
                                  >
                                    {event.related_account_id}
                                  </button>
                                ) : (
                                  <span className="text-secondary">—</span>
                                )}
                              </td>

                              <td>
                                <div className="text-sm text-secondary max-w-lg">
                                  {event.description}
                                </div>

                                {event.amount !== null &&
                                  event.amount !== undefined && (
                                    <div className="font-mono text-sm font-semibold mt-1">
                                      ${formatAmount(event.amount)}
                                    </div>
                                  )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* =========================================================
                TAB: AUDIT TRAIL & CASE ACTIONS
            ========================================================= */}
            {(activeTab === "audit" || activeTab === "all") && (
              <div className="card mb-8">
                <div
                  className="card-header border-b pb-4 mb-4"
                  style={{
                    borderColor: "var(--border-color)",
                  }}
                >
                  <div className="flex items-center justify-between gap-4 w-full flex-wrap">
                    <div>
                      <h2 className="card-title text-lg flex items-center gap-2">
                        <Clock size={20} className="text-critical" />
                        Persistent Investigation Audit Trail
                      </h2>

                      <p className="text-secondary text-sm mt-1">
                        Cryptographically backed, append-only audit trail persisted to datasets/audit_log.json. Every case decision and note is permanently recorded.
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className="btn btn-outline"
                        style={{ fontSize: "0.8125rem", padding: "0.4rem 0.8rem" }}
                        onClick={() => openActionPrompt("note_added")}
                      >
                        <MessageSquare size={14} />
                        Add Forensic Note
                      </button>

                      {investigation.audit_history.length > 0 && (
                        <span className="badge badge-outline text-text-primary">
                          {investigation.audit_history.length}{" "}
                          {investigation.audit_history.length === 1 ? "EVENT" : "EVENTS"}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {investigation.audit_history.length === 0 ? (
                  <div className="text-center py-12 border border-dashed rounded" style={{ borderColor: "var(--border-color)" }}>
                    <Clock
                      size={32}
                      className="text-secondary mx-auto mb-2 opacity-50"
                    />

                    <p className="text-secondary font-medium">
                      No case actions recorded yet for this account.
                    </p>

                    <p className="text-xs text-secondary mt-1 max-w-md mx-auto">
                      Use the action buttons above or click "Add Forensic Note" to record formal investigator findings to the audit log.
                    </p>

                    <div className="flex justify-center gap-2 mt-4">
                      <button
                        type="button"
                        className="btn btn-primary"
                        style={{ fontSize: "0.8125rem" }}
                        onClick={() => openActionPrompt("reviewed")}
                      >
                        Mark as Reviewed
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-4">
                    {investigation.audit_history.map((event, index) => {
                      const isLast = index === investigation.audit_history.length - 1;

                      return (
                        <div
                          key={`${event.timestamp}-${event.action}-${index}`}
                          className="flex gap-4"
                          style={{
                            paddingBottom: isLast ? 0 : "1.25rem",
                          }}
                        >
                          <div
                            className="flex flex-col items-center"
                            style={{
                              width: 20,
                              flexShrink: 0,
                            }}
                          >
                            <div
                              style={{
                                width: 10,
                                height: 10,
                                borderRadius: "50%",
                                backgroundColor:
                                  event.action === "escalated" || event.action === "restricted"
                                    ? "var(--color-critical)"
                                    : event.action === "dismissed"
                                      ? "var(--color-low)"
                                      : event.action === "reviewed"
                                        ? "var(--color-high)"
                                        : "var(--color-medium)",
                                marginTop: 5,
                                boxShadow: "0 0 0 4px var(--bg-surface-hover)",
                              }}
                            />

                            {!isLast && (
                              <div
                                style={{
                                  width: 1,
                                  flex: 1,
                                  marginTop: 6,
                                  backgroundColor: "var(--border-color)",
                                }}
                              />
                            )}
                          </div>

                          <div
                            className="flex-1 rounded border p-4"
                            style={{
                              borderColor: "var(--border-color)",
                              backgroundColor: "var(--bg-surface-hover)",
                            }}
                          >
                            <div className="flex justify-between items-start gap-4 flex-wrap">
                              <div>
                                <div className="flex items-center gap-2 flex-wrap">
                                  <h3 className="font-semibold text-sm text-text-primary">
                                    {auditActionLabel(event.action)}
                                  </h3>

                                  <span className="text-xs text-secondary font-mono">
                                    {event.event_type}
                                  </span>

                                  {event.investigator && (
                                    <span className="badge badge-outline text-xs text-text-secondary">
                                      Investigator: {event.investigator}
                                    </span>
                                  )}
                                </div>

                                <div className="flex items-center gap-2 mt-2 text-sm">
                                  <span className="text-secondary text-xs uppercase tracking-wider">
                                    State:
                                  </span>
                                  <span className="text-secondary">
                                    {auditStatusLabel(event.previous_status)}
                                  </span>
                                  <span className="text-secondary">→</span>
                                  <span className="font-semibold text-text-primary">
                                    {auditStatusLabel(event.new_status)}
                                  </span>
                                </div>

                                {event.notes && (
                                  <div
                                    className="mt-3 p-3 rounded text-sm text-text-primary border"
                                    style={{
                                      backgroundColor: "rgba(0, 0, 0, 0.25)",
                                      borderColor: "var(--border-color)",
                                    }}
                                  >
                                    <span className="text-xs font-semibold text-secondary block mb-1">
                                      Forensic Rationale / Reason:
                                    </span>
                                    {event.notes}
                                  </div>
                                )}
                              </div>

                              <div className="text-xs text-secondary whitespace-nowrap">
                                {formatTimestamp(event.timestamp)}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
    </div>
  );
}