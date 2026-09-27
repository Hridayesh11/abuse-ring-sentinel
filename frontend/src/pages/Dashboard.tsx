import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  ChevronDown,
  Filter,
  Search,
  Users,
  Activity,
  CheckCircle,
  Network,
  Zap,
  DollarSign,
  ArrowRight,
  Layers,
} from "lucide-react";

import { fetchAccounts, fetchRings, fetchStats } from "../api";
import type { Account, AbuseRing, Stats } from "../api";

type SortField =
  | "account_id"
  | "risk_score"
  | "abuse_probability";

type SortDirection = "asc" | "desc";

type RiskFilter =
  | "ALL"
  | "CRITICAL"
  | "HIGH"
  | "MEDIUM"
  | "LOW";

type DecisionFilter =
  | "ALL"
  | "REVIEW"
  | "MONITOR"
  | "ALLOW";

type CaseFilter =
  | "ALL"
  | "UNREVIEWED"
  | "open"
  | "reviewed"
  | "dismissed"
  | "escalated";

function riskClass(riskLevel: string): string {
  switch (riskLevel.toUpperCase()) {
    case "CRITICAL":
      return "critical";
    case "HIGH":
      return "high";
    case "MEDIUM":
      return "medium";
    default:
      return "low";
  }
}

function caseLabel(
  status: string | null | undefined,
): string {
  switch (status) {
    case "open":
      return "OPEN";
    case "reviewed":
      return "REVIEWED";
    case "dismissed":
      return "DISMISSED";
    case "escalated":
      return "ESCALATED";
    default:
      return "UNREVIEWED";
  }
}

function caseStatusClass(
  status: string | null | undefined,
): string {
  switch (status) {
    case "escalated":
      return "text-critical";
    case "reviewed":
    case "dismissed":
      return "text-low";
    case "open":
      return "text-high";
    default:
      return "text-secondary";
  }
}

function matchesCaseFilter(
  account: Account,
  filter: CaseFilter,
): boolean {
  if (filter === "ALL") {
    return true;
  }

  if (filter === "UNREVIEWED") {
    return !account.case_status;
  }

  return account.case_status === filter;
}

