import { useState, useEffect } from 'react';
import api from '../api';
import { Plus, Save, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

export default function Validation() {
  const [interviews, setInterviews] = useState([]);
  const [threshold, setThreshold] = useState(null);
  const [editing, setEditing] = useState(null);

  const load = async () => {
    const [intv, thr] = await Promise.all([
      api.get('/validation/interviews'),
      api.get('/validation/threshold-check'),
    ]);
    setInterviews(intv.data);
    setThreshold(thr.data);
  };

  useEffect(() => { load(); }, []);

  const addInterview = async () => {
    const r = await api.post('/validation/interviews', {});
    setEditing(r.data.id);
    load();
  };

  const saveInterview = async (id, data) => {
    await api.put(`/validation/interviews/${id}`, data);
    setEditing(null);
    load();
  };

  const decisionIcon = {
    Proceed: <CheckCircle size={24} className="text-green-600" />,
    Refine: <AlertTriangle size={24} className="text-yellow-600" />,
    Pivot: <XCircle size={24} className="text-red-600" />,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Validation Tracker</h1>
        <button onClick={addInterview} className="flex items-center gap-2 bg-[#1a365d] text-white px-4 py-2 rounded-lg text-sm hover:bg-[#2c5282]">
          <Plus size={16} /> Add Interview
        </button>
      </div>

      {/* Threshold check */}
      {threshold && (
        <div className={`rounded-xl shadow p-6 ${threshold.decision === 'Proceed' ? 'bg-green-50 border border-green-200' : threshold.decision === 'Refine' ? 'bg-yellow-50 border border-yellow-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center gap-3 mb-4">
            {decisionIcon[threshold.decision]}
            <h2 className="text-xl font-bold">{threshold.decision}</h2>
            <span className="text-sm text-gray-500">({threshold.total_interviews} interviews)</span>
          </div>
          <div className="grid md:grid-cols-4 gap-3">
            {threshold.thresholds.map((t) => (
              <div key={t.metric} className={`rounded-lg p-3 ${t.met ? 'bg-green-100' : 'bg-red-100'}`}>
                <p className="text-xs font-medium text-gray-700">{t.metric}</p>
                <p className="text-lg font-bold">{t.actual}</p>
                <p className="text-xs text-gray-500">Required: {t.required}</p>
                <span className={`text-xs font-medium ${t.met ? 'text-green-700' : 'text-red-700'}`}>
                  {t.met ? '✓ Met' : '✗ Not met'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Interview table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-3 py-2">#</th>
                <th className="text-left px-3 py-2">Participant</th>
                <th className="text-left px-3 py-2">Business</th>
                <th className="text-left px-3 py-2">Date</th>
                <th className="text-left px-3 py-2">Method</th>
                <th className="text-left px-3 py-2">Last Incident</th>
                <th className="text-left px-3 py-2">Cost/Freq</th>
                <th className="text-left px-3 py-2">Workaround</th>
                <th className="text-left px-3 py-2">Photos</th>
                <th className="text-left px-3 py-2">Pay?</th>
                <th className="px-3 py-2"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {interviews.map((iv, idx) => (
                <InterviewRow key={iv.id} interview={iv} index={idx + 1} isEditing={editing === iv.id}
                  onEdit={() => setEditing(iv.id)} onSave={(data) => saveInterview(iv.id, data)} />
              ))}
              {interviews.length === 0 && (
                <tr><td colSpan="11" className="text-center py-8 text-gray-400">No interviews recorded yet. Add one to start.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function InterviewRow({ interview, index, isEditing, onEdit, onSave }) {
  const [form, setForm] = useState(interview);

  if (!isEditing) {
    return (
      <tr className="hover:bg-gray-50 cursor-pointer" onClick={onEdit}>
        <td className="px-3 py-2">{index}</td>
        <td className="px-3 py-2">{interview.participant_role || '—'}</td>
        <td className="px-3 py-2">{interview.business || '—'}</td>
        <td className="px-3 py-2">{interview.interview_date || '—'}</td>
        <td className="px-3 py-2">{interview.method || '—'}</td>
        <td className="px-3 py-2">{interview.last_defect_incident || '—'}</td>
        <td className="px-3 py-2">{interview.cost_frequency || '—'}</td>
        <td className="px-3 py-2">{interview.workaround || '—'}</td>
        <td className="px-3 py-2">{interview.photos_sent || '—'}</td>
        <td className="px-3 py-2">{interview.would_pay || '—'}</td>
        <td className="px-3 py-2"></td>
      </tr>
    );
  }

  const fields = [
    { key: 'participant_role', label: 'Role' },
    { key: 'business', label: 'Business' },
    { key: 'interview_date', label: 'Date' },
    { key: 'method', label: 'Method' },
    { key: 'last_defect_incident', label: 'Incident' },
    { key: 'cost_frequency', label: 'Cost/Freq' },
    { key: 'workaround', label: 'Workaround' },
    { key: 'photos_sent', label: 'Photos' },
    { key: 'would_pay', label: 'Pay?' },
  ];

  return (
    <tr className="bg-blue-50">
      <td className="px-3 py-2">{index}</td>
      {fields.map((f) => (
        <td key={f.key} className="px-1 py-1">
          <input
            value={form[f.key] || ''}
            onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
            placeholder={f.label}
            className="w-full border rounded px-2 py-1 text-xs"
          />
        </td>
      ))}
      <td className="px-3 py-2">
        <button onClick={() => onSave(form)} className="text-blue-600 hover:text-blue-800">
          <Save size={16} />
        </button>
      </td>
    </tr>
  );
}
