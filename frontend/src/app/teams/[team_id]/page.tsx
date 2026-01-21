'use client';

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { teamsApi, analyticsApi, seasonsApi } from '@/lib/api';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorMessage } from '@/components/ui/ErrorMessage';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowLeft, Calendar, Users, TrendingUp } from 'lucide-react';

type TabType = 'overview' | 'team-stats' | 'player-stats' | 'standings' | 'roster';

export default function TeamDetailPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const team_id = params.team_id as string;

  // Fetch current season from database
  const { data: currentSeasonData } = useQuery({
    queryKey: ['currentSeason'],
    queryFn: () => seasonsApi.getCurrent(),
  });

  // Fetch all seasons for dropdown
  const { data: allSeasons } = useQuery({
    queryKey: ['allSeasons'],
    queryFn: () => seasonsApi.getAll(),
  });

  // Get state from URL params
  const urlTab = searchParams.get('tab') as TabType | null;
  const urlRosterPage = parseInt(searchParams.get('rosterPage') || '1');

  const [selectedSeason, setSelectedSeason] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>(urlTab || 'overview');
  const [statsCategory, setStatsCategory] = useState<string>('all');
  const [rosterPage, setRosterPage] = useState(urlRosterPage);
  const itemsPerPage = 10;

  // Update selectedSeason when currentSeasonData is loaded
  useEffect(() => {
    if (currentSeasonData?.year && selectedSeason === null) {
      setSelectedSeason(currentSeasonData.year);
    }
  }, [currentSeasonData, selectedSeason]);

  // Update URL when tab or pagination changes
  useEffect(() => {
    const params = new URLSearchParams();
    if (activeTab !== 'overview') {
      params.set('tab', activeTab);
    }
    if (rosterPage > 1) {
      params.set('rosterPage', rosterPage.toString());
    }

    const query = params.toString();
    const newUrl = query ? `?${query}` : window.location.pathname;
    router.replace(newUrl, { scroll: false });
  }, [activeTab, rosterPage, router]);

  // Fetch team details
  const { data: team, isLoading: teamLoading, error: teamError } = useQuery({
    queryKey: ['team', team_id],
    queryFn: () => teamsApi.getById(team_id),
  });

  // Fetch team stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['teamStats', team_id, selectedSeason],
    queryFn: () => teamsApi.getStats(team_id, selectedSeason!),
    enabled: !!team_id && selectedSeason !== null,
  });

  // Fetch team schedule
  const { data: schedule, isLoading: scheduleLoading } = useQuery({
    queryKey: ['teamSchedule', team_id, selectedSeason],
    queryFn: () => teamsApi.getSchedule(team_id, selectedSeason!),
    enabled: !!team_id && selectedSeason !== null,
  });

  // Fetch team roster
  const { data: roster, isLoading: rosterLoading } = useQuery({
    queryKey: ['teamRoster', team_id, selectedSeason],
    queryFn: () => teamsApi.getRoster(team_id, selectedSeason!.toString()),
    enabled: !!team_id && selectedSeason !== null,
  });

  // Fetch conference info from first game
  const { data: conferenceInfo } = useQuery({
    queryKey: ['teamConference', team_id],
    queryFn: async () => {
      const firstGame = schedule?.[0];
      if (!firstGame) return { home_team_id: null, home_team_conference_slug: null, away_team_conference_slug: null };
      try {
        const response = await fetch(`http://localhost:8000/api/v1/games/${firstGame.id}`);
        const data = await response.json();
        return data || { home_team_id: null, home_team_conference_slug: null, away_team_conference_slug: null };
      } catch (error) {
        return { home_team_id: null, home_team_conference_slug: null, away_team_conference_slug: null };
      }
    },
    enabled: !!schedule && schedule.length > 0,
  });

  const teamConferenceSlug = conferenceInfo?.home_team_id === team_id
    ? conferenceInfo?.home_team_conference_slug
    : conferenceInfo?.away_team_conference_slug;

  // Fetch conference standings
  const { data: standings, isLoading: standingsLoading } = useQuery({
    queryKey: ['conferenceStandings', teamConferenceSlug, selectedSeason],
    queryFn: () => analyticsApi.getConferenceStandings(teamConferenceSlug || '', selectedSeason!),
    enabled: !!teamConferenceSlug && selectedSeason !== null,
  });

  // Fetch ESPN real-time team statistics
  const { data: espnStats, isLoading: espnStatsLoading } = useQuery({
    queryKey: ['espnStats', team_id, selectedSeason],
    queryFn: async () => {
      const response = await fetch(
        `https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/${selectedSeason}/types/0/teams/${team_id}/statistics?lang=en&region=us`
      );
      return response.json();
    },
    enabled: !!team_id && selectedSeason !== null,
  });

  // Fetch ESPN team record (for accurate wins/losses)
  const { data: espnRecord, isLoading: espnRecordLoading } = useQuery({
    queryKey: ['espnRecord', team_id, selectedSeason],
    queryFn: async () => {
      const response = await fetch(
        `https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/${selectedSeason}/types/2/teams/${team_id}/record?lang=en&region=us`
      );
      return response.json();
    },
    enabled: !!team_id && selectedSeason !== null,
  });

  if (teamLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  if (teamError || !team) {
    return <ErrorMessage message="Failed to load team details" />;
  }

  // Parse team logos
  const getTeamLogo = () => {
    if (!team.logos) return null;
    try {
      const logos = JSON.parse(team.logos);
      // Find the default logo or use the first one
      const defaultLogo = logos.find((logo: any) => logo.rel.includes('default'));
      return defaultLogo?.href || logos[0]?.href;
    } catch {
      return null;
    }
  };

  const teamLogo = getTeamLogo();
  const recentGames = schedule?.filter((game: any) => game.completed).slice(-5).reverse() || [];
  const upcomingGames = schedule?.filter((game: any) => !game.completed).slice(0, 5) || [];

  return (
    <div className="space-y-8">
      {/* Header with back button */}
      <Link
        href="/teams"
        className="inline-flex items-center text-gray-400 hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Teams
      </Link>

      {/* Team Header */}
      <div className="glass rounded-lg p-8">
        <div className="flex items-center space-x-6">
          {teamLogo ? (
            <div className="w-24 h-24 flex items-center justify-center">
              <Image
                src={teamLogo}
                alt={team.displayName}
                width={96}
                height={96}
                className="object-contain"
              />
            </div>
          ) : team.color ? (
            <div
              className="w-24 h-24 rounded-lg flex items-center justify-center text-white font-bold text-2xl"
              style={{ backgroundColor: `#${team.color}` }}
            >
              {team.abbreviation}
            </div>
          ) : null}
          <div className="flex-1">
            <h1 className="text-4xl font-bold text-white mb-2">{team.displayName}</h1>
            <p className="text-xl text-gray-400">{team.location}</p>
            {team.nickname && (
              <p className="text-lg text-gray-500 mt-1">{team.nickname}</p>
            )}
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="glass rounded-lg p-2">
        <div className="flex space-x-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab('overview')}
            className={`px-4 py-2 rounded transition-colors whitespace-nowrap ${
              activeTab === 'overview'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('team-stats')}
            className={`px-4 py-2 rounded transition-colors whitespace-nowrap ${
              activeTab === 'team-stats'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            Team Stats
          </button>
          <button
            onClick={() => setActiveTab('player-stats')}
            className={`px-4 py-2 rounded transition-colors whitespace-nowrap ${
              activeTab === 'player-stats'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            Player Stats
          </button>
          <button
            onClick={() => setActiveTab('standings')}
            className={`px-4 py-2 rounded transition-colors whitespace-nowrap ${
              activeTab === 'standings'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            Standings
          </button>
          <button
            onClick={() => setActiveTab('roster')}
            className={`px-4 py-2 rounded transition-colors whitespace-nowrap ${
              activeTab === 'roster'
                ? 'bg-blue-600 text-white'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            Roster
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* Stats Overview */}
      {espnRecord?.items && (
        <div className="glass rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <TrendingUp className="w-6 h-6 mr-2" />
            Season Stats ({allSeasons?.find((s: any) => s.year === selectedSeason)?.displayName || selectedSeason})
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'overall')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Overall Record</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'vs. Conf.')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Conference Record</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'overall')?.stats?.find((s: any) => s.name === 'avgPointsFor')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">PPG</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'overall')?.stats?.find((s: any) => s.name === 'avgPointsAgainst')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Opp PPG</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'Home')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Home Record</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'Road')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Away Record</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-white">
                {espnRecord.items.find((i: any) => i.name === 'overall')?.value ? (espnRecord.items.find((i: any) => i.name === 'overall').value * 100).toFixed(1) + '%' : 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Win %</div>
            </div>
            <div className="text-center">
              <div className={`text-3xl font-bold ${parseFloat(espnRecord.items.find((i: any) => i.name === 'overall')?.stats?.find((s: any) => s.name === 'differential')?.value || 0) > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {espnRecord.items.find((i: any) => i.name === 'overall')?.stats?.find((s: any) => s.name === 'differential')?.displayValue || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 mt-1">Point Diff</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Games */}
        <div className="glass rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <Calendar className="w-6 h-6 mr-2" />
            Recent Games
          </h2>
          {scheduleLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : recentGames.length > 0 ? (
            <div className="space-y-3">
              {recentGames.map((game: any) => (
                <Link key={game.id} href={`/games/${game.id}`}>
                  <div className="bg-gray-800/50 rounded-lg p-4 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="text-sm text-gray-400 mb-1">
                          {game.is_home ? 'vs' : '@'} {game.opponent_name}
                        </div>
                        <div className="flex items-center space-x-3">
                          <div className={`text-lg font-bold ${game.won ? 'text-green-400' : 'text-red-400'}`}>
                            {game.won ? 'W' : 'L'}
                          </div>
                          <div className="text-white font-semibold">
                            {game.score} - {game.opponent_score}
                          </div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(game.date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No recent games</p>
          )}
        </div>

        {/* Upcoming Games */}
        <div className="glass rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center">
            <Calendar className="w-6 h-6 mr-2" />
            Upcoming Games
          </h2>
          {scheduleLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : upcomingGames.length > 0 ? (
            <div className="space-y-3">
              {upcomingGames.map((game: any) => (
                <Link key={game.id} href={`/games/${game.id}`}>
                  <div className="bg-gray-800/50 rounded-lg p-4 hover:bg-gray-800 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="text-white font-semibold mb-1">
                          {game.is_home ? 'vs' : '@'} {game.opponent_name}
                        </div>
                        <div className="text-sm text-gray-400">
                          {game.status_detail || 'Scheduled'}
                        </div>
                      </div>
                      <div className="text-sm text-gray-500">
                        {new Date(game.date).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No upcoming games</p>
          )}
        </div>
      </div>
        </>
      )}

      {/* Team Stats Tab - ESPN Real-time Data */}
      {activeTab === 'team-stats' && (
        <div className="glass rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white">Team Statistics</h2>
            <div className="flex items-center space-x-4">
              <select
                value={selectedSeason || ''}
                onChange={(e) => setSelectedSeason(Number(e.target.value))}
                className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                {allSeasons?.slice(0, 10).map((season: any) => (
                  <option key={season.year} value={season.year}>
                    {season.displayName}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {espnStatsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : espnStats?.splits?.categories ? (
            <>
              {/* Category Tabs */}
              <div className="flex space-x-2 mb-6 overflow-x-auto pb-2">
                <button
                  onClick={() => setStatsCategory('all')}
                  className={`px-4 py-2 rounded whitespace-nowrap transition-colors ${
                    statsCategory === 'all'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white'
                  }`}
                >
                  All Stats
                </button>
                {espnStats.splits.categories.map((category: any) => (
                  <button
                    key={category.name}
                    onClick={() => setStatsCategory(category.name)}
                    className={`px-4 py-2 rounded whitespace-nowrap transition-colors ${
                      statsCategory === category.name
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-white'
                    }`}
                  >
                    {category.displayName}
                  </button>
                ))}
              </div>

              {/* Stats Display */}
              <div className="space-y-6">
                {espnStats.splits.categories
                  .filter((cat: any) => statsCategory === 'all' || cat.name === statsCategory)
                  .map((category: any) => (
                    <div key={category.name}>
                      {statsCategory === 'all' && (
                        <h3 className="text-lg font-semibold text-white mb-4 capitalize border-b border-gray-700 pb-2">
                          {category.displayName}
                        </h3>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {category.stats.map((stat: any) => (
                          <div key={stat.name} className="bg-gray-800/50 rounded-lg p-4 hover:bg-gray-800/70 transition-colors">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="text-sm text-gray-400 mb-1">{stat.displayName}</div>
                                <div className="text-3xl font-bold text-white">{stat.displayValue}</div>
                              </div>
                              {stat.rank && stat.rank <= 100 && (
                                <div className="ml-2">
                                  <div className={`px-2 py-1 rounded text-xs font-semibold ${
                                    stat.rank <= 10 ? 'bg-green-600 text-white' :
                                    stat.rank <= 50 ? 'bg-blue-600 text-white' :
                                    'bg-gray-700 text-gray-300'
                                  }`}>
                                    #{stat.rank}
                                  </div>
                                </div>
                              )}
                            </div>
                            {stat.rank && (
                              <div className="text-xs text-gray-500 mt-2">
                                National Rank: {stat.rankDisplayValue}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </>
          ) : (
            <p className="text-gray-400 text-center py-8">No ESPN statistics available for this season</p>
          )}
        </div>
      )}

      {/* Player Stats Tab */}
      {activeTab === 'player-stats' && (
        <div className="glass rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Player Stats</h2>
          <p className="text-gray-400 text-center py-8">Player statistics coming soon...</p>
        </div>
      )}

      {/* Standings Tab - Conference Standings (ALL TEAMS, NO PAGINATION) */}
      {activeTab === 'standings' && (
        <div className="glass rounded-lg p-6">
          <h2 className="text-2xl font-bold text-white mb-6">Conference Standings</h2>
          {standingsLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : standings && standings.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Rank</th>
                    <th className="text-left py-3 px-4 text-gray-400 font-semibold">Team</th>
                    <th className="text-center py-3 px-4 text-gray-400 font-semibold">Conf</th>
                    <th className="text-center py-3 px-4 text-gray-400 font-semibold">Overall</th>
                    <th className="text-center py-3 px-4 text-gray-400 font-semibold">Win %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {standings.map((standing: any, index: number) => (
                    <tr
                      key={standing.team_id}
                      className={`transition-colors ${
                        standing.team_id === team_id
                          ? 'bg-blue-900/20 font-semibold'
                          : 'hover:bg-gray-800/50'
                      }`}
                    >
                      <td className="py-3 px-4 text-white">{index + 1}</td>
                      <td className="py-3 px-4">
                        <Link href={`/teams/${standing.team_id}?tab=standings`} className="text-white hover:text-blue-400 flex items-center space-x-2">
                          {standing.color && (
                            <div
                              className="w-6 h-6 rounded flex items-center justify-center text-white text-xs font-bold"
                              style={{ backgroundColor: `#${standing.color}` }}
                            >
                              {standing.abbreviation?.substring(0, 2)}
                            </div>
                          )}
                          <span>{standing.team_name}</span>
                        </Link>
                      </td>
                      <td className="py-3 px-4 text-center text-gray-300">
                        {standing.conference_wins}-{standing.conference_losses}
                      </td>
                      <td className="py-3 px-4 text-center text-gray-300">
                        {standing.overall_wins}-{standing.overall_losses}
                      </td>
                      <td className="py-3 px-4 text-center text-gray-300">
                        {(standing.conference_win_percentage * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-gray-400 text-center py-8">No conference standings available</p>
          )}
        </div>
      )}

      {/* Roster Tab */}
      {activeTab === 'roster' && (
        <div className="glass rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-white flex items-center">
              <Users className="w-6 h-6 mr-2" />
              Team Roster {roster && `(${roster.length} players)`}
            </h2>
            <div className="flex items-center space-x-4">
              <select
                value={selectedSeason || ''}
                onChange={(e) => setSelectedSeason(Number(e.target.value))}
                className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                {allSeasons?.slice(0, 10).map((season: any) => (
                  <option key={season.year} value={season.year}>
                    {season.displayName}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {rosterLoading ? (
            <div className="flex justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : roster && roster.length > 0 ? (
            <>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-700">
                      <th className="text-left py-3 px-2 text-gray-400 font-semibold">Player</th>
                      <th className="text-left py-3 px-2 text-gray-400 font-semibold">Pos</th>
                      <th className="text-center py-3 px-2 text-gray-400 font-semibold">Height</th>
                      <th className="text-center py-3 px-2 text-gray-400 font-semibold">Weight</th>
                      <th className="text-center py-3 px-2 text-gray-400 font-semibold">Year</th>
                      <th className="text-center py-3 px-2 text-gray-400 font-semibold">#</th>
                    </tr>
                  </thead>
                  <tbody>
                    {roster
                      .slice((rosterPage - 1) * itemsPerPage, rosterPage * itemsPerPage)
                      .map((player: any) => (
                        <tr
                          key={player.season_player_id || `${player.player_id}-${player.season}`}
                          className="hover:bg-gray-800/50 transition-colors border-b border-gray-800"
                        >
                          <td className="py-3 px-2">
                            <Link href={`/players/${player.player_id}`} className="flex items-center space-x-3 hover:text-blue-400">
                              {player.headshot ? (
                                <Image
                                  src={player.headshot.includes('espncdn.com') && !player.headshot.includes('scale=crop')
                                    ? `${player.headshot}?h=80&w=110&scale=crop`
                                    : player.headshot
                                  }
                                  alt={player.displayName}
                                  width={55}
                                  height={40}
                                  className="object-cover rounded"
                                />
                              ) : (
                                <div className="w-[55px] h-10 bg-gray-700 flex items-center justify-center rounded">
                                  <span className="text-gray-500 text-xs font-semibold">
                                    {player.displayName.split(' ').map((n: string) => n[0]).join('')}
                                  </span>
                                </div>
                              )}
                              <span className="text-white font-medium">{player.displayName}</span>
                            </Link>
                          </td>
                          <td className="py-2 px-2 text-gray-300">{player.position_abbreviation || player.position_name || '-'}</td>
                          <td className="py-2 px-2 text-center text-gray-300">{player.displayHeight || '-'}</td>
                          <td className="py-2 px-2 text-center text-gray-300">{player.displayWeight || '-'}</td>
                          <td className="py-2 px-2 text-center text-gray-300">{player.experience_displayValue || '-'}</td>
                          <td className="py-2 px-2 text-center text-gray-300">{player.jersey || '-'}</td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination for Roster */}
              {roster.length > itemsPerPage && (
                <div className="flex items-center justify-center space-x-2 mt-6">
                  <button
                    onClick={() => setRosterPage(Math.max(1, rosterPage - 1))}
                    disabled={rosterPage === 1}
                    className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-gray-400">
                    Page {rosterPage} of {Math.ceil(roster.length / itemsPerPage)}
                  </span>
                  <button
                    onClick={() => setRosterPage(Math.min(Math.ceil(roster.length / itemsPerPage), rosterPage + 1))}
                    disabled={rosterPage === Math.ceil(roster.length / itemsPerPage)}
                    className="px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-400 text-center py-8">No roster information available</p>
          )}
        </div>
      )}
    </div>
  );
}
