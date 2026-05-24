/**
 * Shadiro luxury design tokens — matte black, champagne gold, ivory.
 * Use with react-native-paper theme merge in App.js.
 * Typography: map display/body to system serif/sans until custom fonts are loaded.
 */
import { Platform } from 'react-native';

export const luxuryColors = {
  matteBlack: '#0C0A09',
  matteBlackSoft: '#1C1917',
  champagneGold: '#C9A962',
  champagneGoldMuted: 'rgba(201, 169, 98, 0.35)',
  ivory: '#FAF8F5',
  ivoryMuted: '#E7E5E4',
  glassBorder: 'rgba(255,255,255,0.12)',
  success: '#22C55E',
  danger: '#EF4444',
};

export const luxuryGradients = {
  hero: ['#0C0A09', '#292524', '#1C1917'],
  goldShimmer: ['#C9A962', '#E8D5A3', '#C9A962'],
};

export const luxuryTypography = {
  display: {
    fontFamily: Platform.select({ ios: 'Georgia', android: 'serif', default: 'serif' }),
    fontWeight: '600',
    letterSpacing: 0.4,
  },
  body: {
    fontFamily: Platform.select({ ios: 'System', android: 'sans-serif', default: 'sans-serif' }),
    letterSpacing: 0.15,
  },
};
