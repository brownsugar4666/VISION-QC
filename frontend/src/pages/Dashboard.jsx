import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle, Package } from 'lucide-react';

const COLORS = ['#e53e3e', '#dd6b20', '#d69e2e', '#38a169', '#3182ce', '#805ad5'];

export default function Dashboard() {
  const { user } = useAuth();
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState(null);
  const [lines, setLines] = useState([]);
  const [lineId, setLineId] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.get('/plants/').then((r) => {
      setPlants(r.data);
      if (r.data.length > 0) setPlantId(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (plantId) {
      api.get(`/plants/${plantId}/lines`).then((r) => setLines(r.data));
    }
  }, [plantId]);

  useEffect(() => {
    if (!plantId) return;
    const params = new URLSearchParams({ plant_id: plantId });
    if (lineId) params.set('line_id', lineId);
    if (dateFrom) params.set('date_from', dateFrom);
    if (dateTo) params.set('date_to', dateTo);
    api.get(`/dashboard/stats?${params}`).then((r) => setStats(r.data));
  }, [plantId, lineId, dateFrom, dateTo]);

  if (!stats) return <div className="text-center py-12 text-gray-500">Loading dashboard...</div>;

  const defectTypeData = Object.entries(stats.by_defect_type).map(([name, count]) => ({ name, value: count }));

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex flex-wrap gap-2">
          <select value={plantId || ''} onChange={(e) => setPlantId(Number(e.target.value))}
            className="border rounded-lg px-3 py-1.5 text-sm">
            {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <select value={lineId} onChange={(e) => setLineId(e.target.value)}
            className="border rounded-lg px-3 py-1.5 text-sm">
            <option value="">All Lines</option>
            {lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
          </select>
          <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
            className="border rounded-lg px-3 py-1.5 text-sm" />
          <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
            className="border rounded-lg px-3 py-1.5 text-sm" />
          <button onClick={() => {
            api.get(`/dashboard/export-csv?plant_id=${plantId}`, { responseType: 'blob' })
              .then((r) => {
                const url = URL.createObjectURL(r.data);
                const a = document.createElement('a');
                a.href = url; a.download = 'visionqc_export.csv'; a.click();
              });
          }} className="bg-[#1a365d] text-white px-4 py-1.5 rounded-lg text-sm hover:bg-[#2c5282]">
            Export CSV
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={Package} label="Total Batches" value={stats.total_batches} color="blue" />
        <StatCard icon={CheckCircle} label="Passed" value={stats.total_passed} color="green" />
        <StatCard icon={AlertTriangle} label="Defective" value={stats.total_defective} color="red" />
        <StatCard icon={TrendingUp} label="Defect Rate" value={`${stats.overall_defect_rate}%`} color="orange" />
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Defect Rate Trend</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={stats.daily_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="defect_rate" stroke="#e53e3e" strokeWidth={2} name="Defect Rate %" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Defects by Shift</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={stats.by_shift}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="shift" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="defective" fill="#e53e3e" name="Defective" radius={[4, 4, 0, 0]} />
              <Bar dataKey="total" fill="#3182ce" name="Total" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Defects by Part Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={stats.by_part} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" tick={{ fontSize: 11 }} />
              <YAxis dataKey="part_type" type="category" tick={{ fontSize: 11 }} width={100} />
              <Tooltip />
              <Bar dataKey="defect_rate" fill="#dd6b20" name="Defect Rate %" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow p-4">
          <h3 className="font-semibold text-gray-700 mb-3">Defect Types</h3>
          {defectTypeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={defectTypeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {defectTypeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-gray-400 text-center py-12">No defect data</p>}
        </div>
      </div>

      {/* Highlights */}
      <div className="grid md:grid-cols-2 gap-4">
        {stats.worst_shift && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <h4 className="font-semibold text-red-800">Worst Shift</h4>
            <p className="text-red-600">Shift {stats.worst_shift.shift}: {stats.worst_shift.defect_rate}% defect rate ({stats.worst_shift.defective} defects)</p>
          </div>
        )}
        {stats.worst_part && (
          <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
            <h4 className="font-semibold text-orange-800">Worst Part Type</h4>
            <p className="text-orange-600">{stats.worst_part.part_type}: {stats.worst_part.defect_rate}% defect rate ({stats.worst_part.defective} defects)</p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    orange: 'bg-orange-50 text-orange-700',
  };
  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`p-2 rounded-lg ${colors[color]}`}><Icon size={18} /></div>
        <span className="text-xs text-gray-500">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
