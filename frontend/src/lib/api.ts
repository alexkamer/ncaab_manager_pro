import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Games API
export const gamesApi = {
  getAll: async (params?: {
    date?: string;
    season?: number;
    team_id?: string;
    conference?: string;
    completed?: boolean;
    limit?: number;
    offset?: number;
  }) => {
    const { data } = await api.get('/games', { params });
    return data;
  },

  getToday: async () => {
    const { data } = await api.get('/games/today');
    return data;
  },

  getById: async (id: string) => {
    const { data } = await api.get(`/games/${id}`);
    return data;
  },

  getBoxscore: async (id: string) => {
    const { data } = await api.get(`/games/${id}/boxscore`);
    return data;
  },

  getPredictions: async (id: string) => {
    const { data } = await api.get(`/games/${id}/predictions`);
    return data;
  },

  getOdds: async (id: string) => {
    const { data } = await api.get(`/games/${id}/odds`);
    return data;
  },
};

// Teams API
export const teamsApi = {
  getAll: async (params?: {
    search?: string;
    conference?: string;
    limit?: number;
    offset?: number;
  }) => {
    const { data } = await api.get('/teams', { params });
    return data;
  },

  getById: async (id: string) => {
    const { data } = await api.get(`/teams/${id}`);
    return data;
  },

  getSchedule: async (id: string, season: number) => {
    const { data } = await api.get(`/teams/${id}/schedule`, {
      params: { season },
    });
    return data;
  },

  getRoster: async (id: string, season: string) => {
    const { data } = await api.get(`/teams/${id}/roster`, {
      params: { season },
    });
    return data;
  },

  getStats: async (id: string, season: number) => {
    const { data } = await api.get(`/teams/${id}/stats`, {
      params: { season },
    });
    return data;
  },

  getPlayerStats: async (id: string, season: number) => {
    const { data } = await api.get(`/teams/${id}/player-stats`, {
      params: { season },
    });
    return data;
  },
};

// Players API
export const playersApi = {
  getAll: async (params?: {
    search?: string;
    limit?: number;
    offset?: number;
  }) => {
    const { data } = await api.get('/players', { params });
    return data;
  },

  getById: async (id: string) => {
    const { data } = await api.get(`/players/${id}`);
    return data;
  },

  getSeasons: async (id: string) => {
    const { data } = await api.get(`/players/${id}/seasons`);
    return data;
  },

  getGameLog: async (id: string, season: number) => {
    const { data } = await api.get(`/players/${id}/gamelog`, {
      params: { season },
    });
    return data;
  },

  getStats: async (id: string, season: number) => {
    const { data } = await api.get(`/players/${id}/stats`, {
      params: { season },
    });
    return data;
  },
};

// Analytics API
export const analyticsApi = {
  getPowerRankings: async (season: number, week?: number, limit?: number) => {
    const { data } = await api.get('/analytics/power-rankings', {
      params: { season, week, limit },
    });
    return data;
  },

  getAPPoll: async (season: number, week?: number) => {
    const { data } = await api.get('/analytics/ap-poll', {
      params: { season, week },
    });
    return data;
  },

  getConferenceStandings: async (conference: string, season: number) => {
    const { data } = await api.get('/analytics/conference-standings', {
      params: { conference, season },
    });
    return data;
  },

  getBettingEdges: async (date?: string, min_edge?: number) => {
    const { data } = await api.get('/analytics/betting-edges', {
      params: { date, min_edge },
    });
    return data;
  },
};

// Betting API
export const bettingApi = {
  getLines: async (date?: string, provider?: string) => {
    const { data } = await api.get('/betting/lines', {
      params: { date, provider },
    });
    return data;
  },

  getLineMovers: async (hours?: number, min_movement?: number) => {
    const { data } = await api.get('/betting/movers', {
      params: { hours, min_movement },
    });
    return data;
  },

  getProviders: async () => {
    const { data } = await api.get('/betting/providers');
    return data;
  },

  compareSportsbooks: async (game_id: string) => {
    const { data } = await api.get(`/betting/compare/${game_id}`);
    return data;
  },
};

// Seasons API
export const seasonsApi = {
  getCurrent: async () => {
    const { data } = await api.get('/seasons/current');
    return data;
  },

  getAll: async () => {
    const { data } = await api.get('/seasons');
    return data;
  },

  getById: async (year: number) => {
    const { data } = await api.get(`/seasons/${year}`);
    return data;
  },
};

export default api;
