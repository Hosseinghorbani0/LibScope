import React from 'react';

interface ScoreGaugeProps {
  score?: number;
  confidence?: 'high' | 'medium' | 'low';
  size?: number;
  showConfidence?: boolean;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  score,
  confidence = 'medium',
  size = 110,
  showConfidence = true,
}) => {
  const isMissing = score === undefined || score === null;
  const val = isMissing ? 0 : Math.min(100, Math.max(0, score));

  // SVG circle calculations
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (val / 100) * circumference;

  let color = '#ef4444'; // Red
  if (val >= 85) color = '#10b981'; // Green
  else if (val >= 65) color = '#f59e0b'; // Amber

  return (
    <div className="flex flex-col items-center">
      <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#1f2937"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {!isMissing && (
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              stroke={color}
              strokeWidth={strokeWidth}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              fill="transparent"
              className="transition-all duration-1000 ease-out"
            />
          )}
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className="text-2xl font-black tracking-tight" style={{ color: isMissing ? '#9ca3af' : color }}>
            {isMissing ? 'N/A' : val.toFixed(1)}
          </span>
          <span className="text-[10px] text-slate-400 uppercase font-medium">/ 100</span>
        </div>
      </div>
      {showConfidence && (
        <div className="mt-2 text-center">
          <span
            className={`px-2 py-0.5 text-[10px] uppercase font-bold rounded-full border ${
              confidence === 'high'
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800'
                : confidence === 'medium'
                ? 'bg-amber-950/60 text-amber-400 border-amber-800'
                : 'bg-rose-950/60 text-rose-400 border-rose-800'
            }`}
          >
            {confidence} Confidence
          </span>
        </div>
      )}
    </div>
  );
};

