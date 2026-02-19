import { useBuild, type BarSlot } from './_layout';
import { api } from '../../lib/api';
import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';

type ScribeEffect = { scribe_effect_id: number; name: string; slot_id: number; slot_name: string };
type SkillOption = { ability_id: number; name: string; skill_line_id: number | null; skill_line_name: string };

const SLOT_LABELS = ['1', '2', '3', '4', '5', 'Ult', '6', '7', '8', '9', '10', 'Ult'];

export default function SkillsTab() {
  const ctx = useBuild();
  const [scribeBySlot, setScribeBySlot] = useState<Record<number, ScribeEffect[]>>({ 1: [], 2: [], 3: [] });
  const [scribeEffectsByAbility, setScribeEffectsByAbility] = useState<Record<number, Record<number, ScribeEffect[]>>>({});
  const [skills, setSkills] = useState<SkillOption[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    if (ctx.buildId == null) return;
    const [effects, skillList] = await Promise.all([
      api.scribeEffects(ctx.buildId),
      api.skillsForBar(ctx.buildId, ctx.classId ?? undefined),
    ]);
    const bySlot: Record<number, ScribeEffect[]> = { 1: [], 2: [], 3: [] };
    effects.forEach((e) => bySlot[e.slot_id].push(e));
    setScribeBySlot(bySlot);
    setSkills(skillList);
    setLoading(false);
  }, [ctx.buildId, ctx.classId]);

  useEffect(() => {
    if (ctx.buildId == null) {
      setLoading(false);
      return;
    }
    setLoading(true);
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (ctx.buildId == null) return;
    const abilityIds = [...new Set([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((ord) => ctx.barSkills[ord]?.ability_id).filter((id): id is number => id != null))];
    abilityIds.forEach((abilityId) => {
      if (scribeEffectsByAbility[abilityId]) return;
      api.scribeEffects(ctx.buildId!, abilityId).then((list) => {
        const bySlot: Record<number, ScribeEffect[]> = { 1: [], 2: [], 3: [] };
        list.forEach((e) => bySlot[e.slot_id].push(e));
        setScribeEffectsByAbility((prev) => ({ ...prev, [abilityId]: bySlot }));
      });
    });
  }, [ctx.buildId, ctx.barSkills, scribeEffectsByAbility]);

  if (ctx.buildId == null) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>No build loaded. Set API URL on the first screen.</Text>
      </View>
    );
  }

  if (loading && skills.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#c69c44" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.hint}>Select class on Build tab, then pick ability and optional Focus / Signature / Affix per bar slot.</Text>
      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((ord) => {
        const cur = ctx.barSkills[ord] ?? {};
        const effectsForRow = cur.ability_id && scribeEffectsByAbility[cur.ability_id] ? scribeEffectsByAbility[cur.ability_id] : scribeBySlot;
        return (
          <View key={ord} style={styles.barRow}>
            {ord === 7 && <Text style={styles.barGroupTitle}>Back bar</Text>}
            {ord === 1 && <Text style={styles.barGroupTitle}>Front bar</Text>}
            <Text style={styles.barLabel}>{SLOT_LABELS[ord - 1]}</Text>
            <View style={styles.pickerWrap}>
              <Picker
                selectedValue={cur.ability_id ?? ''}
                onValueChange={(v) => ctx.setBarAbility(ord, v ? Number(v) : null)}
                style={styles.picker}
                dropdownIconColor="#c69c44"
              >
                <Picker.Item label="— Ability —" value="" color="#8b8f99" />
                {skills.map((s) => (
                  <Picker.Item
                    key={s.ability_id}
                    label={(s.skill_line_name ? s.skill_line_name + ': ' : '') + s.name}
                    value={s.ability_id}
                    color="#e8e6e3"
                  />
                ))}
              </Picker>
            </View>
            {[1, 2, 3].map((slotId) => (
              <View key={slotId} style={styles.scribeWrap}>
                <Picker
                  selectedValue={(cur as BarSlot)[`scribe_effect_id_${slotId}` as keyof BarSlot] ?? ''}
                  onValueChange={(v) => ctx.setBarScribe(ord, slotId, v ? Number(v) : null)}
                  style={styles.scribePicker}
                  dropdownIconColor="#c69c44"
                >
                  <Picker.Item label="—" value="" color="#8b8f99" />
                  {(effectsForRow[slotId] ?? []).map((e) => (
                    <Picker.Item key={e.scribe_effect_id} label={e.name} value={e.scribe_effect_id} color="#e8e6e3" />
                  ))}
                </Picker>
              </View>
            ))}
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0c0e12' },
  content: { padding: 16, paddingBottom: 32 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0c0e12' },
  hint: { color: '#8b8f99', fontSize: 12, marginBottom: 16 },
  barGroupTitle: { fontSize: 14, color: '#c69c44', fontWeight: '600', marginTop: 12, marginBottom: 4, width: '100%' },
  barRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6, flexWrap: 'wrap', gap: 6 },
  barLabel: { width: 28, color: '#e8e6e3', fontSize: 12 },
  pickerWrap: { flex: 1, minWidth: 120, borderWidth: 1, borderColor: '#2a2d38', borderRadius: 8, backgroundColor: '#161922' },
  picker: { color: '#e8e6e3', fontSize: 12 },
  scribeWrap: { width: 80, borderWidth: 1, borderColor: '#2a2d38', borderRadius: 8, backgroundColor: '#161922' },
  scribePicker: { color: '#e8e6e3', fontSize: 11 },
  error: { color: '#a04545', padding: 16 },
});
