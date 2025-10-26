# 🎥 Video Intelligence API Agent
> **Purpose**: Seamlessly transform clinical trial documents into engaging educational videos through automated content analysis and multi-modal generation.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Pillow](https://img.shields.io/badge/Pillow-10.0+-green.svg)
![NLTK](https://img.shields.io/badge/NLTK-3.8+-orange.svg)

## 🎯 Motivation
The Video Intelligence API Agent solves a critical challenge in medical communication: converting complex clinical trial documentation into accessible, engaging video content. By automating the entire pipeline from text analysis to video generation, it enables:

- Automatic separation of mechanism/biological content from trial logistics
- Smart visualization of statistics and key metrics
- Consistent visual style inspired by educational content creators
- Text-to-speech narration with fallback options
- Modular architecture supporting multiple AI services

## 🔑 Core Features

### Content Processing
- Intelligent parsing of clinical trial documents
- Automatic categorization of content (mechanisms vs. trial info)
- Statistical pattern extraction and visualization
- Clean text preparation for narration

### Visual Generation
- Dual-mode slide generation:
  - Bio/cell mechanisms: Full-screen illustrated visualizations
  - Trial info: Split-layout with text + dynamic statistics
- Amoeba Sisters-inspired educational style
- Automatic layout and typography management

### Audio Synthesis
- Primary: Fish Audio API integration
- Fallback: Local TTS via pyttsx3
- Silent WAV generation as final fallback

## 🏗 Architecture

```
Document → Parser → Content Classifier
                     ↙            ↘
         Mechanism Generator    Trial Info Generator
                     ↘            ↓
                      Audio Generator
                           ↓
                    Manifest Builder
```

## 📋 Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd video-api
```

2. Install dependencies:
```bash
pip install pillow requests nltk python-dotenv pyttsx3 pollinations
```

3. Create .env file:
```bash
FISH_API_KEY=your_fish_audio_key_here
USE_LOCAL_TTS=1  # Optional: force local TTS
```

4. Prepare your input:
- Place your clinical trial document as `paper_2_sample.txt`
- Use section markers (-----) to separate content
- Include Category, Content, and Agent Functions fields

## 🚀 Usage

Basic usage:
```python
from image_maker_2 import AIVideoAgent, parse_paper_file

# Initialize agent
agent = AIVideoAgent(fish_key="your_key_here")

# Process document
mechanism_sections, trial_sections = parse_paper_file("paper_2_sample.txt")

# Generate content
mechanism_paths = []
trial_paths = []
audio_paths = []

# Generate slides and audio
for section in mechanism_sections:
    img_path = agent.generate_mechanism_image(section['content'], len(mechanism_paths)+1)
    mechanism_paths.append(img_path)
    
for section in trial_sections:
    img_path = agent.generate_trial_slide(section['content'], len(trial_paths)+1)
    trial_paths.append(img_path)
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Guidelines
- Use consistent code formatting
- Add docstrings for new functions
- Test all fallback paths
- Secure handling of API keys
- Support for multiple input formats

## 🎯 Vision & Impact

The Video Intelligence API Agent represents a significant step forward in medical communication accessibility. By automating the transformation of complex clinical trial documentation into engaging, educational video content, we bridge the gap between medical researchers and the general public.

Our agent's ability to distinguish between mechanical/biological concepts and trial logistics, combined with its intelligent visualization strategies, ensures that each piece of content is presented in the most effective way possible. The dual-mode presentation system—using full-screen illustrations for biological mechanisms and split-layout designs for trial information—makes complex medical concepts more approachable while maintaining scientific accuracy.

This tool has the potential to democratize medical knowledge by making clinical trial information more accessible to patients, medical students, and healthcare providers. By combining multiple AI services with fallback options, we ensure reliable operation while maintaining the flexibility to incorporate new technologies as they emerge.

## 📄 License

MIT License - see LICENSE.md

---
*Inspired by CalHacks 12.0 Project Style*