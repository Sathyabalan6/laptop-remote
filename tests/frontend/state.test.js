import { describe, expect, it, vi } from 'vitest';
import fs from 'node:fs';
import vm from 'node:vm';

const stateSource = fs.readFileSync(
  new URL('../../src/laptop_remote/static/js/state.js', import.meta.url),
  'utf8'
);

function loadState() {
  const storage = new Map();
  const toastCalls = [];

  const buttons = [
    {
      id: 'preset-btn-universal',
      classList: {
        toggle: vi.fn()
      },
      setAttribute: vi.fn()
    },
    {
      id: 'preset-btn-vlc',
      classList: {
        toggle: vi.fn()
      },
      setAttribute: vi.fn()
    }
  ];

  const context = {
    localStorage: {
      getItem: vi.fn(key => storage.get(key) ?? null),
      setItem: vi.fn((key, value) => storage.set(key, String(value)))
    },

    navigator: {
      vibrate: vi.fn(),
      wakeLock: undefined
    },

    document: {
      addEventListener: vi.fn(),
      querySelectorAll: vi.fn(selector => {
        if (selector === '.preset-btn') {
          return buttons;
        }

        return [];
      }),
      getElementById: vi.fn()
    },

    window: {
      presetLogic: {
        getPresetDisplayName: vi.fn(name => {
          if (name === 'vlc') {
            return 'VLC Player';
          }

          if (name === 'youtube_hotstar') {
            return 'YouTube / Hotstar';
          }

          return 'Universal / Netflix';
        })
      }
    },

    showToast: message => {
      toastCalls.push(message);
    },

    setTimeout,
    clearTimeout,
    setInterval,
    clearInterval,
    console
  };

  context.globalThis = context;

  vm.createContext(context);

  vm.runInContext(
    stateSource + `
      this.setPreset = setPreset;
    `,
    context
  );

  return {
    context,
    buttons,
    toastCalls
  };
}

describe('setPreset', () => {
  it('updates the selected preset and localStorage', () => {
    const { context } = loadState();

    context.setPreset('vlc');

    expect(context.localStorage.setItem).toHaveBeenCalledWith(
      'player_preset',
      'vlc'
    );
  });

  it('updates the active preset button', () => {
    const { context, buttons } = loadState();

    context.setPreset('vlc');

    expect(buttons[0].classList.toggle).toHaveBeenCalledWith(
      'active',
      false
    );

    expect(buttons[1].classList.toggle).toHaveBeenCalledWith(
      'active',
      true
    );
  });

  it('uses the preset logic helper for manual preset selection', () => {
  const { context } = loadState();

  context.setPreset('vlc');

  expect(
    context.window.presetLogic.getPresetDisplayName
  ).toHaveBeenCalledWith('vlc');
});

  it('skips vibration and toast for automatic preset changes', () => {
    const { context, toastCalls } = loadState();

    context.setPreset('vlc', true);

    expect(context.navigator.vibrate).not.toHaveBeenCalled();
    expect(toastCalls).toHaveLength(0);
  });
});