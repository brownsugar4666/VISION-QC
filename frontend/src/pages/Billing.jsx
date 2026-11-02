import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function Billing() {
  const { user } = useAuth();
  const [plants, setPlants] = useState([]);
  const [plantId, setPlantId] = useState('');
  const [invoice, setInvoice] = useState(null);
  const [economics, setEconomics] = useState(null);
  const [numLines, setNumLines] = useState(3);

  useEffect(() => {
    api.get('/plants/').then((r) => {
      setPlants(r.data);
      const pid = user?.plant_id || (r.data.length > 0 ? r.data[0].id : '');
      setPlantId(pid);
    });
  }, []);

  useEffect(() => {
    if (!plantId) return;
    api.get(`/billing/invoice/${plantId}`).then((r) => setInvoice(r.data));
  }, [plantId]);

  useEffect(() => {
    api.get(`/billing/unit-economics?num_lines=${numLines}`).then((r) => setEconomics(r.data));
  }, [numLines]);

  const chartData = invoice ? [
    { name: 'Per-Batch', amount: invoice.invoice.batch_fee_total },
    { name: 'Monthly Plan', amount: invoice.invoice.monthly_plan_total },
  ] : [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Billing & Plans</h1>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Invoice */}
        <div className="bg-white rounded-xl shadow p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg">Monthly Invoice</h2>
            {user?.role === 'admin' && (
              <select value={plantId} onChange={(e) => setPlantId(e.target.value)} className="border rounded-lg px-3 py-1.5 text-sm">
                {plants.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            )}
          </div>
          {invoice && (
            <>
              <div className="space-y-2 text-sm">
                <Row label="Month" value={invoice.invoice.month} />
                <Row label="Batches this month" value={invoice.invoice.batch_count} />
                <Row label={`Batch fee (${invoice.invoice.batch_count} × ₹500)`} value={`₹${invoice.invoice.batch_fee_total.toLocaleString('en-IN')}`} />
                <Row label={`Monthly plan (${invoice.invoice.monthly_plan_lines} lines × ₹15,000)`} value={`₹${invoice.invoice.monthly_plan_total.toLocaleString('en-IN')}`} />
                {invoice.invoice.setup_fee > 0 && <Row label="Setup fee" value={`₹${invoice.invoice.setup_fee.toLocaleString('en-IN')}`} />}
                <div className="border-t pt-2 flex justify-between font-bold">
                  <span>Total</span>
                  <span>₹{invoice.invoice.total_amount.toLocaleString('en-IN')}</span>
                </div>
              </div>
              <div className={`p-3 rounded-lg text-sm ${invoice.invoice.cheaper_plan === 'monthly' ? 'bg-blue-50 text-blue-800' : 'bg-green-50 text-green-800'}`}>
                {invoice.recommendation}
              </div>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip formatter={(v) => `₹${v.toLocaleString('en-IN')}`} />
                  <Bar dataKey="amount" fill="#3182ce" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </>
          )}
        </div>

        {/* Unit Economics */}
        <div className="bg-white rounded-xl shadow p-6 space-y-4">
          <h2 className="font-semibold text-lg">Unit Economics</h2>
          <p className="text-xs text-gray-500">(From BMC: fixed ₹30,000/mo, variable ₹3,500/line/mo)</p>
          <div className="flex items-center gap-3">
            <label className="text-sm">Lines:</label>
            <input type="range" min="1" max="20" value={numLines} onChange={(e) => setNumLines(Number(e.target.value))}
              className="flex-1" />
            <span className="font-bold text-lg w-8 text-center">{numLines}</span>
          </div>
          {economics && (
            <div className="space-y-2 text-sm">
              <Row label="Revenue/line/month" value={`₹${economics.revenue_per_line_monthly.toLocaleString('en-IN')}`} />
              <Row label="Variable cost/line/month" value={`₹${economics.variable_per_line_monthly.toLocaleString('en-IN')}`} />
              <Row label="Contribution/line" value={`₹${economics.contribution_per_line.toLocaleString('en-IN')} (${economics.contribution_margin_pct}%)`} />
              <Row label="Fixed cost/month" value={`₹${economics.fixed_cost_monthly.toLocaleString('en-IN')}`} />
              <div className="border-t pt-2">
                <Row label="Break-even" value={`${economics.breakeven_lines} lines`} bold />
              </div>
              <div className="border-t pt-2">
                <h4 className="font-medium mb-1">Scenario ({numLines} lines)</h4>
                <Row label="Total revenue" value={`₹${economics.scenario.total_revenue.toLocaleString('en-IN')}`} />
                <Row label="Total cost" value={`₹${economics.scenario.total_cost.toLocaleString('en-IN')}`} />
                <Row label="Gross profit" value={`₹${economics.scenario.gross_profit.toLocaleString('en-IN')}`} bold />
                <Row label="Gross margin" value={`${economics.scenario.gross_margin_pct}%`} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Pricing table */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="font-semibold text-lg mb-4">Pricing Plans</h2>
        <div className="grid md:grid-cols-3 gap-4">
          <PricingCard title="Per Batch" price="₹500" unit="per batch (up to 200 parts)" features={['Pay as you go', 'No commitment', 'Same-day report']} />
          <PricingCard title="Monthly Plan" price="₹15,000" unit="per line / month" features={['Unlimited batches', 'Priority support', 'Dashboard access']} highlight />
          <PricingCard title="Setup Fee" price="₹10,000" unit="one-time" features={['Camera setup', 'Model training', 'Staff training']} />
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, bold }) {
  return (
    <div className={`flex justify-between ${bold ? 'font-bold' : ''}`}>
      <span className="text-gray-600">{label}</span>
      <span>{value}</span>
    </div>
  );
}

function PricingCard({ title, price, unit, features, highlight }) {
  return (
    <div className={`rounded-xl p-5 ${highlight ? 'bg-[#1a365d] text-white' : 'bg-gray-50'}`}>
      <h3 className={`font-bold text-lg ${highlight ? '' : 'text-gray-900'}`}>{title}</h3>
      <p className="text-2xl font-bold mt-2">{price}</p>
      <p className={`text-xs mt-1 ${highlight ? 'text-blue-200' : 'text-gray-500'}`}>{unit}</p>
      <ul className="mt-4 space-y-2">
        {features.map((f) => (
          <li key={f} className={`text-sm flex items-center gap-2 ${highlight ? 'text-blue-100' : 'text-gray-600'}`}>
            <span>•</span> {f}
          </li>
        ))}
      </ul>
    </div>
  );
}
