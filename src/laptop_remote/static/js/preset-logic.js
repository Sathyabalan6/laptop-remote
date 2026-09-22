export function getPresetDisplayName(name) {
    if (name === 'youtube_hotstar') {
        return 'YouTube / Hotstar';
    }

    if (name === 'vlc') {
        return 'VLC Player';
    }
    if (typeof window !== 'undefined') {
        window.presetLogic = {
            getPresetDisplayName
        };
    }

    return 'Universal / Netflix';
}