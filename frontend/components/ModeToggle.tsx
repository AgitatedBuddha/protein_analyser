'use client';

type ScoreMode = 'cut' | 'bulk' | 'clean';

interface ModeToggleProps {
  mode: ScoreMode;
  onChange: (mode: ScoreMode) => void;
  showDescription?: boolean;
}

const modes: { value: ScoreMode; label: string; description: string; color: string }[] = [
  { 
    value: 'cut', 
    label: 'Cut', 
    description: 'Best for fat loss while preserving muscle. Prioritizes high protein per calorie and leucine content.',
    color: 'bg-orange-500'
  },
  { 
    value: 'bulk', 
    label: 'Bulk', 
    description: 'Best for muscle building. Prioritizes total protein, EAAs, and leucine per serving.',
    color: 'bg-blue-500'
  },
  { 
    value: 'clean', 
    label: 'Clean', 
    description: 'Best for health-conscious users. Prioritizes low sodium, minimal additives, no amino spiking.',
    color: 'bg-green-500'
  },
];

export default function ModeToggle({ mode, onChange, showDescription = true }: ModeToggleProps) {
  const currentMode = modes.find(m => m.value === mode);
  
  return (
    <div className="space-y-2">
      <div className="flex gap-2 p-1 bg-gray-800 rounded-lg w-fit">
        {modes.map((m) => (
          <button
            key={m.value}
            onClick={() => onChange(m.value)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              mode === m.value
                ? `${m.color} text-white`
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            {m.label}
          </button>
        ))}
      </div>
      {showDescription && currentMode && (
        <p className="text-sm text-gray-400 max-w-xl">
          {currentMode.description}
        </p>
      )}
    </div>
  );
}
