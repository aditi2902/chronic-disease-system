import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ReferenceLine, ResponsiveContainer
} from 'recharts';
import { format } from 'date-fns';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  const glucose = payload[0]?.value;
  const color =
    glucose > 300 ? '#ef4444' :
    glucose > 180 ? '#f59e0b' :
    '#10b981';
  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">{label}</p>
      <p style={{ color }} className="tooltip-glucose">
        {glucose?.toFixed(1)} mg/dL
      </p>
      {payload[1] && (
        <p className="tooltip-weight">Weight: {payload[1].value} kg</p>
      )}
    </div>
  );
};

export default function GlucoseChart({ readings, height = 300 }) {
  if (!readings || readings.length === 0) {
    return (
      <div className="chart-empty">
        <span>No readings yet</span>
      </div>
    );
  }

  const data = readings.map((r) => ({
    date: format(new Date(r.date), 'MMM d'),
    glucose: r.glucose_mg_dl,
    weight: r.weight_kg,
    medication: r.medication_taken,
  }));

  const minGlucose = Math.min(...data.map(d => d.glucose));
  const maxGlucose = Math.max(...data.map(d => d.glucose));
  const yMin = Math.max(0, minGlucose - 30);
  const yMax = maxGlucose + 40;

  // Color glucose line based on values
  const getLineColor = () => {
    if (maxGlucose > 300) return '#ef4444';
    if (maxGlucose > 180) return '#f59e0b';
    return '#10b981';
  };

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="glucoseGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={getLineColor()} stopOpacity={0.3} />
            <stop offset="95%" stopColor={getLineColor()} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis
          dataKey="date"
          tick={{ fill: '#94a3b8', fontSize: 12 }}
          axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
          tickLine={false}
        />
        <YAxis
          domain={[yMin, yMax]}
          tick={{ fill: '#94a3b8', fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `${v}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ color: '#94a3b8', fontSize: 13 }}
          iconType="circle"
        />
        {/* Danger zone: > 300 */}
        <ReferenceLine
          y={300}
          stroke="#ef4444"
          strokeDasharray="6 3"
          strokeWidth={1.5}
          label={{ value: 'CRITICAL 300', fill: '#ef4444', fontSize: 11, position: 'insideTopRight' }}
        />
        {/* Elevated: > 180 */}
        <ReferenceLine
          y={180}
          stroke="#f59e0b"
          strokeDasharray="6 3"
          strokeWidth={1.5}
          label={{ value: 'HIGH 180', fill: '#f59e0b', fontSize: 11, position: 'insideTopRight' }}
        />
        <Line
          type="monotone"
          dataKey="glucose"
          name="Glucose (mg/dL)"
          stroke={getLineColor()}
          strokeWidth={2.5}
          dot={(props) => {
            const { cx, cy, payload } = props;
            const c =
              payload.glucose > 300 ? '#ef4444' :
              payload.glucose > 180 ? '#f59e0b' :
              '#10b981';
            return (
              <circle
                key={`dot-${cx}-${cy}`}
                cx={cx} cy={cy} r={4}
                fill={c} stroke="#0f172a" strokeWidth={2}
              />
            );
          }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
