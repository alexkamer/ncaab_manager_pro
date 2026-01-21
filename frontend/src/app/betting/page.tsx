'use client';

import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { TrendingUp, AlertCircle } from 'lucide-react';

export default function BettingPage() {
  const { data: edges, isLoading, error } = useQuery({
    queryKey: ['betting-edges'],
    queryFn: () => analyticsApi.getBettingEdges(undefined, 5.0),
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Betting Intelligence</h1>
        <p className="text-gray-400">Find value bets where predictions disagree with Vegas lines</p>
      </div>

      {/* Info Alert */}
      <div className="glass rounded-lg p-4 border-l-4 border-blue-500">
        <div className="flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-blue-500 mt-0.5" />
          <div className="text-sm text-gray-300">
            <p className="font-semibold mb-1">How Betting Edges Work</p>
            <p className="text-gray-400">
              We compare our prediction model against Vegas implied probabilities to find
              discrepancies. A higher edge percentage indicates greater disagreement and
              potentially more value.
            </p>
          </div>
        </div>
      </div>

      {/* Betting Edges */}
      <section>
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center space-x-2">
          <TrendingUp className="w-6 h-6" />
          <span>Value Bets (5%+ Edge)</span>
        </h2>

        {isLoading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner />
          </div>
        )}

        {error && (
          <ErrorMessage message="Failed to load betting edges" />
        )}

        {edges && edges.length === 0 && (
          <div className="text-center py-12 glass rounded-lg">
            <p className="text-gray-400">No betting edges found for upcoming games</p>
          </div>
        )}

        {edges && edges.length > 0 && (
          <div className="space-y-4">
            {edges.map((edge: any) => (
              <div key={edge.game_id} className="glass rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className="text-lg font-semibold text-white mb-1">
                      {edge.away_team} @ {edge.home_team}
                    </div>
                    <div className="text-sm text-gray-400">{edge.date}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-400">
                      {edge.edge.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-400">Edge</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="text-xs text-gray-400 mb-1">Our Prediction</div>
                    <div className="text-lg font-semibold text-white">
                      {edge.recommended_bet === 'home' ? edge.home_team : edge.away_team} {edge.prediction_home_win_pct}%
                    </div>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <div className="text-xs text-gray-400 mb-1">Vegas Implied</div>
                    <div className="text-lg font-semibold text-white">
                      {edge.recommended_bet === 'home' ? edge.home_team : edge.away_team} {edge.implied_home_win_pct}%
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-700">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">Recommended Bet:</span>
                    <span className="font-semibold text-green-400 uppercase">
                      {edge.recommended_bet === 'home' ? edge.home_team : edge.away_team} ML
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm mt-2">
                    <span className="text-gray-400">Moneylines:</span>
                    <span className="text-white">
                      {edge.away_team} {edge.away_moneyline > 0 ? '+' : ''}{edge.away_moneyline} / {edge.home_team} {edge.home_moneyline > 0 ? '+' : ''}{edge.home_moneyline}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
