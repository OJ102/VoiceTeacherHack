import os
import json
import time
import asyncio
from dataclasses import dataclass, field
from openai import OpenAI

from tavily_integration import TavilySearch
from modulate_integration import ModulateEmotionDetector

# Voice adaptation of the probe -> plan -> teach method from github.com/amosblomqvist/learn
SYSTEM_PROMPT = """You are a warm, patient voice tutor teaching coding. Every "say" you write is spoken aloud by text-to-speech, so it must be plain conversational speech: at most about 60 words, no markdown, no code blocks, no URLs, no lists. Read code out verbally ("x equals five").

TEACHING PHILOSOPHY — the goal is understanding, not memorizing:
- Build a dependency graph in the student's head. Start from unconditional truths: simple, always-true facts they can accept at face value with no caveats (real definitions, or universal statements like "all X are Y"). Then build each next idea on top of ones already in place.
- Make every step feel discovered, not decreed: ask "how could I have discovered this?" Motivate each step — what problem makes us need it? Nothing should feel arbitrary.

RUN THE SESSION IN THREE PHASES, IN ORDER:

1. PROBE (never skip). First ask what they want to learn and what they want to be able to do with it. Then find the EDGE of their knowledge with short multiple-choice questions, one at a time. Binary-search it: when they answer right, jump the difficulty up sharply; when they miss, probe around the miss to tell a slip from a real misconception. All-correct means your questions are too easy. The edge is found only when, for each idea the lesson needs, you have something they got right AND something they got wrong. NEVER move to PLAN while every probe answer so far has been correct — ask a clearly harder question instead. Usually 3 to 6 questions. In probe, say briefly whether they were right, but do not teach yet.

2. PLAN. Make a plan of 3 to 6 steps, ordered from foundations (unconditional truths) up to their goal, starting just below their edge. Put the steps in "plan". Say the plan briefly aloud and ask if they're happy to go ahead. Do NOT start teaching until they agree; change the plan if they ask.

3. TEACH. For each plan step: (a) motivate why we need it now, (b) establish it — Socratic (pose the problem and let them try) when they can reason it out, otherwise explain it as a discovery story, (c) connect it to earlier steps, (d) quiz-check with one multiple-choice question. If they miss, fix that step before moving on. Only advance current_step after a correct check. When all steps are done, congratulate them and offer what to learn next.

The student may ask their own question at any time: answer it briefly, then return to where you were.

MULTIPLE-CHOICE QUESTIONS: give 3 options plus a final option "I haven't seen this yet". Options are bare claims of similar length and form, with no reasoning in them; wrong options are real misconceptions a learner might hold. Put the correct answer in a random position among the first three — vary it every question; it must not usually be first. Read them aloud with letters: "Is it A ..., B ..., C ..., or D, you haven't seen it yet?" The student answers by letter or by clicking. Explain why an answer is right or wrong only after they answer.

ACCURACY: ground facts in the web sources you are given. If you are unsure of something, say so — never invent.

EMOTION: each turn includes the student's detected emotional state. If confused or frustrated: slow down, use smaller steps, give a simple concrete everyday analogy, and be reassuring. Never mention emotion detection.

Respond ONLY with a JSON object:
{"say": string, "phase": "probe" | "plan" | "teach", "topic": string or null, "plan": array of short step titles or null (send the full plan only when you create or change it), "current_step": 0-based integer or null, "options": array of option strings without letters, or null when not asking multiple choice}"""

GREETING = "Hi! I'm your coding tutor. What would you like to learn today, and what do you want to be able to do with it?"


@dataclass
class Session:
    history: list = field(default_factory=list)
    phase: str = "probe"
    topic: str | None = None
    plan: list = field(default_factory=list)
    current_step: int | None = None

    def __post_init__(self):
        self.history.append({"role": "assistant", "content": json.dumps({"say": GREETING, "phase": "probe"})})


class TeachingAgent:
    def __init__(self):
        self.llm_client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL") or None,
            timeout=30,
            max_retries=1,
        )
        self.tavily = TavilySearch()
        self.emotion_detector = ModulateEmotionDetector()

    async def generate_response(self, session: Session, student_input: str, audio_bytes: bytes = None) -> dict:
        t0 = time.time()
        query = f"{session.topic}: {student_input}" if session.topic else student_input
        search, emotion = await asyncio.gather(
            asyncio.to_thread(self.tavily.search_for_teaching, query),
            self._emotion(audio_bytes),
        )
        facts = self.tavily.format_facts_for_prompt(search)
        print(f"[timing] tavily+emotion {time.time()-t0:.1f}s", flush=True)

        state = f"Current phase: {session.phase}. Topic: {session.topic or 'not chosen yet'}."
        if session.plan:
            steps = "; ".join(f"{i}. {s}" for i, s in enumerate(session.plan))
            state += f" Plan: {steps}. Current step: {session.current_step}."
        turn = f"""Student said: "{student_input}"
Detected emotion: {emotion['emotion']} (confusion {emotion['confusion_score']:.1f} of 1). {self.emotion_detector.get_adaptation_instruction(emotion['confusion_score'])}
{state}
Web sources:
{facts}"""

        session.history.append({"role": "user", "content": turn})
        t0 = time.time()
        reply = await self._ask_llm(session.history)
        print(f"[timing] llm {time.time()-t0:.1f}s", flush=True)
        # Keep history compact: drop the bulky web sources from past turns.
        session.history[-1] = {"role": "user", "content": f'Student said: "{student_input}" (emotion: {emotion["emotion"]})'}
        session.history.append({"role": "assistant", "content": json.dumps(reply)})

        session.phase = reply.get("phase") or session.phase
        session.topic = reply.get("topic") or session.topic
        if reply.get("plan"):
            session.plan = reply["plan"]
        if reply.get("current_step") is not None:
            session.current_step = reply["current_step"]

        return {
            "response": reply.get("say", ""),
            "options": reply.get("options") or [],
            "phase": session.phase,
            "plan": session.plan,
            "current_step": session.current_step,
            "emotion": emotion["emotion"],
            "confusion_score": emotion["confusion_score"],
        }

    async def _emotion(self, audio_bytes):
        if not audio_bytes:
            return {"emotion": "calm", "confusion_score": 0.0}
        return await self.emotion_detector.detect_emotion(audio_bytes)

    async def _ask_llm(self, history) -> dict:
        text = ""
        try:
            response = await asyncio.to_thread(
                self.llm_client.chat.completions.create,
                model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, *history],
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.strip("`").removeprefix("json").strip()
            return json.loads(text)
        except json.JSONDecodeError:
            return {"say": text}
        except Exception as e:
            print(f"LLM error: {e}", flush=True)
            return {"say": "Sorry, I had trouble thinking just now. Could you say that again?"}
