# Google AI Studio - Live API demo


## Model

links:

[Google AI Studio: Live API](https://ai.google.dev/gemini-api/docs/live?example=mic-stream)


[Gemini 2.5 Flash](https://ai.google.dev/gemini-api/docs/models#gemini-2.5-flash).  

models/gemini-2.5-flash-native-audio-preview-12-2025


## aistudio0.py

Code from 

https://aistudio.google.com/u/2/live?model=gemini-2.5-flash-native-audio-preview-12-2025

has many audio gaps when playing response audio from LLM,
because mic is listening while LLM sends the audio.  

## aistudio1.py

Adaption of aistudio0.py for last genai SDK and last LLM:   
models/gemini-2.5-flash-native-audio-preview-12-2025


## aistudio2.py

Code from 

https://ai.google.dev/gemini-api/docs/live?example=mic-stream

same issue with many gaps at audio play

## aistudio.py          <<<< DECENT PLAY OF LLM AUDIO

Based on aistudio1.py 

Added more instructions (Greek based replies)

Working better because is working at walkie-talkie mode

Mute mic when AI speaks

a. listening audio from microphone : listen_audio. 
b. then sending audio to Live API : send_realtime.  
c. then it receives audio from Live API: receive_audio.  
d. it plays the audio: play_audio. 


## preparation

requires latest python3

better via homebrew:

[brew installation](https://brew.sh/)

```
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

```

```
brew install python3
```

brew basic commands:

```
brew install [package]
brew remove [package]
brew list
brew info [package]
brew update
brew upgrade
```

requires uv python package manager

[uv](https://docs.astral.sh/uv/getting-started/installation/)

```
brew install uv

# or

curl -LsSf https://astral.sh/uv/install.sh | sh

# or 

wget -qO- https://astral.sh/uv/install.sh | sh
```

## installation

```
git clone https://github.com/kletin/liveapi

uv sync

```

## how to get a GEMINI_API_KEY

login to Google AI studio with a gmail account

[Google AI Studio - API Keys](https://aistudio.google.com/u/2/api-keys)

Get or Create a free tier Key :   
` Default Gemini API Key ` for `Default Gemini Project`

## how to test

one time per terminal session to activate virtual python environment

```
source .venv/bin/activate
```

one time per terminal session to setenv GEMINI_API_KEY

```
export GEMINI_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXX
```

```
python3 aistudio.py

# talk to LLM 1
Τι ώρα είναι τώρα ?
# wait for LLM reply
# talk to LLM 2
τι καιρό θα κάνει στη Θεσσαλονίκη αύριο ?
# wait for LLM reply
# talk to LLM 3
πότε παίζει ο ΠΑΟΚ ποδόσφαιρο τις επόμενες μέρες ?
```

Works in walkie-talkie mode, we don't talk while LLM is thinking or replying

Press `ctrl` + `C` to interrupt program



