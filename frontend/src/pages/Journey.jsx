import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';

const STAGES = ['free_sample_audit', 'paid_pilot', 'monthly_plan'];
const STAGE_LABELS = { free_sample_audit: 'Free Sample Audit', paid_pilot: 'Paid Pilot', monthly_plan: 'Monthly Plan' };
const STAGE_COLORS = { free_sample_audit: 'bg-yellow-100 text-yellow-800', paid_pilot: 'bg-blue-100 text-blue-800', monthly_plan: 'bg-green-100 text-green-800' };

export default function Journey() {
  const { user } = useAuth();
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');
  const [journey, setJourney] = useState(null);
  const [kpis, setKpis] = useState([]);

  useEffect(() => {
    api.get('/plants/').then((r) => {
      setPlants(r.data);
      const pid = user?.plant_id || (r.data.length > 0 ? r.data[0].id : '');
      setPlantId(pid);
    });
  }, []);

  useEffect(() => {
    if (!plantId) return;
    api.get(`/journey/${plantId}`).then((r) => setJourney(r.data));
    api.get(`/journey/${plantId}/kpis`).then((r) => setKpis(r.data));
  }, [plantId]);

  const updateStatus = async (status) => {
    await api.post(`/journey/${plantId}`, { status, notes: `Updated to ${status}` });
    api.get(`/journey/${plantId}`).then((r) => setJourney(r.data));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Customer Journey</h1>
        {user?.role === 'admin' && (
          <select value={plantId} onChange={(e) => setPlantId(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
            {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        )}
      </div>

      {/* Stage pipeline */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="font-semibold mb-4">Stage Pipeline</h2>
        <div className="flex items-center gap-2 flex-wrap">
          {STAGES.map((stage, i) => {
            const isCurrent = journey?.current_status === stage;
            return (
              <div key={stage} className="flex items-center gap-2">
                <button
                  onClick={() => updateStatus(stage)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isCurrent ? 'bg-[#1a365d] text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {STAGE_LABELS[stage]}
                </button>
                {i < STAGES.length - 1 && <span className="text-gray-300">→</span>}
              </div>
            );
          })}
        </div>
      </div>

      {/* History */}
      {journey?.history?.length > 0 && (
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="font-semibold mb-3">Journey History</h2>
          <div className="space-y-3">
            {journey.history.map((h, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#1a365d]" />
                <span className={`px-2 py-0.5 text-xs rounded ${STAGE_COLORS[h.status]}`}>{STAGE_LABELS[h.status]}</span>
                <span className="text-sm text-gray-500">{new Date(h.changed_at).toLocaleDateString('en-IN')}</span>
                {h.notes && <span className="text-sm text-gray-400">— {h.notes}</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* KPIs */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="font-semibold mb-3">Retention KPIs</h2>
        {kpis.length > 0 ? (
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left px-4 py-2">Month</th>
                <th className="text-right px-4 py-2">Report Open Rate</th>
                <th className="text-right px-4 py-2">Defect Catch Rate</th>
                <th className="text-center px-4 py-2">Churned?</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {kpis.map((k) => (
                <tr key={k.id}>
                  <td className="px-4 py-2">{k.month}</td>
                  <td className="px-4 py-2 text-right">{(k.report_open_rate * 100).toFixed(0)}%</td>
                  <td className="px-4 py-2 text-right">{(k.defect_catch_rate * 100).toFixed(0)}%</td>
                  <td className="px-4 py-2 text-center">{k.churned ? '❌' : '✅'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="text-gray-400 text-sm">No KPI data yet</p>}
      </div>
    </div>
  );
}
