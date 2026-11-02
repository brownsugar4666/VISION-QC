import { useState, useEffect } from 'react';
import api from '../api';
import { CheckCircle, XCircle } from 'lucide-react';

export default function ReviewQueue() {
  const [queue, setQueue] = useState([]);
  const [defectTypes, setDefectTypes] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadQueue = async () => {
    setLoading(true);
    const r = await api.get('/review/queue');
    setQueue(r.data);
    setLoading(false);
  };

  useEffect(() => { loadQueue(); }, []);

  const handleReview = async (inspectionId, result, defectTypeId = null) => {
    await api.post(`/review/${inspectionId}`, {
      result,
      defect_type_id: defectTypeId,
      notes: '',
    });
    loadQueue();
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading review queue...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
        <span className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-sm font-medium">
          {queue.length} pending
        </span>
      </div>

      {queue.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-12 text-center">
          <CheckCircle size={48} className="mx-auto text-green-500 mb-3" />
          <p className="text-gray-500">No items pending review</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {queue.map((item) => (
            <ReviewCard key={item.id} item={item} onReview={handleReview} />
          ))}
        </div>
      )}
    </div>
  );
}

function ReviewCard({ item, onReview }) {
  const [selectedDefect, setSelectedDefect] = useState('');
  const [defectTypes, setDefectTypes] = useState([]);

  useEffect(() => {
    api.get(`/inspections/batches/${item.batch_id}`).then((r) => {
      api.get(`/plants/${r.data.plant_id}/defect-types`).then((d) => setDefectTypes(d.data));
    });
  }, [item.batch_id]);

  return (
    <div className="bg-white rounded-xl shadow overflow-hidden">
      <img src={`/${item.image_path}`} alt="" className="w-full h-48 object-cover" />
      {item.gradcam_path && (
        <img src={`/${item.gradcam_path}`} alt="Grad-CAM" className="w-full h-48 object-cover border-t" />
      )}
      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-500">ID #{item.id} | Batch #{item.batch_id}</span>
          <span className="text-xs text-gray-500">Conf: {(item.confidence * 100).toFixed(0)}%</span>
        </div>
        <select value={selectedDefect} onChange={(e) => setSelectedDefect(e.target.value)}
          className="w-full border rounded-lg px-3 py-1.5 text-sm">
          <option value="">No defect type</option>
          {defectTypes.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <div className="flex gap-2">
          <button onClick={() => onReview(item.id, 'ok')}
            className="flex-1 flex items-center justify-center gap-1 bg-green-600 text-white py-2 rounded-lg text-sm hover:bg-green-700">
            <CheckCircle size={16} /> OK
          </button>
          <button onClick={() => onReview(item.id, 'defective', selectedDefect ? Number(selectedDefect) : null)}
            className="flex-1 flex items-center justify-center gap-1 bg-red-600 text-white py-2 rounded-lg text-sm hover:bg-red-700">
            <XCircle size={16} /> Defective
          </button>
        </div>
      </div>
    </div>
  );
}
