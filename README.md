# DESK-AI 🤖

DESK-AI is a Python-based desktop voice assistant that listens to user commands, understands natural language, executes system-level actions, and responds using text-to-speech. The project is built with a modular architecture, making it easy to extend and customize.

## Features

- 🎙️ Voice input using Speech-to-Text (STT)
- 🧠 Natural Language Processing (NLP)
- 🔊 Text-to-Speech (TTS) responses
- ⚙️ Command mapping and execution engine
- 🪵 Centralized error logging
- 🧩 Modular and extensible design
- 🖥️ Desktop-focused AI assistant

## Tech Stack

- Python 3
- Speech recognition libraries (configurable)
- Text-to-speech libraries (configurable)
- NLP utilities
- Standard Python modules

## Project structure

````markdown
DESK-AI/
│
├── __pycache__/          # Python cache files
├── logs/                 # Application logs
├── model/                # AI / NLP related models
├── venv/                 # Virtual environment (ignored in git)
│
├── command_mapper.py     # Maps user intent to executable commands
├── error_logger.py       # Centralized error handling & logging
├── execution_engine.py   # Executes mapped commands
├── nlp_engine.py         # Processes natural language input
├── stt_engine.py         # Speech-to-Text engine
├── tts_engine.py         # Text-to-Speech engine
├── voice_listener.py     # Listens continuously for voice input
│
├── UI.py                 # Desktop UI
├── main.py               # Application entry point
├── requirements.txt      # Project dependencies
└── .gitignore            # Git ignore rules
````

## Installation & Setup

1. Clone the repository

   git clone https://github.com/hrishikhapekar/DESK-AI.git
   cd DESK-AI

2. Create & activate a virtual environment (recommended)
   ``` bash
   python -m venv venv
   ```
   ### Windows
   ``` bash
   venv\Scripts\activate
   ```

3. Install dependencies
   ``` bash
   pip install -r requirements.txt
   ```

## Running

Make sure your microphone is enabled and accessible before running the application.

Start the assistant:
   ``` bash
      python UI.py
   ```
   OR
   ``` bash
      python main.py
   ```
## How it works (high-level flow)

1. voice_listener captures the user’s voice
2. stt_engine converts speech to text
3. nlp_engine understands the intent
4. command_mapper maps intent to commands
5. execution_engine performs the action
6. tts_engine responds back to the user
7. error_logger logs any errors

## Use cases

- Desktop automation using voice
- Learning AI assistant architecture
- Experimenting with NLP, STT, and TTS
- Base project for advanced AI assistants

## Future enhancements

- Wake-word detection
- Smarter NLP using ML models
- Integration with APIs (weather, calendar, email)
- Plugin-based command system
- Cross-platform support
- Packaging as a standalone .exe

## Contributing

Contributions are welcome!

1. Fork the repository
2. Create a new branch
3. Commit your changes
4. Open a Pull Request

Please follow the repository coding style and include tests where appropriate.

## License

This project is open-source and available under the MIT License.

---

*Contributers of this Project*
Akshay Thakur : @CodeArtisanAksahy
Hrishi Khapekar : @hrishikhapekar
Shrikant Agrawal : @agrawalsb
