#!/bin/bash
# TTS script using r9s audio API
# Usage: speak.sh "text to speak"

set -e

TEXT="$1"
if [ -z "$TEXT" ]; then
    echo "Usage: speak.sh \"text to speak\"" >&2
    exit 1
fi

# Configuration via environment variables
MODEL="${R9S_TTS_MODEL:-tts-1}"
VOICE="${R9S_TTS_VOICE:-alloy}"
SPEED="${R9S_TTS_SPEED:-1.0}"
FORMAT="${R9S_TTS_FORMAT:-mp3}"

# Create temp file for audio
TMPFILE=$(mktemp /tmp/r9s-tts-XXXXXX.$FORMAT)
trap "rm -f $TMPFILE" EXIT

# Generate speech using r9s CLI
r9s audio speech "$TEXT" -o "$TMPFILE" --model "$MODEL" --voice "$VOICE" --speed "$SPEED" --format "$FORMAT" 2>/dev/null

# Play audio based on available player
if command -v mpv &>/dev/null; then
    mpv --no-terminal "$TMPFILE" 2>/dev/null
elif command -v ffplay &>/dev/null; then
    ffplay -nodisp -autoexit "$TMPFILE" 2>/dev/null
elif command -v afplay &>/dev/null; then
    # macOS
    afplay "$TMPFILE" 2>/dev/null
elif command -v paplay &>/dev/null; then
    # PulseAudio - convert to wav first if needed
    if [ "$FORMAT" = "wav" ]; then
        paplay "$TMPFILE" 2>/dev/null
    elif command -v ffmpeg &>/dev/null; then
        WAVFILE=$(mktemp /tmp/r9s-tts-XXXXXX.wav)
        trap "rm -f $TMPFILE $WAVFILE" EXIT
        ffmpeg -i "$TMPFILE" -f wav "$WAVFILE" -y 2>/dev/null
        paplay "$WAVFILE" 2>/dev/null
    fi
elif command -v aplay &>/dev/null; then
    # ALSA - needs wav format
    if [ "$FORMAT" = "wav" ]; then
        aplay "$TMPFILE" 2>/dev/null
    elif command -v ffmpeg &>/dev/null; then
        WAVFILE=$(mktemp /tmp/r9s-tts-XXXXXX.wav)
        trap "rm -f $TMPFILE $WAVFILE" EXIT
        ffmpeg -i "$TMPFILE" -f wav "$WAVFILE" -y 2>/dev/null
        aplay "$WAVFILE" 2>/dev/null
    fi
elif command -v play &>/dev/null; then
    # SoX
    play "$TMPFILE" 2>/dev/null
else
    echo "No audio player found. Install mpv, ffplay, or paplay." >&2
    exit 1
fi
