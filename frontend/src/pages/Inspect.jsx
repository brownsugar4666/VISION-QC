import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { Camera, Upload, Loader2 } from 'lucide-react';

export default function Inspect() {
  const { user } = useAuth();
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');
  const [lines, setLines] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [partTypes, setPartTypes] = useState([]);
  const [lineId, setLineId] = useState('');
  const [shiftId, setShiftId] = useState('');
  const [partTypeId, setPartTypeId] = useState('');
  const [concierge, setConcierge] = useState(false);
  const [batch, setBatch] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);
  const fileRef = useRef();

  useEffect(() => {
    api.get('/plants/').then((r) => {
      setPlants(r.data);
      const pid = user?.plant_id || (r.data.length > 0 ? r.data[0].id : '');
      setPlantId(pid);
    });
  }, []);

  useEffect(() => {
    if (!plantId) return;
    api.get(`/plants/${plantId}/lines`).then((r) => setLines(r.data));
    api.get(`/plants/${plantId}/shifts`).then((r) => setShifts(r.data));
    api.get(`/plants/${plantId}/part-types`).then((r) => setPartTypes(r.data));
  }, [plantId]);

  const startBatch = async () => {
    const r = await api.post('/inspections/batches', {
      plant_id: Number(plantId), line_id: Number(lineId),
      shift_id: Number(shiftId), part_type_id: Number(partTypeId),
      concierge_mode: concierge,
    });
    setBatch(r.data);
    setResults([]);
    setSummary(null);
  };

  const uploadFiles = async (files) => {
    if (!batch || !files.length) return;
    setUploading(true);
    const form = new FormData();
    for (const f of files) form.append('files', f);
    try {
      const r = await api.post(`/inspections/batches/${batch.id}/upload`, form);
      setResults((prev) => [...prev, ...r.data.results]);
      const s = await api.get(`/inspections/batches/${batch.id}/summary`);
      setSummary(s.data);
    } finally {
      setUploading(false);
    }
  };

  const completeBatch = async () => {
    await api.post(`/inspections/batches/${batch.id}/complete`);
    setBatch({ ...batch, status: 'completed' });
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900">Batch Inspection</h1>

      {!batch ? (
        <div className="bg-white rounded-xl shadow p-6 space-y-4">
          <h2 className="font-semibold text-lg">Start New Batch</h2>
          <div className="grid grid-cols-2 gap-4">
            {user?.role === 'admin' && (
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Plant</label>
                <select value={plantId} onChange={(e) => setPlantId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                  {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Line</label>
              <select value={lineId} onChange={(e) => setLineId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="">Select line</option>
                {lines.map((l) => <option key={l.id} value={l.id}>{l.name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Shift</label>
              <select value={shiftId} onChange={(e) => setShiftId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="">Select shift</option>
                {shifts.map((s) => <option key={s.id} value={s.id}>Shift {s.name} ({s.start_time}–{s.end_time})</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Part Type</label>
              <select value={partTypeId} onChange={(e) => setPartTypeId(e.target.value)} className="w-full border rounded-lg px-3 py-2 text-sm">
                <option value="">Select part</option>
                {partTypes.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="concierge" checked={concierge} onChange={(e) => setConcierge(e.target.checked)} />
              <label htmlFor="concierge" className="text-sm text-gray-700">Concierge Mode (human review all)</label>
            </div>
          </div>
          <button onClick={startBatch} disabled={!lineId || !shiftId || !partTypeId}
            className="bg-[#1a365d] text-white px-6 py-2.5 rounded-lg font-medium hover:bg-[#2c5282] disabled:opacity-50 transition-colors">
            Start Batch
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow p-4 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="font-semibold">Batch #{batch.id}</p>
              <p className="text-sm text-gray-500">
                Status: <span className={batch.status === 'completed' ? 'text-green-600' : 'text-blue-600'}>{batch.status}</span>
                {concierge && <span className="ml-2 bg-yellow-100 text-yellow-800 text-xs px-2 py-0.5 rounded">Concierge</span>}
              </p>
            </div>
            {batch.status !== 'completed' && (
              <div className="flex gap-2">
                <input type="file" ref={fileRef} multiple accept="image/*" onChange={(e) => uploadFiles(e.target.files)} className="hidden" />
                <button onClick={() => fileRef.current?.click()} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700">
                  <Upload size={16} /> Upload Images
                </button>
                <input type="file" accept="image/*" capture="environment" onChange={(e) => uploadFiles(e.target.files)}
                  className="hidden" id="camera-input" />
                <label htmlFor="camera-input" className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm cursor-pointer hover:bg-green-700">
                  <Camera size={16} /> Capture
                </label>
                <button onClick={completeBatch} className="bg-gray-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-gray-700">
                  Complete Batch
                </button>
              </div>
            )}
          </div>

          {uploading && (
            <div className="flex items-center gap-2 text-blue-600">
              <Loader2 size={18} className="animate-spin" /> Processing images...
            </div>
          )}

          {summary && (
            <div className="bg-white rounded-xl shadow p-4">
              <h3 className="font-semibold mb-2">Batch Summary</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xl font-bold">{summary.total}</p>
                  <p className="text-xs text-gray-500">Total</p>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <p className="text-xl font-bold text-green-700">{summary.passed}</p>
                  <p className="text-xs text-gray-500">Passed</p>
                </div>
                <div className="bg-red-50 rounded-lg p-3">
                  <p className="text-xl font-bold text-red-700">{summary.defective}</p>
                  <p className="text-xs text-gray-500">Defective</p>
                </div>
                <div className="bg-yellow-50 rounded-lg p-3">
                  <p className="text-xl font-bold text-yellow-700">{summary.review_pending}</p>
                  <p className="text-xs text-gray-500">In Review</p>
                </div>
                <div className="bg-orange-50 rounded-lg p-3">
                  <p className="text-xl font-bold text-orange-700">{summary.defect_rate}%</p>
                  <p className="text-xs text-gray-500">Defect Rate</p>
                </div>
              </div>
            </div>
          )}

          {results.length > 0 && (
            <div className="bg-white rounded-xl shadow p-4">
              <h3 className="font-semibold mb-3">Results ({results.length} images)</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {results.map((r) => (
                  <div key={r.id} className={`border rounded-lg overflow-hidden ${r.result === 'ok' ? 'border-green-300' : r.result === 'defective' ? 'border-red-300' : 'border-yellow-300'}`}>
                    <img src={`/${r.image_path}`} alt="" className="w-full h-32 object-cover" />
                    {r.gradcam_path && (
                      <img src={`/${r.gradcam_path}`} alt="Grad-CAM" className="w-full h-32 object-cover border-t" />
                    )}
                    <div className="p-2">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                        r.result === 'ok' ? 'bg-green-100 text-green-800' :
                        r.result === 'defective' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {r.result.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-500 ml-2">{(r.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
