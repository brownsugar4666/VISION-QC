import { useState, useEffect } from 'react';
import api from '../api';
import { RefreshCw, RotateCcw, Loader2 } from 'lucide-react';

export default function Models() {
  const [versions, setVersions] = useState([]);
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');
  const [retraining, setRetraining] = useState(false);
  const [trainResult, setTrainResult] = useState(null);

  useEffect(() => {
    api.get('/plants/').then((r) => setPlants(r.data));
    loadVersions();
  }, []);

  const loadVersions = (pid) => {
    const params = pid ? `?plant_id=${pid}` : '';
    api.get(`/models/versions${params}`).then((r) => setVersions(r.data));
  };

  const retrain = async () => {
    if (!plantId) return;
    setRetraining(true);
    setTrainResult(null);
    try {
      const r = await api.post(`/models/retrain?plant_id=${plantId}`);
      setTrainResult(r.data);
      loadVersions(plantId);
    } finally {
      setRetraining(false);
    }
  };

  const rollback = async (versionId) => {
    await api.post(`/models/rollback/${versionId}`);
    loadVersions(plantId);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Model Management</h1>

      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="font-semibold mb-4">Retrain Model</h2>
        <div className="flex items-center gap-3 flex-wrap">
          <select value={plantId} onChange={(e) => { setPlantId(e.target.value); loadVersions(e.target.value); }}
            className="border rounded-lg px-3 py-2 text-sm">
            <option value="">Baseline (all plants)</option>
            {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
          <button onClick={retrain} disabled={retraining}
            className="flex items-center gap-2 bg-[#1a365d] text-white px-4 py-2 rounded-lg text-sm hover:bg-[#2c5282] disabled:opacity-50">
            {retraining ? <Loader2 size={16} className="animate-spin" /> : <RefreshCw size={16} />}
            {retraining ? 'Training...' : 'Retrain'}
          </button>
        </div>
        {trainResult && (
          <div className={`mt-4 p-3 rounded-lg text-sm ${trainResult.status === 'completed' ? 'bg-green-50' : 'bg-red-50'}`}>
            <p className="font-medium">{trainResult.status === 'completed' ? 'Training completed!' : 'Training failed'}</p>
            {trainResult.stdout && <pre className="mt-2 text-xs overflow-x-auto whitespace-pre-wrap max-h-48">{trainResult.stdout}</pre>}
            {trainResult.stderr && <pre className="mt-2 text-xs text-red-600 overflow-x-auto whitespace-pre-wrap max-h-48">{trainResult.stderr}</pre>}
          </div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="text-left px-4 py-3">Version</th>
              <th className="text-left px-4 py-3">Plant</th>
              <th className="text-right px-4 py-3">Accuracy</th>
              <th className="text-right px-4 py-3">Precision</th>
              <th className="text-right px-4 py-3">Recall</th>
              <th className="text-center px-4 py-3">Active</th>
              <th className="text-center px-4 py-3">Confusion Matrix</th>
              <th className="text-right px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {versions.map((v) => {
              let cm = [];
              try { cm = JSON.parse(v.confusion_matrix_json); } catch {}
              return (
                <tr key={v.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{v.version}</td>
                  <td className="px-4 py-3 text-gray-500">{v.plant_id ? `Plant #${v.plant_id}` : 'Baseline'}</td>
                  <td className="px-4 py-3 text-right">{v.accuracy.toFixed(1)}%</td>
                  <td className="px-4 py-3 text-right">{v.precision.toFixed(3)}</td>
                  <td className="px-4 py-3 text-right">{v.recall.toFixed(3)}</td>
                  <td className="px-4 py-3 text-center">
                    {v.is_active ? <span className="bg-green-100 text-green-800 px-2 py-0.5 text-xs rounded">Active</span> : '–'}
                  </td>
                  <td className="px-4 py-3">
                    {cm.length === 2 && (
                      <div className="text-xs text-center">
                        <div className="grid grid-cols-3 gap-px">
                          <div></div><div className="text-gray-500">OK</div><div className="text-gray-500">Def</div>
                          <div className="text-gray-500">OK</div><div className="bg-green-100 px-1">{cm[0][0]}</div><div className="bg-red-50 px-1">{cm[0][1]}</div>
                          <div className="text-gray-500">Def</div><div className="bg-red-50 px-1">{cm[1][0]}</div><div className="bg-green-100 px-1">{cm[1][1]}</div>
                        </div>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {!v.is_active && (
                      <button onClick={() => rollback(v.id)} className="text-blue-600 hover:text-blue-800" title="Rollback to this version">
                        <RotateCcw size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
