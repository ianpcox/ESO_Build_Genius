import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, setBaseUrl, testConnection } from '../lib/api';

const STORAGE_KEY = 'eso_build_genius_api_url';

export default function WelcomeScreen() {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState<string | null>(null);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((stored) => {
      if (stored) {
        setUrl(stored);
        setSaved(stored);
      } else {
        setUrl('http://192.168.1.1:5000');
      }
    });
  }, []);

  const handleSaveAndConnect = async () => {
    const base = url.trim().replace(/\/+$/, '');
    if (!base.startsWith('http://') && !base.startsWith('https://')) {
      Alert.alert('Invalid URL', 'URL must start with http:// or https://');
      return;
    }
    setLoading(true);
    try {
      setBaseUrl(base);
      const ok = await testConnection();
      if (ok) {
        await AsyncStorage.setItem(STORAGE_KEY, base);
        setSaved(base);
        router.replace('/(tabs)/build');
      } else {
        Alert.alert(
          'Connection failed',
          'Could not reach the API. Ensure the web server is running (python web/app.py) and use your computer\'s LAN IP, e.g. http://192.168.1.5:5000'
        );
      }
    } catch (e) {
      Alert.alert('Error', (e as Error).message || 'Connection failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>ESO Build Genius</Text>
      <Text style={styles.subtitle}>Mobile (Expo Go)</Text>
      <Text style={styles.hint}>
        Enter the URL of your ESO Build Genius API server. Run the web app on your computer with:
      </Text>
      <Text style={styles.code}>python web/app.py</Text>
      <Text style={styles.env}>Then set ESO_BUILD_GENIUS_HOST=0.0.0.0 and use your PC's IP below.</Text>
      <TextInput
        style={styles.input}
        value={url}
        onChangeText={setUrl}
        placeholder="http://192.168.1.5:5000"
        placeholderTextColor="#8b8f99"
        autoCapitalize="none"
        autoCorrect={false}
        editable={!loading}
      />
      {saved ? (
        <Text style={styles.saved}>Saved: {saved}</Text>
      ) : null}
      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleSaveAndConnect}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#0c0e12" />
        ) : (
          <Text style={styles.buttonText}>Save & Connect</Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0c0e12',
    padding: 24,
    justifyContent: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#c69c44',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#8b8f99',
    marginBottom: 24,
  },
  hint: {
    fontSize: 14,
    color: '#e8e6e3',
    marginBottom: 8,
  },
  code: {
    fontFamily: 'monospace',
    fontSize: 13,
    color: '#c69c44',
    marginBottom: 8,
  },
  env: {
    fontSize: 12,
    color: '#8b8f99',
    marginBottom: 16,
  },
  input: {
    backgroundColor: '#161922',
    borderWidth: 1,
    borderColor: '#2a2d38',
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
    color: '#e8e6e3',
    marginBottom: 8,
  },
  saved: {
    fontSize: 12,
    color: '#8b8f99',
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#c69c44',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: '#0c0e12',
    fontSize: 16,
    fontWeight: '600',
  },
});
