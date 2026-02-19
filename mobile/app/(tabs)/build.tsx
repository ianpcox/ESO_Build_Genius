import { useBuild } from './_layout';
import { api, postBuild, type BuildFull } from '../../lib/api';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';

type Option = { id: number; name: string };
type MundusFoodPotion = { mundus_id?: number; food_id?: number; potion_id?: number; name: string };

export default function BuildTab() {
  const ctx = useBuild();
  const [classes, setClasses] = useState<Option[]>([]);
  const [races, setRaces] = useState<Option[]>([]);
  const [roles, setRoles] = useState<Option[]>([]);
  const [mundus, setMundus] = useState<MundusFoodPotion[]>([]);
  const [foods, setFoods] = useState<MundusFoodPotion[]>([]);
  const [potions, setPotions] = useState<MundusFoodPotion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);
  const [loadIdInput, setLoadIdInput] = useState('');

  const getBarSkillsPayload = () => {
    const out: { bar_slot_ord: number; ability_id: number; scribe_effect_id_1: number | null; scribe_effect_id_2: number | null; scribe_effect_id_3: number | null }[] = [];
    for (let ord = 1; ord <= 12; ord++) {
      const cur = ctx.barSkills[ord];
      if (!cur?.ability_id) continue;
      out.push({
        bar_slot_ord: ord,
        ability_id: cur.ability_id,
        scribe_effect_id_1: cur.scribe_effect_id_1 ?? null,
        scribe_effect_id_2: cur.scribe_effect_id_2 ?? null,
        scribe_effect_id_3: cur.scribe_effect_id_3 ?? null,
      });
    }
    return out;
  };

  const saveBuild = async () => {
    if (ctx.buildId == null) return;
    const payload: Record<string, unknown> = {
      build_id: ctx.buildId,
      equipment: Object.entries(ctx.equipment).map(([slotId, gameId]) => ({ slot_id: Number(slotId), game_id: gameId })),
      bar_skills: getBarSkillsPayload(),
    };
    if (ctx.recommendedBuildId != null) {
      payload.recommended_build_id = ctx.recommendedBuildId;
      if (ctx.classId != null && ctx.raceId != null && ctx.roleId != null && ctx.mundusId != null && ctx.foodId != null && ctx.potionId != null) {
        payload.class_id = ctx.classId;
        payload.race_id = ctx.raceId;
        payload.role_id = ctx.roleId;
        payload.mundus_id = ctx.mundusId;
        payload.food_id = ctx.foodId;
        payload.potion_id = ctx.potionId;
      }
    } else {
      if (ctx.classId == null || ctx.raceId == null || ctx.roleId == null || ctx.mundusId == null || ctx.foodId == null || ctx.potionId == null) {
        setSaveStatus('Set class, race, role, mundus, food, and potion to create a new build.');
        return;
      }
      payload.class_id = ctx.classId;
      payload.race_id = ctx.raceId;
      payload.role_id = ctx.roleId;
      payload.mundus_id = ctx.mundusId;
      payload.food_id = ctx.foodId;
      payload.potion_id = ctx.potionId;
    }
    try {
      const res = await postBuild(payload);
      ctx.setRecommendedBuildId(res.recommended_build_id);
      setSaveStatus('Saved as build #' + res.recommended_build_id);
    } catch (e) {
      setSaveStatus((e as Error).message || 'Save failed.');
    }
  };

  const loadBuildById = async () => {
    const id = parseInt(loadIdInput, 10);
    if (!id || ctx.buildId == null) return;
    try {
      const data = await api.build(id) as BuildFull;
      if (data.class_id != null) ctx.setClassId(data.class_id);
      if (data.race_id != null) ctx.setRaceId(data.race_id);
      if (data.role_id != null) ctx.setRoleId(data.role_id);
      if (data.mundus_id != null) ctx.setMundusId(data.mundus_id);
      if (data.food_id != null) ctx.setFoodId(data.food_id);
      if (data.potion_id != null) ctx.setPotionId(data.potion_id);
      if (data.equipment && data.equipment.length > 0) {
        const eq: Record<number, number> = {};
        data.equipment.forEach((item) => { eq[item.slot_id] = item.game_id; });
        ctx.setEquipmentAll(eq);
      }
      if (data.bar_skills) ctx.setBarSkillsFromLoaded(data.bar_skills);
      if (data.recommended_build_id != null) ctx.setRecommendedBuildId(data.recommended_build_id);
      setSaveStatus('Loaded build #' + data.recommended_build_id);
    } catch (e) {
      setSaveStatus((e as Error).message || 'Load failed.');
    }
  };

  useEffect(() => {
    if (ctx.buildId == null) {
      setLoading(false);
      setError('No build loaded. Set API URL on the first screen.');
      return;
    }
    setError(null);
    Promise.all([
      api.classes(),
      api.races(),
      api.roles(),
      api.mundus(ctx.buildId),
      api.foods(ctx.buildId),
      api.potions(ctx.buildId),
    ])
      .then(([c, r, ro, m, f, p]) => {
        setClasses(c);
        setRaces(r);
        setRoles(ro);
        setMundus(m);
        setFoods(f);
        setPotions(p);
      })
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [ctx.buildId]);

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#c69c44" />
      </View>
    );
  }
  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  const pickerStyle = { color: '#e8e6e3', backgroundColor: '#161922' };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.label}>Class</Text>
      <View style={styles.pickerWrap}>
        <Picker
          selectedValue={ctx.classId ?? ''}
          onValueChange={(v) => ctx.setClassId(v ? Number(v) : null)}
          style={pickerStyle}
          dropdownIconColor="#c69c44"
        >
          <Picker.Item label="— Select —" value="" color="#8b8f99" />
          {classes.map((c) => (
            <Picker.Item key={c.id} label={c.name} value={c.id} color="#e8e6e3" />
          ))}
        </Picker>
      </View>
      <Text style={styles.label}>Race</Text>
      <View style={styles.pickerWrap}>
        <Picker
          selectedValue={ctx.raceId ?? ''}
          onValueChange={(v) => ctx.setRaceId(v ? Number(v) : null)}
          style={pickerStyle}
          dropdownIconColor="#c69c44"
        >
          <Picker.Item label="— Select —" value="" color="#8b8f99" />
          {races.map((r) => (
            <Picker.Item key={r.id} label={r.name} value={r.id} color="#e8e6e3" />
          ))}
        </Picker>
      </View>
      <Text style={styles.label}>Role</Text>
      <View style={styles.pickerWrap}>
        <Picker
          selectedValue={ctx.roleId ?? ''}
          onValueChange={(v) => ctx.setRoleId(v ? Number(v) : null)}
          style={pickerStyle}
          dropdownIconColor="#c69c44"
        >
          <Picker.Item label="— Select —" value="" color="#8b8f99" />
          {roles.map((r) => (
            <Picker.Item key={r.id} label={r.name} value={r.id} color="#e8e6e3" />
          ))}
        </Picker>
      </View>
      <Text style={styles.label}>Mundus</Text>
      <View style={styles.pickerWrap}>
        <Picker
          selectedValue={ctx.mundusId ?? ''}
          onValueChange={(v) => ctx.setMundusId(v ? Number(v) : null)}
          style={pickerStyle}
          dropdownIconColor="#c69c44"
        >
          <Picker.Item label="— Select —" value="" color="#8b8f99" />
          {mundus.map((m) => (
            <Picker.Item key={'m-' + (m.mundus_id ?? 0)} label={m.name} value={m.mundus_id ?? ''} color="#e8e6e3" />
          ))}
        </Picker>
      </View>
      <Text style={styles.label}>Food / Drink</Text>
      <View style={styles.pickerWrap}>
        <Picker
          selectedValue={ctx.foodId ?? ''}
          onValueChange={(v) => ctx.setFoodId(v ? Number(v) : null)}
          style={pickerStyle}
          dropdownIconColor="#c69c44"
        >
          <Picker.Item label="— Select —" value="" color="#8b8f99" />
          {foods.map((f) => (
            <Picker.Item key={'f-' + (f.food_id ?? 0)} label={f.name} value={f.food_id ?? ''} color="#e8e6e3" />
          ))}
        </Picker>
      </View>
      <Text style={styles.label}>Potion</Text>
      <View style={styles.pickerWrap}>
        <Picker
          selectedValue={ctx.potionId ?? ''}
          onValueChange={(v) => ctx.setPotionId(v ? Number(v) : null)}
          style={pickerStyle}
          dropdownIconColor="#c69c44"
        >
          <Picker.Item label="— Select —" value="" color="#8b8f99" />
          {potions.map((p) => (
            <Picker.Item key={'p-' + (p.potion_id ?? 0)} label={p.name} value={p.potion_id ?? ''} color="#e8e6e3" />
          ))}
        </Picker>
      </View>
      <View style={styles.persistSection}>
        <TouchableOpacity style={styles.saveButton} onPress={saveBuild}>
          <Text style={styles.saveButtonText}>Save build</Text>
        </TouchableOpacity>
        {saveStatus != null && <Text style={styles.saveStatus}>{saveStatus}</Text>}
        <Text style={styles.label}>Load build ID</Text>
        <View style={styles.loadRow}>
          <TextInput
            style={styles.loadInput}
            value={loadIdInput}
            onChangeText={setLoadIdInput}
            placeholder="recommended_build_id"
            placeholderTextColor="#8b8f99"
            keyboardType="number-pad"
          />
          <TouchableOpacity style={styles.loadButton} onPress={loadBuildById}>
            <Text style={styles.loadButtonText}>Load</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0c0e12' },
  content: { padding: 16, paddingBottom: 32 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#0c0e12' },
  label: { fontSize: 14, color: '#c69c44', marginBottom: 4, marginTop: 12 },
  pickerWrap: { borderWidth: 1, borderColor: '#2a2d38', borderRadius: 8, backgroundColor: '#161922' },
  error: { color: '#a04545', padding: 16 },
  persistSection: { marginTop: 20, paddingTop: 16, borderTopWidth: 1, borderTopColor: '#2a2d38' },
  saveButton: { backgroundColor: '#c69c44', padding: 12, borderRadius: 8, alignItems: 'center' },
  saveButtonText: { color: '#0c0e12', fontWeight: '600' },
  saveStatus: { marginTop: 8, fontSize: 12, color: '#8b8f99' },
  loadRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 6 },
  loadInput: { flex: 1, borderWidth: 1, borderColor: '#2a2d38', borderRadius: 8, backgroundColor: '#161922', padding: 10, color: '#e8e6e3', fontSize: 14 },
  loadButton: { backgroundColor: '#161922', padding: 10, borderRadius: 8, borderWidth: 1, borderColor: '#2a2d38' },
  loadButtonText: { color: '#c69c44', fontWeight: '500' },
});
