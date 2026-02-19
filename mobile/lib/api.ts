/**
 * API client for ESO Build Genius backend.
 * Base URL is set on the welcome screen (e.g. http://YOUR_PC_IP:5000).
 */

let baseUrl = 'http://127.0.0.1:5000';

export function setBaseUrl(url: string) {
  baseUrl = url.replace(/\/+$/, '');
}

export async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function testConnection(): Promise<boolean> {
  try {
    const data = await get<{ build_id?: number }>('/api/build');
    return typeof data?.build_id === 'number';
  } catch {
    return false;
  }
}

export type BuildFull = {
  build_id: number;
  recommended_build_id?: number;
  class_id?: number;
  race_id?: number;
  role_id?: number;
  mundus_id?: number;
  food_id?: number;
  potion_id?: number;
  equipment?: { slot_id: number; game_id: number }[];
  bar_skills?: {
    bar_slot_ord: number;
    ability_id: number;
    scribe_effect_id_1: number | null;
    scribe_effect_id_2: number | null;
    scribe_effect_id_3: number | null;
  }[];
};

export async function postBuild(payload: Record<string, unknown>): Promise<{ recommended_build_id: number }> {
  const res = await fetch(`${baseUrl}/api/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<{ recommended_build_id: number }>;
}

export const api = {
  build: (recommendedBuildId?: number) =>
    get<BuildFull | { build_id: number }>(
      recommendedBuildId ? `/api/build?recommended_build_id=${recommendedBuildId}` : '/api/build'
    ),
  classes: () => get<{ id: number; name: string }[]>('/api/classes'),
  races: () => get<{ id: number; name: string }[]>('/api/races'),
  roles: () => get<{ id: number; name: string }[]>('/api/roles'),
  mundus: (buildId: number) => get<{ mundus_id: number; name: string }[]>(`/api/mundus?build_id=${buildId}`),
  foods: (buildId: number) => get<{ food_id: number; name: string }[]>(`/api/foods?build_id=${buildId}`),
  potions: (buildId: number) => get<{ potion_id: number; name: string }[]>(`/api/potions?build_id=${buildId}`),
  slots: () => get<{ id: number; name: string }[]>('/api/slots'),
  sets: (buildId: number, slotId: number) =>
    get<{ game_id: number; set_name: string; type: string; set_max_equip_count: number }[]>(
      `/api/sets?build_id=${buildId}&slot_id=${slotId}`
    ),
  recommend: (buildId: number, slotId: number, equipment: { slot_id: number; game_id: number }[]) =>
    get<{ set_name: string; type: string; set_max_equip_count: number; is_fully_redundant: boolean }[]>(
      `/api/recommend?build_id=${buildId}&slot_id=${slotId}&equipment=${encodeURIComponent(JSON.stringify(equipment))}`
    ),
  scribeEffects: (buildId: number, abilityId?: number) =>
    get<{ scribe_effect_id: number; name: string; slot_id: number; slot_name: string }[]>(
      `/api/scribe_effects?build_id=${buildId}${abilityId != null ? `&ability_id=${abilityId}` : ''}`
    ),
  skillsForBar: (buildId: number, classId?: number) =>
    get<{ ability_id: number; name: string; skill_line_id: number | null; skill_line_name: string }[]>(
      `/api/skills_for_bar?build_id=${buildId}${classId ? `&class_id=${classId}` : ''}`
    ),
};
