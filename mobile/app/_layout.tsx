import { DarkTheme, ThemeProvider } from '@react-navigation/native';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

const ESOTheme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    primary: '#c69c44',
    background: '#0c0e12',
    card: '#161922',
    text: '#e8e6e3',
    border: '#2a2d38',
  },
};

export default function RootLayout() {
  return (
    <ThemeProvider value={ESOTheme}>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: '#161922' },
          headerTintColor: '#c69c44',
          headerTitleStyle: { fontFamily: 'System', fontWeight: '600' },
          contentStyle: { backgroundColor: '#0c0e12' },
        }}
      >
        <Stack.Screen name="index" options={{ title: 'ESO Build Genius', headerBackVisible: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false, gestureEnabled: false }} />
      </Stack>
    </ThemeProvider>
  );
}
