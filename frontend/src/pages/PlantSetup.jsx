import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { Plus } from 'lucide-react';

export default function PlantSetup() {
  const { user } = useAuth();
  const [plants, setPlants] = useState([]);
  const [selected, setSelected] = useState(null);
  const [lines, setLines] = useState([]);
  const [shifts, setShifts] = useState([]);
  const [partTypes, setPartTypes] = useState([]);
  const [defectTypes, setDefectTypes] = useState([]);
  const [newPlant, setNewPlant] = useState({ name: '', location: '' });

  const loadPlants = async () => {
    const r = await api.get('/plants/');
    setPlants(r.data);
    if (r.data.length > 0 && !selected) setSelected(r.data[0]);
  };

  useEffect(() => { loadPlants(); }, []);

  useEffect(() => {
    if (!selected) return;
    api.get(`/plants/${selected.id}/lines`).then((r) => setLines(r.data));
    api.get(`/plants/${selected.id}/shifts`).then((r) => setShifts(r.data));
    api.get(`/plants/${selected.id}/part-types`).then((r) => setPartTypes(r.data));
    api.get(`/plants/${selected.id}/defect-types`).then((r) => setDefectTypes(r.data));
  }, [selected]);

  const createPlant = async () => {
    if (!newPlant.name) return;
    const r = await api.post('/plants/', newPlant);
    setNewPlant({ name: '', location: '' });
    loadPlants();
    setSelected(r.data);
  };

  const addItem = async (endpoint, data, reload) => {
    await api.post(`/plants/${selected.id}/${endpoint}`, data);
    reload();
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Plant Setup</h1>

      {/* Create plant */}
      {user?.role === 'admin' && (
        <div className="bg-white rounded-xl shadow p-4">
          <h2 className="font-semibold mb-3">Create New Plant</h2>
          <div className="flex gap-2 flex-wrap">
            <input placeholder="Plant name" value={newPlant.name} onChange={(e) => setNewPlant({ ...newPlant, name: e.target.value })}
              className="border rounded-lg px-3 py-2 text-sm flex-1" />
            <input placeholder="Location" value={newPlant.location} onChange={(e) => setNewPlant({ ...newPlant, location: e.target.value })}
              className="border rounded-lg px-3 py-2 text-sm flex-1" />
            <button onClick={createPlant} className="bg-[#1a365d] text-white px-4 py-2 rounded-lg text-sm hover:bg-[#2c5282]">Create</button>
          </div>
        </div>
      )}

      {/* Plant selector */}
      <div className="flex gap-2 flex-wrap">
        {plants.map((p) => (
          <button key={p.id} onClick={() => setSelected(p)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${selected?.id === p.id ? 'bg-[#1a365d] text-white' : 'bg-white text-gray-700 shadow'}`}>
            {p.name}
          </button>
        ))}
      </div>

      {selected && (
        <div className="grid md:grid-cols-2 gap-6">
          <SetupSection title="Lines" items={lines} fields={[{ key: 'name', label: 'Line name' }]}
            onAdd={(d) => addItem('lines', d, () => api.get(`/plants/${selected.id}/lines`).then((r) => setLines(r.data)))} />
          <SetupSection title="Shifts" items={shifts} fields={[
            { key: 'name', label: 'Shift (e.g. A)' },
            { key: 'start_time', label: 'Start (HH:MM)' },
            { key: 'end_time', label: 'End (HH:MM)' },
          ]} display={(s) => `${s.name}: ${s.start_time}–${s.end_time}`}
            onAdd={(d) => addItem('shifts', d, () => api.get(`/plants/${selected.id}/shifts`).then((r) => setShifts(r.data)))} />
          <SetupSection title="Part Types" items={partTypes} fields={[
            { key: 'name', label: 'Part name' },
            { key: 'description', label: 'Description' },
          ]} display={(p) => `${p.name}${p.description ? ` — ${p.description}` : ''}`}
            onAdd={(d) => addItem('part-types', d, () => api.get(`/plants/${selected.id}/part-types`).then((r) => setPartTypes(r.data)))} />
          <SetupSection title="Defect Types" items={defectTypes} fields={[
            { key: 'name', label: 'Defect name' },
            { key: 'description', label: 'Description' },
          ]} display={(d) => `${d.name}${d.description ? ` — ${d.description}` : ''}`}
            onAdd={(d) => addItem('defect-types', d, () => api.get(`/plants/${selected.id}/defect-types`).then((r) => setDefectTypes(r.data)))} />
        </div>
      )}
    </div>
  );
}

function SetupSection({ title, items, fields, display, onAdd }) {
  const [form, setForm] = useState({});
  const [adding, setAdding] = useState(false);

  const submit = async () => {
    await onAdd(form);
    setForm({});
    setAdding(false);
  };

  return (
    <div className="bg-white rounded-xl shadow p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">{title} ({items.length})</h3>
        <button onClick={() => setAdding(!adding)} className="text-blue-600 hover:text-blue-800">
          <Plus size={18} />
        </button>
      </div>
      {adding && (
        <div className="flex gap-2 mb-3 flex-wrap">
          {fields.map((f) => (
            <input key={f.key} placeholder={f.label} value={form[f.key] || ''}
              onChange={(e) => setForm({ ...form, [f.key]: e.target.value })}
              className="border rounded-lg px-2 py-1.5 text-sm flex-1 min-w-[120px]" />
          ))}
          <button onClick={submit} className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm">Add</button>
        </div>
      )}
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.id} className="text-sm text-gray-700 py-1 border-b border-gray-100 last:border-0">
            {display ? display(item) : item.name}
          </li>
        ))}
      </ul>
    </div>
  );
}
