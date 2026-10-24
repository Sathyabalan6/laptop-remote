export function getPresetDisplayName(name) {
  if (name === 'youtube_hotstar') {
    return 'YouTube / Hotstar';
  }

  if (name === 'vlc') {
    return 'VLC Player';
  }

  if (name === 'presentation') {
    return 'Presentation Deck';
  }

  return 'Universal / Netflix';
}

export function getPresetDescription(name) {
  if (name === 'youtube_hotstar') {
    return 'Optimized web shortcuts for YouTube & Hotstar (K, J, L, F, T, I)';
  }

  if (name === 'vlc') {
    return 'Full desktop VLC hotkeys (Space, Audio cycle, Aspect ratio)';
  }

  if (name === 'presentation') {
    return 'Slideshow controls, laser pointer & presentation stopwatch';
  }

  return 'Standard web media keys (Space, Arrow keys, F, M, S for intro)';
}

if (typeof window !== 'undefined') {
  window.presetLogic = {
    getPresetDisplayName,
    getPresetDescription
  };
}