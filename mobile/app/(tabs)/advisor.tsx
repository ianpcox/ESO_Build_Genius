import { useBuild } from './_layout';
import { api } from '../../lib/api';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

const SLOT_NAMES: Record<number, string> = {
  1: 'Head', 2: 'Shoulders', 3: 'Chest', 4: 'Legs', 5: 'Feet',
  6: 'Hands', 7: 'Waist', 8: 'Front main', 9: 'Front off',
  10: 'Back main', 11: 'Back off', 12: 'Neck', 13: 'Ring 1', 14: 'Ring 2',
};

type Rec = { set_name: string; type: string; set_max_equip_count: number; is_fully_redundant: boolean };

export default function AdvisorTab() {
  const ctx = useBuild();
  const [recs, setRecs] = useState<Rec[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecs = useCallback(async () => {
    if (ctx.buildId == null || ctx.selectedSlotId == null) {
      setRecs([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const equipment = Object.entries(ctx.equipment).map(([slotId, gameId]) => ({
        slot_id: Number(slotId),
        game_id: gameId,
      }));
      const list = await api.recommend(ctx.buildId, ctx.selectedSlotId, equipment);
      setRecs(list.slice(0, 25));
    } catch (e) {
      setError((e as Error).message);
      setRecs([]);
    } finally {
      setLoading(false);
    }
  }, [ctx.buildId, ctx.selectedSlotId, ctx.equipment]);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  if (ctx.buildId == null) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>No build loaded. Set API URL on the first screen.</Text>
      </View>
    );
  }

  if (ctx.selectedSlotId == null) {
    return (
      <View style={styles.centered}>
        <Text style={styles.hint}>
          Select an equipment slot on the Equipment tab to see set recommendations (with buff redundancy).
        </Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Recommendations for {SLOT_NAMES[ctx.selectedSlotId] ?? `Slot ${ctx.selectedSlotId}`}</Text>
      {loading && <ActivityIndicator color="#c69c44" style={styles.loader} />}
      {error && <Text style={styles.error}>{error}</Text>}
      {!loading && !error && recs.length === 0 && (
        <Text style={styles.muted}>No recommendations.</Text>
      )}
      {!loading && recs.map((r, i) => (
        <View key={i} style={[styles.item, r.is_fully_redundant && styles.itemRedundant]}>
          <Text style={styles.setName}>{r.set_name}</Text>
          <Text style={styles.meta}>
            {r.type}, {r.set_max_equip_count}pc
            {r.is_fully_redundant ? ' [redundant for self-buffs]' : ''}
          </Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0c0e12' },
  content: { padding: 16, paddingBottom: 32 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0c0e12', padding: 24 },
  hint: { color: '#8b8f99', textAlign: 'center', fontSize: 14 },
  title: { fontSize: 16, color: '#c69c44', marginBottom: 12, fontWeight: '600' },
  loader: { marginVertical: 12 },
  error: { color: '#a04545', marginBottom: 8 },
  muted: { color: '#8b8f99', marginTop: 8 },
  item: { paddingVertical: 10, paddingHorizontal: 12, backgroundColor: '#161922', borderRadius: 8, marginBottom: 6, borderWidth: 1, borderColor: '#2a2d38' },
  itemRedundant: { borderColor: 'rgba(160, 69, 69, 0.5)', opacity: 0.9 },
  setName: { color: '#e8e6e3', fontSize: 15, fontWeight: '500' },
  meta: { color: '#8b8f99', fontSize: 12, marginTop: 2 },
});
