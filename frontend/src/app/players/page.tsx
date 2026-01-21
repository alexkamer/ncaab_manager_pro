'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { playersApi } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { Search } from 'lucide-react';
import Link from 'next/link';

export default function PlayersPage() {
  const [search, setSearch] = useState('');

  const { data: players, isLoading, error } = useQuery({
    queryKey: ['players', search],
    queryFn: () => playersApi.getAll({ search: search || undefined, limit: 100 }),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Players</h1>
        <p className="text-gray-400">Search and explore NCAA basketball players</p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search players by name..."
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
        <ErrorMessage message="Failed to load players" />
      )}

      {players && players.length === 0 && search && (
        <div className="text-center py-12 glass rounded-lg">
          <p className="text-gray-400">No players found matching "{search}"</p>
        </div>
      )}

      {players && players.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {players.map((player: any) => (
            <Link key={player.id} href={`/players/${player.id}`}>
              <div className="glass rounded-lg p-4 hover:bg-white/10 transition-all cursor-pointer">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">{player.displayName}</div>
                    <div className="text-sm text-gray-400 space-x-2">
                      {player.displayHeight && <span>{player.displayHeight}</span>}
                      {player.displayWeight && <span>• {player.displayWeight}</span>}
                      {player.jersey && <span>• #{player.jersey}</span>}
                    </div>
                    {player.experience_displayValue && (
                      <div className="text-xs text-gray-500 mt-1">
                        {player.experience_displayValue}
                      </div>
                    )}
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
