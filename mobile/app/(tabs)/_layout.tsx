import { Tabs } from 'expo-router';
import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../../lib/api';

export type BarSlot = {
  ability_id: number | null;
  scribe_effect_id_1: number | null;
  scribe_effect_id_2: number | null;
  scribe_effect_id_3: number | null;
};

type BuildState = {
  buildId: number | null;
  recommendedBuildId: number | null;
  classId: number | null;
  raceId: number | null;
  roleId: number | null;
  mundusId: number | null;
  foodId: number | null;
  potionId: number | null;
  equipment: Record<number, number>;
  barSkills: Record<number, BarSlot>;
  selectedSlotId: number | null;
  setClassId: (v: number | null) => void;
  setRaceId: (v: number | null) => void;
  setRoleId: (v: number | null) => void;
  setMundusId: (v: number | null) => void;
  setFoodId: (v: number | null) => void;
  setPotionId: (v: number | null) => void;
  setEquipment: (slotId: number, gameId: number | null) => void;
  setEquipmentAll: (next: Record<number, number>) => void;
  setBarAbility: (ord: number, abilityId: number | null) => void;
  setBarScribe: (ord: number, slotId: 1 | 2 | 3, effectId: number | null) => void;
  setBarSkillsFromLoaded: (rows: { bar_slot_ord: number; ability_id: number; scribe_effect_id_1: number | null; scribe_effect_id_2: number | null; scribe_effect_id_3: number | null }[]) => void;
  setRecommendedBuildId: (v: number | null) => void;
  setSelectedSlotId: (v: number | null) => void;
  refreshFromStorage: () => void;
};

const BuildContext = createContext<BuildState | null>(null);

export function useBuild() {
  const ctx = useContext(BuildContext);
  if (!ctx) throw new Error('useBuild must be used inside BuildProvider');
  return ctx;
}

export function BuildProvider({ children }: { children: React.ReactNode }) {
  const [buildId, setBuildId] = useState<number | null>(null);
  const [recommendedBuildId, setRecommendedBuildId] = useState<number | null>(null);
  const [classId, setClassId] = useState<number | null>(null);
  const [raceId, setRaceId] = useState<number | null>(null);
  const [roleId, setRoleId] = useState<number | null>(null);
  const [mundusId, setMundusId] = useState<number | null>(null);
  const [foodId, setFoodId] = useState<number | null>(null);
  const [potionId, setPotionId] = useState<number | null>(null);
  const [equipment, setEquipmentState] = useState<Record<number, number>>({});
  const [barSkills, setBarSkillsState] = useState<Record<number, BarSlot>>({});
  const [selectedSlotId, setSelectedSlotId] = useState<number | null>(null);

  const setEquipment = (slotId: number, gameId: number | null) => {
    setEquipmentState((prev) => {
      const next = { ...prev };
      if (gameId == null) delete next[slotId];
      else next[slotId] = gameId;
      return next;
    });
  };

  const setEquipmentAll = (next: Record<number, number>) => {
    setEquipmentState({ ...next });
  };

  const setBarAbility = (ord: number, abilityId: number | null) => {
    setBarSkillsState((prev) => ({
      ...prev,
      [ord]: { ...(prev[ord] ?? {}), ability_id: abilityId, scribe_effect_id_1: prev[ord]?.scribe_effect_id_1 ?? null, scribe_effect_id_2: prev[ord]?.scribe_effect_id_2 ?? null, scribe_effect_id_3: prev[ord]?.scribe_effect_id_3 ?? null },
    }));
  };

  const setBarScribe = (ord: number, slotId: 1 | 2 | 3, effectId: number | null) => {
    const key = `scribe_effect_id_${slotId}` as keyof BarSlot;
    setBarSkillsState((prev) => {
      const cur = prev[ord] ?? {} as BarSlot;
      return { ...prev, [ord]: { ...cur, [key]: effectId } };
    });
  };

  const setBarSkillsFromLoaded = (rows: { bar_slot_ord: number; ability_id: number; scribe_effect_id_1: number | null; scribe_effect_id_2: number | null; scribe_effect_id_3: number | null }[]) => {
    const next: Record<number, BarSlot> = {};
    rows.forEach((r) => {
      next[r.bar_slot_ord] = {
        ability_id: r.ability_id,
        scribe_effect_id_1: r.scribe_effect_id_1 ?? null,
        scribe_effect_id_2: r.scribe_effect_id_2 ?? null,
        scribe_effect_id_3: r.scribe_effect_id_3 ?? null,
      };
    });
    setBarSkillsState(next);
  };

  const refreshFromStorage = () => {
    api.build().then((r) => setBuildId('build_id' in r ? r.build_id : r.build_id)).catch(() => setBuildId(null));
  };

  useEffect(() => {
    refreshFromStorage();
  }, []);

  const state: BuildState = {
    buildId,
    recommendedBuildId,
    classId,
    raceId,
    roleId,
    mundusId,
    foodId,
    potionId,
    equipment,
    barSkills,
    selectedSlotId,
    setClassId,
    setRaceId,
    setRoleId,
    setMundusId,
    setFoodId,
    setPotionId,
    setEquipment,
    setEquipmentAll,
    setBarAbility,
    setBarScribe,
    setBarSkillsFromLoaded,
    setRecommendedBuildId,
    setSelectedSlotId,
    refreshFromStorage,
  };

  return (
    <BuildContext.Provider value={state}>
      {children}
    </BuildContext.Provider>
  );
}

export default function TabsLayout() {
  return (
    <BuildProvider>
      <Tabs
        screenOptions={{
          headerStyle: { backgroundColor: '#161922' },
          headerTintColor: '#c69c44',
          tabBarStyle: { backgroundColor: '#161922', borderTopColor: '#2a2d38' },
          tabBarActiveTintColor: '#c69c44',
          tabBarInactiveTintColor: '#8b8f99',
        }}
      >
        <Tabs.Screen name="build" options={{ title: 'Build' }} />
        <Tabs.Screen name="equipment" options={{ title: 'Equipment' }} />
        <Tabs.Screen name="advisor" options={{ title: 'Advisor' }} />
        <Tabs.Screen name="skills" options={{ title: 'Skills' }} />
      </Tabs>
    </BuildProvider>
  );
}
