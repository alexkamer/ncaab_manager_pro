'use client';

import Link from 'next/link';
import Image from 'next/image';
import { Calendar, MapPin } from 'lucide-react';
import { Game } from '@/lib/types';
import { format, parseISO } from 'date-fns';

interface GameCardProps {
  game: Game;
}

export function GameCard({ game }: GameCardProps) {
  const isCompleted = game.event_status_completed === 1;
  const isLive = game.event_status_state === 'in';

  const gameDate = parseISO(game.date);
  const formattedTime = format(gameDate, 'h:mm a');

  const homeWon = game.home_team_winner === 1;
  const awayWon = game.away_team_winner === 1;

  return (
    <Link href={`/games/${game.id}`}>
      <div className="glass rounded-lg p-6 hover:bg-white/10 transition-all cursor-pointer group">
        {/* Game Status */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <Calendar className="w-4 h-4" />
            <span>{formattedTime}</span>
          </div>
          {isLive && (
            <span className="px-2 py-1 bg-red-600 text-white text-xs font-bold rounded score-live">
              LIVE
            </span>
          )}
          {isCompleted && (
            <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs font-semibold rounded">
              FINAL
            </span>
          )}
          {!isCompleted && !isLive && (
            <span className="px-2 py-1 bg-blue-900 text-blue-300 text-xs font-semibold rounded">
              SCHEDULED
            </span>
          )}
        </div>

        {/* Teams */}
        <div className="space-y-4">
          {/* Away Team */}
          <div className={`flex items-center justify-between p-3 rounded-lg transition-all ${
            isCompleted && awayWon ? 'bg-green-900/20' : 'bg-gray-800/30'
          }`}>
            <div className="flex items-center space-x-3 flex-1">
              {game.away_team_logo && (
                <Image
                  src={game.away_team_logo}
                  alt={game.away_team_displayName}
                  width={32}
                  height={32}
                  className="rounded"
                />
              )}
              <div>
                <div className={`font-semibold ${
                  isCompleted && awayWon ? 'text-white' : 'text-gray-300'
                }`}>
                  {game.away_team_displayName}
                </div>
                <div className="text-xs text-gray-500">{game.away_team_abbreviation}</div>
              </div>
            </div>
            {game.away_team_score !== null && game.away_team_score !== undefined && (
              <div className={`text-2xl font-bold ${
                isCompleted && awayWon ? 'text-white' : 'text-gray-400'
              }`}>
                {game.away_team_score}
              </div>
            )}
          </div>

          {/* Home Team */}
          <div className={`flex items-center justify-between p-3 rounded-lg transition-all ${
            isCompleted && homeWon ? 'bg-green-900/20' : 'bg-gray-800/30'
          }`}>
            <div className="flex items-center space-x-3 flex-1">
              {game.home_team_logo && (
                <Image
                  src={game.home_team_logo}
                  alt={game.home_team_displayName}
                  width={32}
                  height={32}
                  className="rounded"
                />
              )}
              <div>
                <div className={`font-semibold ${
                  isCompleted && homeWon ? 'text-white' : 'text-gray-300'
                }`}>
                  {game.home_team_displayName}
                </div>
                <div className="text-xs text-gray-500">{game.home_team_abbreviation}</div>
              </div>
            </div>
            {game.home_team_score !== null && game.home_team_score !== undefined && (
              <div className={`text-2xl font-bold ${
                isCompleted && homeWon ? 'text-white' : 'text-gray-400'
              }`}>
                {game.home_team_score}
              </div>
            )}
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-4 pt-4 border-t border-gray-800">
          <div className="flex items-center justify-between text-xs text-gray-500">
            {game.is_neutral_site === 1 && (
              <div className="flex items-center space-x-1">
                <MapPin className="w-3 h-3" />
                <span>Neutral Site</span>
              </div>
            )}
            {game.is_conference_competition === 1 && (
              <span className="px-2 py-1 bg-purple-900/30 text-purple-300 rounded">
                Conference
              </span>
            )}
            {game.event_status_short_detail && (
              <span className="text-gray-400">{game.event_status_short_detail}</span>
            )}
          </div>
        </div>
      </div>
    </Link>
  );
}
