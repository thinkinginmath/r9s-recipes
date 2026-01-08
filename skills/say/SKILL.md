---
name: say
description: Text-to-speech output using r9s audio API
compatibility: requires r9s CLI with audio API access and audio player (mpv, ffplay, afplay, or paplay)
metadata:
  author: r9s-ai
  version: 2.0.0
  tags: [tts, audio, speech]
---

# Text-to-Speech

Use this skill to speak words or phrases aloud via text-to-speech using the r9s audio API.

## Syntax

To speak text, output on its own line:

```
%{scripts/speak.sh "text to speak"}
```

## Configuration

Set environment variables to customize TTS:

- `R9S_TTS_MODEL` - TTS model to use (default: tts-1). Examples: tts-1, gpt-4o-mini-tts, speech-2.6-hd
- `R9S_TTS_VOICE` - Voice to use (default: alloy). Options: alloy, echo, fable, onyx, nova, shimmer
- `R9S_TTS_SPEED` - Speech speed 0.25-4.0 (default: 1.0)
- `R9S_TTS_FORMAT` - Audio format (default: mp3). Options: mp3, opus, aac, flac, wav, pcm

## Guidelines

- Place the command on its own line, separate from other content
- Use double quotes around the text
- For long narrations, keep text under 4096 characters
- You can use multiple speak commands in one response

## Examples

Pronounce a vocabulary word:
```
**serendipity** /ˌsɛrənˈdɪpɪti/

%{scripts/speak.sh "serendipity"}

**Definition**: The occurrence of pleasant discoveries by chance.
```

Full narration:
```
%{scripts/speak.sh "Let's explore the word ephemeral. E-phem-er-al. This beautiful word describes something that lasts for only a very short time."}
```

## Requirements

- r9s CLI installed with valid API key
- Audio player: mpv (recommended), ffplay, afplay (macOS), paplay, or aplay
- Run with `--allow-scripts` flag to enable script execution
