'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const routes = [
  { path: '/', label: 'Leaderboard', icon: '🏆' },
  { path: '/nutrients', label: 'Nutrients', icon: '🥗' },
  { path: '/aminoacids', label: 'Amino Acids', icon: '🧬' },
  { path: '/scoring', label: 'Scoring Logic', icon: '⚖️' },
];

export default function Navigation() {
  const pathname = usePathname();

  return (
    <nav className="flex gap-1 p-1 bg-gray-800 rounded-lg mb-6">
      {routes.map((route) => (
        <Link
          key={route.path}
          href={route.path}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-all ${
            pathname === route.path
              ? 'bg-gray-700 text-white'
              : 'text-gray-400 hover:text-gray-200'
          }`}
        >
          <span>{route.icon}</span>
          <span>{route.label}</span>
        </Link>
      ))}
    </nav>
  );
}
