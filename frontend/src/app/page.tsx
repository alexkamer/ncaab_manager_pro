'use client';

import { useQuery } from '@tanstack/react-query';
import { gamesApi } from '@/lib/api';
import { GameCard } from '@/components/games/GameCard';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';

export default function Home() {
  const { data: games, isLoading, error } = useQuery({
    queryKey: ['games', 'today'],
    queryFn: () => gamesApi.getToday(),
  });

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4 py-12">
        <h1 className="text-6xl font-bold bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 bg-clip-text text-transparent">
          NCAA Basketball Analytics
        </h1>
        <p className="text-xl text-gray-400 max-w-2xl mx-auto">
          Advanced analytics, predictions, and betting intelligence for NCAA basketball
        </p>
      </div>

      {/* Today's Games */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-3xl font-bold text-white">Today's Games</h2>
          <span className="text-sm text-gray-400">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })}
          </span>
        </div>

        {isLoading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {error && (
          <ErrorMessage message="Failed to load today's games" />
        )}

        {games && games.length === 0 && (
          <div className="text-center py-12 glass rounded-lg">
            <p className="text-gray-400 text-lg">No games scheduled for today</p>
          </div>
        )}

        {games && games.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {games.map((game) => (
              <GameCard key={game.id} game={game} />
            ))}
          </div>
        )}
      </section>

      {/* Quick Stats */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="glass rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-400 mb-2">Total Games</h3>
          <p className="text-4xl font-bold text-white">60,000+</p>
          <p className="text-sm text-gray-500 mt-2">Since 2002</p>
        </div>
        <div className="glass rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-400 mb-2">Active Teams</h3>
          <p className="text-4xl font-bold text-white">362</p>
          <p className="text-sm text-gray-500 mt-2">Division I</p>
        </div>
        <div className="glass rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-400 mb-2">Players Tracked</h3>
          <p className="text-4xl font-bold text-white">17,000+</p>
          <p className="text-sm text-gray-500 mt-2">Current & Historical</p>
        </div>
      </section>
    </div>
  );
}
