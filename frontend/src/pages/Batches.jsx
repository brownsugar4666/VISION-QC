import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';

export default function Batches() {
  const { user } = useAuth();
  const [batches, setBatches] = useState([]);
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');

  useEffect(() => {
    api.get('/plants/').then((r) => {
      setPlants(r.data);
      const pid = user?.plant_id || (r.data.length > 0 ? r.data[0].id : '');
      setPlantId(pid);
    });
  }, []);

  useEffect(() => {
    if (!plantId) return;
    api.get(`/inspections/batches?plant_id=${plantId}`).then((r) => setBatches(r.data));
  }, [plantId]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Batches</h1>
        {user?.role === 'admin' && (
          <select value={plantId} onChange={(e) => setPlantId(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
            {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        )}
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-4 py-3">ID</th>
                <th className="text-left px-4 py-3">Date</th>
                <th className="text-left px-4 py-3">Status</th>
                <th className="text-right px-4 py-3">Total</th>
                <th className="text-right px-4 py-3">Passed</th>
                <th className="text-right px-4 py-3">Defective</th>
                <th className="text-right px-4 py-3">Rate</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {batches.map((b) => (
                <tr key={b.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">#{b.id}</td>
                  <td className="px-4 py-3 text-gray-500">{new Date(b.created_at).toLocaleString('en-IN')}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      b.status === 'completed' ? 'bg-green-100 text-green-800' :
                      b.status === 'reviewed' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>{b.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">{b.total_images}</td>
                  <td className="px-4 py-3 text-right text-green-600">{b.passed_count}</td>
                  <td className="px-4 py-3 text-right text-red-600">{b.defective_count}</td>
                  <td className="px-4 py-3 text-right font-medium">
                    {b.total_images > 0 ? `${(b.defective_count / b.total_images * 100).toFixed(1)}%` : '–'}
                  </td>
                </tr>
              ))}
              {batches.length === 0 && (
                <tr><td colSpan="7" className="text-center py-8 text-gray-400">No batches yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
