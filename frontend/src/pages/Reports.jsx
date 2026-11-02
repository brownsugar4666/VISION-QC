import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { FileDown, MessageCircle } from 'lucide-react';

export default function Reports() {
  const { user } = useAuth();
  const [batches, setBatches] = useState([]);
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');
  const [waMessage, setWaMessage] = useState(null);

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

  const downloadPdf = (batchId) => {
    api.get(`/reports/batch/${batchId}/pdf`, { responseType: 'blob' }).then((r) => {
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url; a.download = `visionqc_batch_${batchId}.pdf`; a.click();
    });
  };

  const getWhatsApp = async (batchId) => {
    const r = await api.get(`/reports/batch/${batchId}/whatsapp`);
    setWaMessage(r.data);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        {user?.role === 'admin' && (
          <select value={plantId} onChange={(e) => setPlantId(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
            {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        )}
      </div>

      {waMessage && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <h3 className="font-semibold text-green-800 mb-2 flex items-center gap-2">
            <MessageCircle size={18} /> WhatsApp Message
          </h3>
          <pre className="text-sm text-green-900 whitespace-pre-wrap bg-white rounded-lg p-3 border">{waMessage.message}</pre>
          <a href={waMessage.whatsapp_link} target="_blank" rel="noreferrer"
            className="inline-block mt-3 bg-green-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-green-700">
            Share on WhatsApp
          </a>
          <button onClick={() => setWaMessage(null)} className="ml-2 text-sm text-green-600 hover:underline">Close</button>
        </div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-3">Batch</th>
              <th className="text-left px-4 py-3">Date</th>
              <th className="text-right px-4 py-3">Images</th>
              <th className="text-right px-4 py-3">Defect Rate</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {batches.filter((b) => b.status === 'completed').map((b) => (
              <tr key={b.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">#{b.id}</td>
                <td className="px-4 py-3 text-gray-500">{new Date(b.created_at).toLocaleString('en-IN')}</td>
                <td className="px-4 py-3 text-right">{b.total_images}</td>
                <td className="px-4 py-3 text-right">
                  {b.total_images > 0 ? `${(b.defective_count / b.total_images * 100).toFixed(1)}%` : '–'}
                </td>
                <td className="px-4 py-3 text-right">
                  <button onClick={() => downloadPdf(b.id)} className="text-blue-600 hover:text-blue-800 mr-3" title="Download PDF">
                    <FileDown size={18} />
                  </button>
                  <button onClick={() => getWhatsApp(b.id)} className="text-green-600 hover:text-green-800" title="WhatsApp">
                    <MessageCircle size={18} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
