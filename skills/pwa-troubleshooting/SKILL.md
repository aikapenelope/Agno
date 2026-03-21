---
name: pwa-troubleshooting
description: Troubleshooting guide for Progressive Web Apps — installation, caching, service workers, microphone permissions, and browser-specific issues across iOS, Android, and desktop.
metadata:
  version: "1.0.0"
  tags: [pwa, troubleshooting, mobile, browser, cache, service-worker]
---

# PWA Troubleshooting

Reference for Aurora support agents handling technical issues.
Guide users step by step — assume zero technical knowledge.

## Installation Issues

### "Can't find install button"
| Browser | How to Install |
|---------|---------------|
| Chrome (Android) | Menu (3 dots) → "Add to Home Screen" or "Install app" |
| Chrome (Desktop) | Address bar → install icon (monitor with arrow) |
| Safari (iOS) | Share button (square with arrow) → "Add to Home Screen" |
| Firefox | Not supported for PWA install (use Chrome) |
| Samsung Internet | Menu → "Add page to" → "Home screen" |

### "Install button doesn't appear"
1. Check the URL is HTTPS (not HTTP)
2. Clear browser cache and reload
3. Check if already installed (look in app drawer)
4. Try incognito/private mode
5. On iOS: ONLY Safari supports PWA install

### "App doesn't work offline"
- PWA needs first load with internet to cache resources
- Check: Settings → Apps → Aurora → Storage → Cache (should be > 0)
- Try: uninstall, reconnect to internet, reinstall

## Microphone Issues (critical for Aurora)

### "Microphone not working"
1. Check browser permissions: Settings → Site Settings → Microphone → Allow
2. Check OS permissions: Settings → Privacy → Microphone → Allow for browser
3. On iOS: Settings → Safari → Microphone → Allow
4. Test: open any voice recorder app to verify mic works
5. If headphones connected: check headphone mic is selected

### "Voice recognition is inaccurate"
- Speak clearly, at normal pace
- Reduce background noise
- Hold phone 15-30cm from mouth
- Check language setting matches your language
- Groq Whisper works best with: clear speech, minimal accent, quiet environment

## Cache & Update Issues

### "App shows old version"
1. Open Aurora in browser (not installed PWA)
2. Hard refresh: Ctrl+Shift+R (desktop) or pull-to-refresh (mobile)
3. Clear site data: Settings → Privacy → Clear browsing data → select Aurora's domain
4. Uninstall PWA and reinstall

### "App is slow"
- Clear cache (see above)
- Check internet connection speed
- Close other tabs/apps
- On older devices: reduce number of stored notes/tasks

## Browser-Specific Quirks

| Issue | iOS Safari | Chrome Android | Chrome Desktop |
|-------|-----------|---------------|----------------|
| Push notifications | Not supported (iOS 16.4+ only) | Supported | Supported |
| Background sync | Limited | Supported | Supported |
| Mic in PWA | Works | Works | Works |
| File upload | Works (camera + files) | Works | Works |
| Fullscreen | Standalone mode only | Supported | Supported |