export default function Dashboard() {
  const navigate = useNavigate();

  const [stats, setStats] = useState<Stats | null>(null);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [rings, setRings] = useState<AbuseRing[]>([]);
  const [showAllRings, setShowAllRings] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [riskFilter, setRiskFilter] =
    useState<RiskFilter>("ALL");
  const [decisionFilter, setDecisionFilter] =
    useState<DecisionFilter>("ALL");
  const [caseFilter, setCaseFilter] =
    useState<CaseFilter>("ALL");

  const [sortField, setSortField] =
    useState<SortField>("risk_score");
  const [sortDirection, setSortDirection] =
    useState<SortDirection>("desc");

  useEffect(() => {
    let mounted = true;

    async function loadDashboard() {
      try {
        setLoading(true);
        setError(null);

        const [statsData, accountsData, ringsData] =
          await Promise.all([
            fetchStats(),
            fetchAccounts(),
            fetchRings().catch(() => []),
          ]);

        if (!mounted) {
          return;
        }

        setStats(statsData);
        setAccounts(accountsData);
        setRings(ringsData);
      } catch (err: unknown) {
        if (!mounted) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Failed to load dashboard",
        );
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  const unreviewedCaseCount = useMemo(
    () =>
      accounts.filter(
        (account) => !account.case_status,
      ).length,
    [accounts],
  );

  const openCaseCount = useMemo(
    () =>
      accounts.filter(
        (account) => account.case_status === "open",
      ).length,
    [accounts],
  );

  const escalatedCaseCount = useMemo(
    () =>
      accounts.filter(
        (account) =>
          account.case_status === "escalated",
      ).length,
    [accounts],
  );

  const filteredAccounts = useMemo(() => {
    const normalizedSearch =
      search.trim().toLowerCase();

    const result = accounts.filter((account) => {
      const matchesSearch =
        !normalizedSearch ||
        account.account_id
          .toLowerCase()
          .includes(normalizedSearch);

      const matchesRisk =
        riskFilter === "ALL" ||
        account.risk_level.toUpperCase() ===
          riskFilter;

      const matchesDecision =
        decisionFilter === "ALL" ||
        account.decision.toUpperCase() ===
          decisionFilter;

      const matchesCase = matchesCaseFilter(
        account,
        caseFilter,
      );

      return (
        matchesSearch &&
        matchesRisk &&
        matchesDecision &&
        matchesCase
      );
    });

    result.sort((a, b) => {
      let comparison = 0;

      if (sortField === "account_id") {
        comparison = a.account_id.localeCompare(
          b.account_id,
        );
      }

      if (sortField === "risk_score") {
        comparison =
          a.risk_score - b.risk_score;
      }

      if (sortField === "abuse_probability") {
        comparison =
          a.abuse_probability -
          b.abuse_probability;
      }

      return sortDirection === "asc"
        ? comparison
        : -comparison;
    });

    return result.slice(0, 50);
  }, [
    accounts,
    search,
    riskFilter,
    decisionFilter,
    caseFilter,
    sortField,
    sortDirection,
  ]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection((current) =>
        current === "asc" ? "desc" : "asc",
      );
      return;
    }

    setSortField(field);
    setSortDirection("desc");
  };

  const sortIcon = (field: SortField) => {
    if (sortField !== field) {
      return null;
    }

    return sortDirection === "asc" ? (
      <ArrowUp size={13} />
    ) : (
      <ArrowDown size={13} />
    );
  };

  const riskDistribution = stats
    ? [
        {
          label: "CRITICAL",
          value: stats.critical_accounts,
          className: "bg-critical",
        },
        {
          label: "HIGH",
          value: stats.high_risk_accounts,
          className: "bg-high",
        },
        {
          label: "MEDIUM",
          value: stats.medium_risk_accounts,
          className: "bg-medium",
        },
        {
          label: "LOW",
          value: stats.low_risk_accounts,
          className: "bg-low",
        },
      ]
    : [];

  const totalRiskAccounts =
    stats?.total_accounts ?? 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="page-title">
            Executive Dashboard
          </h1>

          <p className="text-secondary mt-1">
            System-wide abuse risk and investigation
            operations
          </p>
        </div>
      </div>

      {error && (
        <div
          className="card mb-6"
          style={{
            borderColor: "var(--color-critical)",
          }}
        >
          <div className="flex items-center gap-3 text-critical">
            <AlertTriangle size={22} />

            <div>
              <h2 className="font-semibold">
                Dashboard Error
              </h2>

              <p className="text-secondary mt-1">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex-col gap-6">
          <div
            className="skeleton"
            style={{ height: 140 }}
          />

          <div
            className="skeleton"
            style={{ height: 120 }}
          />

          <div
            className="skeleton"
            style={{ height: 400 }}
          />
        </div>
      ) : (
        <>
          {/* =========================================================
              DEMO WALKTHROUGH BANNER (RAZORPAY BUILDATHON DEMO)
              ========================================================= */}
          <div className="demo-banner">
            <div className="flex items-center gap-3">
              <div className="pulse-indicator" />
              <div>
                <span className="font-semibold text-sm text-text-primary">
                  Live Forensic Demo Mode:
                </span>
                <span className="text-sm text-secondary ml-2">
                  Select a confirmed abuse ring account to inspect graph topology, structured evidence, and audit persistence:
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                className="demo-chip"
                onClick={() => navigate("/investigation/ACC_00001")}
                title="Investigate ACC_00001 (Syndicate Ring 001 - Hardware Sharing)"
              >
                <Zap size={13} className="text-critical" />
                ACC_00001 <span className="text-critical font-bold">98</span>
              </button>

              <button
                type="button"
                className="demo-chip"
                onClick={() => navigate("/investigation/ACC_00009")}
                title="Investigate ACC_00009 (Syndicate Ring 002 - Circular Velocity)"
              >
                <Zap size={13} className="text-high" />
                ACC_00009 <span className="text-high font-bold">94</span>
              </button>

              <button
                type="button"
                className="demo-chip"
                onClick={() => navigate("/investigation/ACC_00017")}
                title="Investigate ACC_00017 (Syndicate Ring 003 - Payment Syndicate)"
              >
                <Zap size={13} className="text-critical" />
                ACC_00017 <span className="text-critical font-bold">96</span>
              </button>

              <button
                type="button"
                className="demo-chip"
                onClick={() => navigate("/investigation/ACC_00153")}
                title="Investigate ACC_00153 (Syndicate Ring 020 - High Volume Hub)"
              >
                <Zap size={13} className="text-critical" />
                ACC_00153 <span className="text-critical font-bold">100</span>
              </button>
            </div>
          </div>

          {/* =========================================================
              EXECUTIVE METRICS (5 METRIC CARDS)
              ========================================================= */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
            <div className="stat-card">
              <div className="flex items-center gap-2 mb-1">
                <div style={{ width: 28, height: 28, borderRadius: '8px', background: 'rgba(148,163,184,0.1)', border: '1px solid rgba(148,163,184,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Users size={14} style={{ color: 'var(--text-secondary)' }} />
                </div>
                <span className="stat-label">Total Accounts</span>
              </div>
              <span className="stat-value font-mono">
                {stats?.total_accounts.toLocaleString() ?? '—'}
              </span>
            </div>

            <div className="stat-card" style={{ borderColor: 'rgba(239, 68, 68, 0.35)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div style={{ width: 28, height: 28, borderRadius: '8px', background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Network size={14} style={{ color: 'var(--color-critical)' }} />
                </div>
                <span className="stat-label text-critical">Abuse Rings</span>
              </div>
              <span className="stat-value font-mono text-critical">
                {stats?.detected_rings_count ?? rings.length}
                <span className="text-xs text-secondary font-normal" style={{ fontFamily: 'inherit', marginLeft: '0.375rem' }}>active</span>
              </span>
            </div>

            <div className="stat-card" style={{ borderColor: 'rgba(239, 68, 68, 0.25)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div style={{ width: 28, height: 28, borderRadius: '8px', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <AlertTriangle size={14} style={{ color: 'var(--color-critical)' }} />
                </div>
                <span className="stat-label text-critical">Critical Accounts</span>
              </div>
              <span className="stat-value font-mono text-critical">
                {stats?.critical_accounts.toLocaleString() ?? '—'}
              </span>
            </div>

            <div className="stat-card" style={{ borderColor: 'rgba(249, 115, 22, 0.25)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div style={{ width: 28, height: 28, borderRadius: '8px', background: 'rgba(249,115,22,0.1)', border: '1px solid rgba(249,115,22,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <DollarSign size={14} style={{ color: 'var(--color-high)' }} />
                </div>
                <span className="stat-label text-high">Flagged Volume</span>
              </div>
              <span className="stat-value font-mono text-high">
                ${stats?.total_flagged_volume ? (stats.total_flagged_volume / 1_000_000).toFixed(2) + 'M' : '—'}
              </span>
            </div>

            <div className="stat-card" style={{ borderColor: 'rgba(234, 179, 8, 0.25)' }}>
              <div className="flex items-center gap-2 mb-1">
                <div style={{ width: 28, height: 28, borderRadius: '8px', background: 'rgba(234,179,8,0.1)', border: '1px solid rgba(234,179,8,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Activity size={14} style={{ color: 'var(--color-medium)' }} />
                </div>
                <span className="stat-label text-medium">Review Queue</span>
              </div>
              <span className="stat-value font-mono text-medium">
                {stats?.review_count.toLocaleString() ?? '—'}
              </span>
            </div>
          </div>

          {/* =========================================================
              DETECTED ABUSE RINGS & CLUSTERS SECTION
              ========================================================= */}
          {rings.length > 0 && (
            <div className="card mb-6">
              <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
                <div>
                  <h2 className="card-title text-lg flex items-center gap-2">
                    <Layers size={20} className="text-critical" />
                    Detected Abuse Rings & Suspicious Clusters
                  </h2>
                  <p className="text-secondary text-sm mt-1">
                    Graph community detection identified {rings.length} coordinated rings exhibiting shared identity entities and circular velocity.
                  </p>
                </div>

                <button
                  type="button"
                  className="btn btn-outline"
                  style={{ fontSize: '0.8125rem', padding: '0.4rem 0.8rem' }}
                  onClick={() => setShowAllRings((prev) => !prev)}
                >
                  {showAllRings ? "Show Top 4 Rings" : `View All ${rings.length} Rings`}
                </button>
              </div>

              <div 
                style={{ 
                  display: 'grid', 
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', 
                  gap: '1rem' 
                }}
              >
                {(showAllRings ? rings : rings.slice(0, 4)).map((ring) => (
                  <div key={ring.ring_id} className="ring-card">
                    <div>
                      <div className="flex justify-between items-start gap-2 mb-2">
                        <span className="font-mono font-semibold text-sm">
                          {ring.name}
                        </span>
                        <span className={`badge ${ring.threat_level.toLowerCase()} text-xs`}>
                          {ring.threat_level} ({ring.risk_score})
                        </span>
                      </div>

                      <p className="text-xs text-secondary mb-3">
                        {ring.primary_pattern}
                      </p>

                      <div className="grid-2 gap-2 text-xs mb-3 p-2 rounded bg-bg-surface-hover">
                        <div>
                          <span className="text-secondary block">Ring Members</span>
                          <span className="font-semibold font-mono">{ring.accounts_count} accounts</span>
                        </div>
                        <div>
                          <span className="text-secondary block">Internal Volume</span>
                          <span className="font-semibold font-mono text-high">${ring.internal_volume.toLocaleString()}</span>
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-1 mb-3">
                        {ring.member_accounts.slice(0, 4).map((member) => (
                          <span 
                            key={member}
                            className="badge badge-outline text-text-secondary"
                            style={{ fontSize: '0.7rem', padding: '0.15rem 0.4rem' }}
                          >
                            {member}
                          </span>
                        ))}
                        {ring.member_accounts.length > 4 && (
                          <span className="text-xs text-secondary self-center ml-1">
                            +{ring.member_accounts.length - 4} more
                          </span>
                        )}
                      </div>
                    </div>

                    <button
                      type="button"
                      className="btn btn-outline"
                      style={{ 
                        width: '100%', 
                        justifyContent: 'space-between',
                        fontSize: '0.8125rem',
                        marginTop: '0.5rem',
                        borderColor: 'rgba(239, 68, 68, 0.4)',
                        color: 'var(--text-primary)'
                      }}
                      onClick={() => navigate(`/investigation/${ring.primary_account}`)}
                    >
                      <span>Investigate Hub ({ring.primary_account})</span>
                      <ArrowRight size={14} className="text-critical" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* =========================================================
              SYSTEM RISK DISTRIBUTION
              ========================================================= */}

          <div className="card mb-6">
            <div className="flex justify-between items-center mb-3">
              <span className="text-sm uppercase tracking-wider text-secondary">
                System Risk Distribution
              </span>

              <span className="text-sm">
                {stats?.total_transactions.toLocaleString() ??
                  "—"}{" "}
                Total Transactions Monitored
              </span>
            </div>

            <div
              className="flex rounded overflow-hidden"
              style={{
                height: 9,
                backgroundColor:
                  "var(--bg-surface-hover)",
              }}
            >
              {riskDistribution.map((risk) => {
                const percentage =
                  totalRiskAccounts > 0
                    ? (risk.value /
                        totalRiskAccounts) *
                      100
                    : 0;

                return (
                  <div
                    key={risk.label}
                    className={risk.className}
                    style={{
                      width: `${percentage}%`,
                    }}
                    title={`${risk.label}: ${percentage.toFixed(
                      1,
                    )}%`}
                  />
                );
              })}
            </div>

            <div className="flex gap-6 flex-wrap mt-3 text-sm">
              {riskDistribution.map((risk) => {
                const percentage =
                  totalRiskAccounts > 0
                    ? (risk.value /
                        totalRiskAccounts) *
                      100
                    : 0;

                return (
                  <div
                    key={risk.label}
                    className="flex items-center gap-1"
                  >
                    <span
                      className={`risk-dot ${riskClass(
                        risk.label,
                      )}`}
                    />

                    <span>
                      {risk.label} (
                      {percentage.toFixed(1)}%)
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* =========================================================
              INVESTIGATION QUEUE
              ========================================================= */}

          <div className="card">
            <div className="flex justify-between items-start gap-4 mb-5">
              <div>
                <h2 className="card-title text-lg">
                  Investigation Queue
                </h2>

                <div className="flex items-center gap-3 text-sm text-secondary mt-1 flex-wrap">
                  <span>
                    {unreviewedCaseCount} unreviewed
                  </span>

                  <span>•</span>

                  <span>
                    {openCaseCount} open
                  </span>

                  <span>•</span>

                  <span>
                    {escalatedCaseCount} escalated
                  </span>
                </div>
              </div>

              <span className="text-sm text-secondary">
                Showing {filteredAccounts.length}{" "}
                {filteredAccounts.length === 1
                  ? "account"
                  : "accounts"}
                {accounts.length > 50 &&
                  " · top 50"}
              </span>
            </div>

            {/* Filters */}

            <div className="flex gap-3 flex-wrap mb-5">
              <div
                className="flex items-center gap-2"
                style={{ flex: "1 1 220px" }}
              >
                <Search
                  size={18}
                  className="text-secondary"
                />

                <input
                  type="text"
                  placeholder="Search Account ID..."
                  className="search-input"
                  value={search}
                  onChange={(event) =>
                    setSearch(event.target.value)
                  }
                  style={{ width: "100%" }}
                />
              </div>

              <div className="flex items-center gap-2">
                <Filter
                  size={16}
                  className="text-secondary"
                />

                <select
                  value={riskFilter}
                  onChange={(event) =>
                    setRiskFilter(
                      event.target.value as RiskFilter,
                    )
                  }
                  className="search-input"
                  style={{
                    minWidth: 150,
                    cursor: "pointer",
                  }}
                >
                  <option value="ALL">
                    All Risk Levels
                  </option>

                  <option value="CRITICAL">
                    Critical
                  </option>

                  <option value="HIGH">
                    High
                  </option>

                  <option value="MEDIUM">
                    Medium
                  </option>

                  <option value="LOW">
                    Low
                  </option>
                </select>

                <ChevronDown
                  size={14}
                  className="text-secondary"
                  style={{ marginLeft: -30 }}
                />
              </div>

              <div className="flex items-center gap-2">
                <Filter
                  size={16}
                  className="text-secondary"
                />

                <select
                  value={decisionFilter}
                  onChange={(event) =>
                    setDecisionFilter(
                      event.target
                        .value as DecisionFilter,
                    )
                  }
                  className="search-input"
                  style={{
                    minWidth: 150,
                    cursor: "pointer",
                  }}
                >
                  <option value="ALL">
                    All Decisions
                  </option>

                  <option value="REVIEW">
                    Review
                  </option>

                  <option value="MONITOR">
                    Monitor
                  </option>

                  <option value="ALLOW">
                    Allow
                  </option>
                </select>

                <ChevronDown
                  size={14}
                  className="text-secondary"
                  style={{ marginLeft: -30 }}
                />
              </div>

              <div className="flex items-center gap-2">
                <Filter
                  size={16}
                  className="text-secondary"
                />

                <select
                  value={caseFilter}
                  onChange={(event) =>
                    setCaseFilter(
                      event.target.value as CaseFilter,
                    )
                  }
                  className="search-input"
                  style={{
                    minWidth: 150,
                    cursor: "pointer",
                  }}
                >
                  <option value="ALL">
                    All Cases
                  </option>

                  <option value="UNREVIEWED">
                    Unreviewed
                  </option>

                  <option value="open">
                    Open
                  </option>

                  <option value="reviewed">
                    Reviewed
                  </option>

                  <option value="dismissed">
                    Dismissed
                  </option>

                  <option value="escalated">
                    Escalated
                  </option>
                </select>

                <ChevronDown
                  size={14}
                  className="text-secondary"
                  style={{ marginLeft: -30 }}
                />
              </div>
            </div>

            {/* Queue Table */}

            <div
              style={{
                overflowX: "auto",
              }}
            >
              <table
                style={{
                  width: "100%",
                  borderCollapse: "collapse",
                }}
              >
                <thead>
                  <tr
                    className="text-secondary text-sm"
                    style={{
                      borderBottom:
                        "1px solid var(--border-color)",
                    }}
                  >
                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                        cursor: "pointer",
                      }}
                      onClick={() =>
                        handleSort("account_id")
                      }
                    >
                      <div className="flex items-center gap-1">
                        Account ID
                        {sortIcon("account_id")}
                      </div>
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                      }}
                    >
                      Risk Level
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                        cursor: "pointer",
                      }}
                      onClick={() =>
                        handleSort("risk_score")
                      }
                    >
                      <div className="flex items-center gap-1">
                        Risk Score
                        {sortIcon("risk_score")}
                      </div>
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                        cursor: "pointer",
                      }}
                      onClick={() =>
                        handleSort(
                          "abuse_probability",
                        )
                      }
                    >
                      <div className="flex items-center gap-1">
                        Probability
                        {sortIcon(
                          "abuse_probability",
                        )}
                      </div>
                    </th>

                    {/* Primary Signal */}

                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                      }}
                    >
                      Primary Signal
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                      }}
                    >
                      Decision
                    </th>

                    <th
                      style={{
                        textAlign: "left",
                        padding: "0.8rem 1rem",
                        fontWeight: 500,
                      }}
                    >
                      Case
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {filteredAccounts.map((account) => (
                    <tr
                      key={account.account_id}
                      onClick={() =>
                        navigate(
                          `/investigation/${account.account_id}`,
                        )
                      }
                      style={{
                        borderBottom:
                          "1px solid var(--border-color)",
                        cursor: "pointer",
                      }}
                      className="hover:bg-bg-surface-hover"
                    >
                      <td
                        style={{
                          padding: "1rem",
                        }}
                      >
                        <span className="font-mono font-medium">
                          {account.account_id}
                        </span>
                      </td>

                      <td
                        style={{
                          padding: "1rem",
                        }}
                      >
                        <span
                          className={`badge ${riskClass(
                            account.risk_level,
                          )}`}
                        >
                          {account.risk_level}
                        </span>
                      </td>

                      <td
                        style={{
                          padding: "0.875rem 1rem",
                        }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', minWidth: 70 }}>
                          <span
                            className={`font-mono font-semibold text-sm ${
                              account.risk_score >= 80
                                ? 'text-critical'
                                : account.risk_score >= 60
                                  ? 'text-high'
                                  : 'text-low'
                            }`}
                          >
                            {account.risk_score}
                          </span>
                          <div style={{ height: 3, borderRadius: 2, background: 'var(--bg-surface-hover)', overflow: 'hidden', width: 60 }}>
                            <div style={{
                              height: '100%',
                              borderRadius: 2,
                              width: `${account.risk_score}%`,
                              background: account.risk_score >= 80
                                ? 'linear-gradient(90deg, #dc2626, #ef4444)'
                                : account.risk_score >= 60
                                  ? 'linear-gradient(90deg, #ea580c, #f97316)'
                                  : 'linear-gradient(90deg, #1d4ed8, #3b82f6)',
                              transition: 'width 0.3s ease',
                            }} />
                          </div>
                        </div>
                      </td>

                      <td
                        style={{
                          padding: "1rem",
                        }}
                      >
                        <span className="font-mono">
                          {(
                            account.abuse_probability *
                            100
                          ).toFixed(1)}
                          %
                        </span>
                      </td>

                      {/* Primary Signal */}

                      <td
                        style={{
                          padding: "1rem",
                          maxWidth: 260,
                        }}
                      >
                        <span
                          className="text-sm"
                          title={account.primary_signal}
                        >
                          {account.primary_signal}
                        </span>
                      </td>

                      <td
                        style={{
                          padding: "1rem",
                        }}
                      >
                        <span
                          className={`badge badge-outline ${
                            account.decision ===
                            "REVIEW"
                              ? "text-high"
                              : account.decision ===
                                  "ALLOW"
                                ? "text-low"
                                : "text-medium"
                          }`}
                        >
                          {account.decision}
                        </span>
                      </td>

                      <td
                        style={{
                          padding: "1rem",
                        }}
                      >
                        <span
                          className={`badge badge-outline ${caseStatusClass(
                            account.case_status,
                          )}`}
                        >
                          {account.case_status ===
                            "escalated" && (
                            <AlertTriangle
                              size={12}
                              className="mr-1"
                            />
                          )}

                          {(account.case_status ===
                            "reviewed" ||
                            account.case_status ===
                              "dismissed") && (
                            <CheckCircle
                              size={12}
                              className="mr-1"
                            />
                          )}

                          {caseLabel(
                            account.case_status,
                          )}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {filteredAccounts.length === 0 && (
              <div
                className="text-center text-secondary"
                style={{
                  padding: "4rem 1rem",
                }}
              >
                <Search
                  size={32}
                  className="mx-auto mb-3 opacity-50"
                />

                <p className="font-medium">
                  No accounts match the current
                  filters.
                </p>

                <p className="text-sm mt-1">
                  Try clearing one or more filters.
                </p>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}