# 🎙️ Voice Tutor: The Empathetic AI Coding Teacher

[![Status: Proof of Concept](https://img.shields.io/badge/Status-Proof_of_Concept-orange.svg)]()
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)]()

Meet **Voice Tutor**, a hands-free, intelligent voice assistant that teaches you how to code just like a human mentor would. You talk to it directly in your browser. It evaluates your current knowledge, creates a personalized lesson plan, and guides you step-by-step.

But what makes Voice Tutor truly revolutionary? **It listens to *how* you feel.** 

## 🌟 Why Voice Tutor?

### 🧠 Emotion-Aware Teaching
Ever felt frustrated when a tutorial moves too fast? Voice Tutor uses **advanced emotion detection APIs** to analyze your voice tone in real-time. If it detects **confusion or frustration**, it automatically:
- Slows down the pace of the lesson.
- Breaks down complex topics into smaller, bite-sized steps.
- Uses relatable, everyday analogies to bridge the gap.

*The result? A tutor that adapts to your emotional state, keeping you engaged and preventing burnout.*

### 📚 The "Probe → Plan → Teach" Pedagogy
Voice Tutor doesn't just read documentation to you. It uses a proven teaching methodology:
1. **Probe:** It discovers what you want to learn and asks quick questions to find the boundaries of your knowledge.
2. **Plan:** It proposes a structured, multi-step lesson plan tailored to your goal and waits for your green light.
3. **Teach:** It guides you through each step, checks your understanding with interactive quizzes, and ensures you've mastered the concept before moving forward.

### 🔍 Fact-Checked & Accurate
Powered by web search APIs in the background, Voice Tutor cross-references its explanations with real-time web data to ensure you're getting the most accurate and up-to-date coding knowledge.

---

## 🚀 Getting Started

Ready to experience empathetic AI tutoring? Follow these steps to get your local environment running.

### Prerequisites
- **Python 3.11+**
- **Google Chrome** (Required for the built-in Web Speech API)

### 1. Setup the Environment

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Your API Keys

Copy the example environment file:
```bash
cp .env.example .env
```

Open `backend/.env` and add your keys:
- **`OPENAI_API_KEY`**: Your Gemini API key (or any OpenAI-compatible provider).
- **`LLM_MODEL`**: e.g., `gemini-flash-lite-latest` (recommended for low-latency voice interactions).
- **`TAVILY_API_KEY`**: For real-time web fact-checking.
- **`MODULATE_API_KEY`**: To power the magical emotion detection! *(Note: The current implementation uses a placeholder endpoint for Modulate, but the architecture is ready for your key!)*

> **Security Tip:** Never commit your `.env` file! We've already added it to `.gitignore` to keep your keys safe.

### 3. Run the Tutor

Start the unified server (which handles both the FastAPI backend and serves the frontend):
```bash
# Ensure you are still in the backend directory with venv activated
python -m uvicorn main:app --port 8000
```

Open **http://localhost:8000** in Google Chrome, grant microphone permissions, tap the circle, and just start talking! 

---

## 🏗️ Under the Hood

Voice Tutor orchestrates a powerful symphony of APIs in real-time:

1. **Speech-to-Text:** Chrome's built-in Web Speech API transcribes your voice instantly.
2. **Parallel Processing:**
   - **Web Search** looks up relevant context.
   - **Emotion APIs** analyze the audio recording for emotional cues (confusion, frustration).
3. **Brain (Gemini):** Processes the transcript, web facts, and your emotional state to formulate a personalized, empathetic response.
4. **Text-to-Speech:** Uses text-to-speech engines to generate the audio response, streamed directly back to you.

## 🛠️ Tuning & Customization

- **Adjust Turn Length:** Modify `SILENCE_MS` in `frontend/app.js` (default `1500` ms). Increase it if you tend to pause frequently while thinking.
- **Modify Teaching Style:** Tweak the `SYSTEM_PROMPT` inside `backend/teacher_agent.py` to change the tutor's personality.

## 🔮 Roadmap

- [ ] **Live Emotion Integration:** Fully wire up the emotion detection API in `modulate_integration.py`.
- [ ] **Phone Support:** Native phone call capabilities via **Plivo**.
- [ ] **Barge-In:** Allow students to talk over the tutor with active echo cancellation.
- [ ] **Visual Code Snippets:** Display code blocks dynamically on-screen while the tutor speaks.
