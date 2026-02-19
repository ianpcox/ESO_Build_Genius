# ESO Build Genius – Mobile (Expo Go)

React Native app that uses the same Flask API as the web UI. Run in **Expo Go** on your phone or simulator.

## Prerequisites

- Node.js 18+
- Expo Go app on your phone ([iOS](https://apps.apple.com/app/expo-go/id982107779) / [Android](https://play.google.com/store/apps/details?id=host.exp.exponent))
- ESO Build Genius backend running (see below)

## 1. Run the API server (same machine or LAN)

From the **project root** (not `mobile/`):

```bash
# Create DB and ingest data if you haven't already
python scripts/create_db.py
# ... run ingest scripts as needed ...

# Start the web server so the mobile app can call the API.
# For Expo Go on a real device, bind to all interfaces so your phone can reach it:
set ESO_BUILD_GENIUS_HOST=0.0.0.0
python web/app.py
```

Leave this running. Note your computer's LAN IP (e.g. `192.168.1.5`). On Windows: `ipconfig`; on macOS/Linux: `ifconfig` or `ip addr`.

## 2. Install and start the mobile app

```bash
cd mobile
npm install
npx expo start
```

- **Phone:** Open the Expo Go app, scan the QR code from the terminal (or from the browser that opens).
- **Simulator:** Press `i` (iOS) or `a` (Android) in the terminal.

## 3. Connect to the API

On first launch you'll see the **ESO Build Genius** welcome screen.

1. Enter the API base URL, e.g. `http://192.168.1.5:5000` (use your PC's IP and port 5000).
2. Tap **Save & Connect**. If the server is running and reachable, you'll be taken to the Build tab.

The URL is stored on device; next time you open the app you can go straight to the tabs (or change the URL by clearing app data or re-entering it if we add a settings screen).

## Tabs

- **Build** – Class, Race, Role, Mundus, Food, Potion (same as web).
- **Equipment** – 14 slots (Body, Jewelry, Front/Back bar). Tap a slot label to select it; Advisor uses the selected slot.
- **Advisor** – Set recommendations for the selected equipment slot (with buff redundancy).
- **Skills** – 12-skill bar with base ability + optional Focus / Signature / Affix scripts (scribing). Select class on Build first.

## CORS and network

The Flask app sends `Access-Control-Allow-Origin: *` so the mobile app can call the API from another host. For **Expo Go on a physical device**, the device and the machine running `web/app.py` must be on the same network, and you must start the server with `ESO_BUILD_GENIUS_HOST=0.0.0.0` and use the machine's LAN IP in the app.

## Development

- **Expo SDK:** 52
- **Entry:** `expo-router` (file-based routing under `app/`).
- **State:** Build context (buildId, class, race, equipment, selected slot) is shared across tabs via `app/(tabs)/_layout.tsx`.
- **API client:** `lib/api.ts`; base URL is set on the welcome screen and stored in AsyncStorage.
