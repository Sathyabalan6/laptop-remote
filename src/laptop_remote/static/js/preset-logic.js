export function getPresetDisplayName(name) {
  if (name === 'youtube_hotstar') {
    return 'YouTube / Hotstar';
  }

  if (name === 'vlc') {
    return 'VLC Player';
  }

  return 'Universal / Netflix';
}

if (typeof window !== 'undefined') {
  window.presetLogic = {
    getPresetDisplayName
  };
}