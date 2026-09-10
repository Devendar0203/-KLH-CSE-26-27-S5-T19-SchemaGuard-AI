import React, { useState, useEffect } from 'react';

const API_BASE = "http://127.0.0.1:8000";

export default function App() {
  const [liveData, setLiveData] = useState({
    status_summary: { active_runs: 0, total_runs: 0, total_records: 0, total_quarantined: 0, system_health: "HEALTHY" },
    workers: [],
    events: [],
    decisions: [],
    knowledge_base: [],
    actions_log: []
  });
  const [triggeringFault, setTriggeringFault] = useState(null);
  const [activeTab, setActiveTab] = useState("live");

  const fetchLive = async () => {
    try {
      const res = await fetch(`${API_BASE}/live`);
      if (res.ok) {
        const data = await res.json();
        setLiveData(data);
      }
    } catch (e) {
      console.error("Error polling live backend:", e);
    }
  };

  useEffect(() => {
    fetchLive();
    const interval = setInterval(fetchLive, 2000); // 2 second live poll
    return () => clearInterval(interval);
  }, []);

  const handleSimulateFault = async (faultType) => {
    setTriggeringFault(faultType);
    try {
      const res = await fetch(`${API_BASE}/simulate/fault`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fault_type: faultType, source_name: "customers_csv" })
      });
      if (res.ok) {
        await fetchLive();
      }
    } catch (e) {
      alert(`Simulation error: ${e.message}`);
    } finally {
      setTriggeringFault(null);
    }
  };

  const handleApproveDecision = async (decisionId) => {
    try {
      const res = await fetch(`${API_BASE}/actions/${decisionId}/approve`, { method: "POST" });
      if (res.ok) {
        await fetchLive();
      }
    } catch (e) {
      alert(`Approval error: ${e.message}`);
    }
  };

  const { status_summary, workers, events, decisions, knowledge_base } = liveData;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-4 mb-6">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-indigo-500 bg-clip-text text-transparent">
              SchemaGuard AI
            </span>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-mono bg-cyan-950 text-cyan-400 border border-cyan-800">
              MAPE-K Self-Healing
            </span>
          </div>
          <p className="text-slate-400 text-sm mt-1">Autonomous Data Pipeline Self-Adaptation Engine</p>
        </div>

        {/* Global System Health Indicator */}
        <div className="flex items-center gap-3">
          <div className={`px-4 py-2 rounded-lg border font-medium flex items-center gap-2 ${
            status_summary.system_health === 'HEALTHY'
              ? 'bg-emerald-950/60 border-emerald-800 text-emerald-300'
              : 'bg-amber-950/60 border-amber-800 text-amber-300 animate-pulse'
          }`}>
            <span className={`w-2.5 h-2.5 rounded-full ${status_summary.system_health === 'HEALTHY' ? 'bg-emerald-400' : 'bg-amber-400'}`}></span>
            Pipeline Health: {status_summary.system_health}
          </div>
        </div>
      </header>

      {/* Top Stat Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Total Records Ingested</div>
          <div className="text-3xl font-extrabold text-white mt-2 font-mono">{status_summary.total_records}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Quarantined Records</div>
          <div className={`text-3xl font-extrabold mt-2 font-mono ${status_summary.total_quarantined > 0 ? 'text-amber-400' : 'text-slate-300'}`}>
            {status_summary.total_quarantined}
          </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Pipeline Runs</div>
          <div className="text-3xl font-extrabold text-cyan-400 mt-2 font-mono">{status_summary.total_runs}</div>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Active Worker Nodes</div>
          <div className="text-3xl font-extrabold text-indigo-400 mt-2 font-mono">{workers.length || 1}</div>
        </div>
      </div>

      {/* Fault Injection Panel */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-900/50 rounded-xl p-5 mb-8 shadow-lg">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-md font-bold text-indigo-300 flex items-center gap-2">
            <span>⚡ Trigger Fault Simulation (Demo Controls)</span>
          </h2>
          <span className="text-xs text-slate-400 font-mono">POST /simulate/fault</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { id: "schema_drift", label: "Schema Drift", icon: "📐", color: "hover:bg-amber-600/30 border-amber-800/80 text-amber-200" },
            { id: "bad_data", label: "Bad Data", icon: "🚫", color: "hover:bg-rose-600/30 border-rose-800/80 text-rose-200" },
            { id: "worker_crash", label: "Worker Crash", icon: "💥", color: "hover:bg-red-600/30 border-red-800/80 text-red-200" },
            { id: "db_outage", label: "DB Outage", icon: "🗄️", color: "hover:bg-purple-600/30 border-purple-800/80 text-purple-200" },
            { id: "workload_spike", label: "Workload Spike", icon: "📈", color: "hover:bg-cyan-600/30 border-cyan-800/80 text-cyan-200" }
          ].map(item => (
            <button
              key={item.id}
              onClick={() => handleSimulateFault(item.id)}
              disabled={triggeringFault !== null}
              className={`p-3 rounded-lg border bg-slate-950 text-sm font-semibold transition-all flex items-center justify-center gap-2 shadow-sm ${item.color} disabled:opacity-50`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {triggeringFault === item.id && <span className="animate-spin text-xs">🌀</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Main Content Split: Events & Decisions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Events Feed (Monitor & Analyze) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col h-[480px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <h3 className="font-bold text-slate-200 flex items-center gap-2">
              <span>📡 Event Monitoring Feed (M-A)</span>
              <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-mono">{events.length}</span>
            </h3>
          </div>
          <div className="overflow-y-auto flex-1 space-y-3 pr-1">
            {events.length === 0 ? (
              <div className="text-center text-slate-500 py-12 text-sm">No detected events yet. Trigger a demo fault above!</div>
            ) : (
              events.map(ev => (
                <div key={ev.id} className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold font-mono text-cyan-300 text-sm">{ev.event_type.toUpperCase()}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      ev.severity === 'CRITICAL' ? 'bg-red-950 text-red-400 border border-red-800' :
                      ev.severity === 'HIGH' ? 'bg-rose-950 text-rose-400 border border-rose-800' :
                      'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}>
                      {ev.severity}
                    </span>
                  </div>
                  <div className="text-slate-400 text-[11px] font-mono">
                    Detected: {ev.detected_at ? new Date(ev.detected_at).toLocaleTimeString() : 'N/A'}
                  </div>
                  {ev.evidence && (
                    <div className="bg-slate-900/80 p-2 rounded text-slate-300 font-mono text-[11px] overflow-x-auto">
                      {JSON.stringify(ev.evidence)}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* AI Decision & Planning Feed (Plan & Execute) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col h-[480px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-4">
            <h3 className="font-bold text-slate-200 flex items-center gap-2">
              <span>🧠 AI Recovery Decisions (P-E)</span>
              <span className="text-xs bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded-full font-mono">{decisions.length}</span>
            </h3>
          </div>
          <div className="overflow-y-auto flex-1 space-y-3 pr-1">
            {decisions.length === 0 ? (
              <div className="text-center text-slate-500 py-12 text-sm">No recovery decisions generated yet.</div>
            ) : (
              decisions.map(dec => (
                <div key={dec.id} className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-indigo-300 text-sm font-mono">{dec.chosen_action}</span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      dec.status === 'EXECUTED' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' :
                      dec.status === 'PENDING_APPROVAL' ? 'bg-amber-950 text-amber-300 border border-amber-800 animate-pulse' :
                      'bg-indigo-950 text-indigo-300 border border-indigo-800'
                    }`}>
                      {dec.status}
                    </span>
                  </div>
                  <div className="text-slate-300 text-xs">{dec.rationale}</div>

                  {/* Confidence Bar */}
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-400">Confidence:</span>
                    <div className="flex-1 bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full ${dec.confidence >= 0.8 ? 'bg-emerald-400' : 'bg-amber-400'}`}
                        style={{ width: `${(dec.confidence || 0) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-[10px] font-mono text-slate-300">{Math.round((dec.confidence || 0) * 100)}%</span>
                  </div>

                  {/* Interactive Human Approval Button */}
                  {dec.status === 'PENDING_APPROVAL' && (
                    <div className="pt-2 border-t border-slate-800 flex gap-2">
                      <button
                        onClick={() => handleApproveDecision(dec.id)}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-3 py-1 rounded text-xs transition"
                      >
                        ✓ Approve & Execute Action
                      </button>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Knowledge Base Table (Knowledge) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <h3 className="font-bold text-slate-200 mb-3 flex items-center gap-2">
          <span>📚 Knowledge Base (Self-Learning History)</span>
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase">
                <th className="py-2.5 px-3">Event Type</th>
                <th className="py-2.5 px-3">Action Executed</th>
                <th className="py-2.5 px-3">Outcome Summary</th>
                <th className="py-2.5 px-3">Success</th>
                <th className="py-2.5 px-3">Logged At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {knowledge_base.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-6 text-center text-slate-500">No knowledge base logs recorded yet.</td>
                </tr>
              ) : (
                knowledge_base.map(k => (
                  <tr key={k.id} className="hover:bg-slate-800/40">
                    <td className="py-2.5 px-3 font-bold text-cyan-300">{k.event_type}</td>
                    <td className="py-2.5 px-3 text-indigo-300">{k.action}</td>
                    <td className="py-2.5 px-3 text-slate-300">{k.outcome}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] ${k.success_bool ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400'}`}>
                        {k.success_bool ? 'SUCCESS' : 'FAILED'}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {k.created_at ? new Date(k.created_at).toLocaleTimeString() : 'N/A'}
                    </td>
                  </tr>
                ))
              ) }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
