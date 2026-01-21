'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function AnalyticsPage() {
  const currentSeason = 2026;
  const [season, setSeason] = useState(currentSeason);

  const { data: rankings, isLoading, error } = useQuery({
    queryKey: ['power-rankings', season],
    queryFn: () => analyticsApi.getPowerRankings(season, undefined, 25),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Analytics</h1>
        <p className="text-gray-400">Power rankings, standings, and advanced metrics</p>
      </div>

      {/* Season Selector */}
      <div className="flex items-center space-x-4">
        <label className="text-gray-400">Season:</label>
        <select
          value={season}
          onChange={(e) => setSeason(Number(e.target.value))}
          className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
        >
          {[2026, 2025, 2024, 2023, 2022].map((year) => (
            <option key={year} value={year}>
              {year}-{String(year + 1).slice(2)}
            </option>
          ))}
        </select>
      </div>

      {/* Power Rankings */}
      <section>
        <h2 className="text-2xl font-bold text-white mb-4">Power Rankings</h2>

        {isLoading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {error && (
          <ErrorMessage message="Failed to load power rankings" />
        )}

        {rankings && (
          <div className="glass rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Rank
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Team
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Record
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                    Win %
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {rankings.map((team: any) => (
                  <tr key={team.team_id} className="hover:bg-white/5">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-lg font-bold text-white">{team.rank}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        {team.color && (
                          <div
                            className="w-8 h-8 rounded flex items-center justify-center text-white text-xs font-bold"
                            style={{ backgroundColor: `#${team.color}` }}
                          >
                            {team.abbreviation}
                          </div>
                        )}
                        <span className="text-white font-medium">{team.team_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                      {team.wins}-{team.losses}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-gray-300">
                      {(team.win_percentage * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
