# Mobile Development Setup

## Running the App

### For Simulators/Emulators (Default)

These use localhost addresses that work for simulators/emulators:

```bash
# iOS Simulator
npm run ios:simulator
# or just
npm run ios

# Android Emulator
npm run android:emulator
# or just
npm run android
```

**Default API URLs:**

- iOS Simulator: `http://127.0.0.1:8000`
- Android Emulator: `http://10.0.2.2:8000`

---

### For Real Devices on LAN

These set the API URL to your computer's LAN IP:

```bash
# iOS Device
npm run ios:device

# Android Device
npm run android:device

# Or just start Metro and scan QR code
npm run start:device
```

**API URL:** `http://192.168.4.188:8000` (your computer's current LAN IP)

**Important:** Update the IP in `package.json` if your computer's IP changes!

---

## Finding Your Computer's LAN IP

### macOS:

```bash
ipconfig getifaddr en0
```

### Linux:

```bash
hostname -I | awk '{print $1}'
```

### Windows:

```bash
ipconfig
# Look for "IPv4 Address" under your WiFi adapter
```

---

## Backend Setup

Make sure your backend is running and accessible on your network:

```bash
cd ../backend
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

The `--host 0.0.0.0` is crucial - it allows devices on your LAN to connect!

---

## Environment Variables

The app uses these environment variables:

### Development

- `EXPO_PUBLIC_DEV_API_URL`: API URL for real devices (set in npm scripts)
  - If not set, falls back to simulator/emulator defaults

### Production

- `EXPO_PUBLIC_API_BASE_URL`: API URL for EAS builds
  - Set in `eas.json` for each build profile

---

## Troubleshooting

### "Network Error" on Real Device

1. Check your computer's LAN IP hasn't changed
2. Update the IP in `package.json` scripts if needed
3. Make sure backend is running with `--host 0.0.0.0`
4. Check both devices are on the same WiFi network

### "Network Error" on Emulator

1. Use the default scripts (without `:device`)
2. Make sure backend is running on `localhost:8000`
3. For Android emulator, `10.0.2.2` maps to host's `localhost`
