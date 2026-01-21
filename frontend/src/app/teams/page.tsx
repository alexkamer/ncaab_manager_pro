'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { teamsApi } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Search } from 'lucide-react';
import Link from 'next/link';

export default function TeamsPage() {
  const [search, setSearch] = useState('');

  const { data: teams, isLoading, error } = useQuery({
    queryKey: ['teams', search],
    queryFn: () => teamsApi.getAll({ search: search || undefined }),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Teams</h1>
        <p className="text-gray-400">Browse all NCAA Division I basketball teams</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search teams by name or location..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-12 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
        />
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner />
        </div>
      )}

      {error && (
        <ErrorMessage message="Failed to load teams" />
      )}

      {teams && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {teams.map((team: any) => (
            <Link key={team.id} href={`/teams/${team.id}`}>
              <div className="glass rounded-lg p-4 hover:bg-white/10 transition-all cursor-pointer">
                <div className="flex items-center space-x-3">
                  {team.color && (
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold"
                      style={{ backgroundColor: `#${team.color}` }}
                    >
                      {team.abbreviation}
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="font-semibold text-white">{team.displayName}</div>
                    <div className="text-sm text-gray-400">{team.location}</div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
