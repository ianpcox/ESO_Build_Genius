import { useBuild } from './_layout';
import { api } from '../../lib/api';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';

const SLOT_NAMES: Record<number, string> = {
  1: 'Head', 2: 'Shoulders', 3: 'Chest', 4: 'Legs', 5: 'Feet',
  6: 'Hands', 7: 'Waist', 8: 'Front main', 9: 'Front off',
  10: 'Back main', 11: 'Back off', 12: 'Neck', 13: 'Ring 1', 14: 'Ring 2',
};

const GROUPS: { name: string; ids: number[] }[] = [
  { name: 'Body', ids: [1, 2, 3, 4, 5, 6, 7] },
  { name: 'Jewelry', ids: [12, 13, 14] },
  { name: 'Front bar', ids: [8, 9] },
  { name: 'Back bar', ids: [10, 11] },
];

type SetOption = { game_id: number; set_name: string; type: string; set_max_equip_count: number };

export default function EquipmentTab() {
  const ctx = useBuild();
  const [setsBySlot, setSetsBySlot] = useState<Record<number, SetOption[]>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (ctx.buildId == null) {
      setLoading(false);
      return;
    }
    const slotIds = GROUPS.flatMap((g) => g.ids);
    Promise.all(slotIds.map((slotId) => api.sets(ctx.buildId!, slotId)))
      .then((results) => {
        const next: Record<number, SetOption[]> = {};
        slotIds.forEach((id, i) => { next[id] = results[i]; });
        setSetsBySlot(next);
      })
      .finally(() => setLoading(false));
  }, [ctx.buildId]);

  if (ctx.buildId == null) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>No build loaded. Set API URL on the first screen.</Text>
      </View>
    );
  }

  if (loading && Object.keys(setsBySlot).length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#c69c44" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {GROUPS.map((group) => (
        <View key={group.name} style={styles.group}>
          <Text style={styles.groupTitle}>{group.name}</Text>
          {group.ids.map((slotId) => (
            <View key={slotId} style={styles.row}>
              <TouchableOpacity
                style={[styles.slotLabel, ctx.selectedSlotId === slotId && styles.slotLabelSelected]}
                onPress={() => ctx.setSelectedSlotId(ctx.selectedSlotId === slotId ? null : slotId)}
              >
                <Text style={styles.slotLabelText}>{SLOT_NAMES[slotId] ?? `Slot ${slotId}`}</Text>
              </TouchableOpacity>
              <View style={styles.pickerWrap}>
                <Picker
                  selectedValue={ctx.equipment[slotId] ?? ''}
                  onValueChange={(v) => ctx.setEquipment(slotId, v ? Number(v) : null)}
                  style={styles.picker}
                  dropdownIconColor="#c69c44"
                >
                  <Picker.Item label="—" value="" color="#8b8f99" />
                  {(setsBySlot[slotId] ?? []).map((s) => (
                    <Picker.Item key={s.game_id} label={s.set_name} value={s.game_id} color="#e8e6e3" />
                  ))}
                </Picker>
              </View>
            </View>
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0c0e12' },
  content: { padding: 16, paddingBottom: 32 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0c0e12' },
  group: { marginBottom: 20 },
  groupTitle: { fontSize: 16, color: '#c69c44', marginBottom: 10, fontWeight: '600' },
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  slotLabel: { width: 100, paddingVertical: 8, paddingRight: 8 },
  slotLabelSelected: { backgroundColor: 'rgba(198, 156, 68, 0.2)', borderRadius: 6 },
  slotLabelText: { color: '#e8e6e3', fontSize: 14 },
  pickerWrap: { flex: 1, borderWidth: 1, borderColor: '#2a2d38', borderRadius: 8, backgroundColor: '#161922' },
  picker: { color: '#e8e6e3' },
  error: { color: '#a04545', padding: 16 },
});
