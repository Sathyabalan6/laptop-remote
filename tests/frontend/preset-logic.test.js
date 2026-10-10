import { describe, expect, it } from 'vitest';
import { getPresetDisplayName, getPresetDescription } from '../../src/laptop_remote/static/js/preset-logic.js';

describe('getPresetDisplayName', () => {
  it('returns the default name for the universal preset', () => {
    expect(getPresetDisplayName('universal')).toBe('Universal / Netflix');
  });

  it('returns the YouTube / Hotstar name', () => {
    expect(getPresetDisplayName('youtube_hotstar')).toBe('YouTube / Hotstar');
  });

  it('returns the VLC name', () => {
    expect(getPresetDisplayName('vlc')).toBe('VLC Player');
  });

  it('falls back to the default name for an unknown preset', () => {
    expect(getPresetDisplayName('unknown')).toBe('Universal / Netflix');
  });
});

describe('getPresetDescription', () => {
  it('returns description for universal preset', () => {
    expect(getPresetDescription('universal')).toContain('Standard web media keys');
  });

  it('returns description for YouTube preset', () => {
    expect(getPresetDescription('youtube_hotstar')).toContain('YouTube & Hotstar');
  });

  it('returns description for VLC preset', () => {
    expect(getPresetDescription('vlc')).toContain('VLC');
  });
});