// Voice Teaching Agent — hands-free conversation loop:
// listen -> (silence) -> send turn -> tutor speaks -> listen again

const SILENCE_MS = 1500;

class VoiceTeachingAgent {
    constructor() {
        this.ws = null;
        this.active = false;
        this.state = 'idle'; // idle | listening | thinking | speaking
        this.stream = null;
        this.analyser = null;
        this.recognition = null;
        this.recorder = null;
        this.currentAudio = null;
        this.pendingAudio = null;

        this.el = {
            talkBtn: document.getElementById('talk-btn'),
            voiceState: document.getElementById('voice-state'),
            composer: document.getElementById('composer'),
            studentInput: document.getElementById('student-input'),
            messages: document.getElementById('messages'),
            connectionStatus: document.getElementById('connection-status'),
            emotionText: document.getElementById('emotion-text'),
            options: document.getElementById('options'),
            planPanel: document.getElementById('plan-panel'),
            planList: document.getElementById('plan-list'),
        };

        this.el.talkBtn.addEventListener('click', () => (this.active ? this.stopConversation() : this.startConversation()));
        this.el.composer.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendTyped();
        });
        this.connectWebSocket();
    }

    // ---------- conversation control ----------

    async startConversation() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) {
            this.addSystemMessage('Speech recognition needs Chrome. You can still type below.');
            return;
        }
        try {
            this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        } catch (err) {
            this.addSystemMessage('Microphone access was blocked. Allow it in the address bar and try again.');
            return;
        }
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = ctx.createAnalyser();
        ctx.createMediaStreamSource(this.stream).connect(this.analyser);
        this.drawLevel();

        this.active = true;
        this.el.talkBtn.setAttribute('aria-label', 'End conversation');

        if (this.pendingAudio) {
            const audio = this.pendingAudio;
            this.pendingAudio = null;
            this.speak(audio);
        } else if (this.state !== 'thinking') {
            this.listen();
        }
    }

    stopConversation() {
        this.active = false;
        this.abortListening();
        if (this.currentAudio) this.currentAudio.pause();
        if (this.stream) this.stream.getTracks().forEach((t) => t.stop());
        this.stream = null;
        this.el.talkBtn.setAttribute('aria-label', 'Start conversation');
        this.setState('idle');
    }

    setState(state) {
        this.state = state;
        const labels = { idle: 'Tap to start', listening: 'Listening', thinking: 'Thinking', speaking: 'Speaking — tap an answer to interrupt' };
        this.el.voiceState.textContent = labels[state];
        this.el.talkBtn.className = `orb ${state}${this.active ? ' on' : ''}`;
    }

    // ---------- listening & turn detection ----------

    listen() {
        if (!this.active) return;
        this.setState('listening');
        this.committed = '';
        this.interim = '';
        this.chunks = [];

        this.recorder = new MediaRecorder(this.stream);
        this.recorder.ondataavailable = (e) => this.chunks.push(e.data);
        this.recorder.start();

        this.startRecognition();
    }

    startRecognition() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const rec = new SR();
        rec.lang = 'en-US';
        rec.continuous = true;
        rec.interimResults = true;
        rec.onresult = (e) => {
            this.interim = Array.from(e.results).map((r) => r[0].transcript).join(' ');
            this.el.voiceState.textContent = (this.committed + ' ' + this.interim).trim();
            clearTimeout(this.silenceTimer);
            this.silenceTimer = setTimeout(() => this.endTurn(), SILENCE_MS);
        };
        // Chrome ends recognition on its own after a pause; keep listening until the turn ends.
        rec.onend = () => {
            if (this.recognition !== rec) return;
            this.committed = (this.committed + ' ' + this.interim).trim();
            this.interim = '';
            if (this.active && this.state === 'listening') this.startRecognition();
        };
        rec.onerror = (e) => {
            if (e.error === 'not-allowed') {
                this.addSystemMessage('Speech recognition was blocked.');
                this.stopConversation();
            }
        };
        this.recognition = rec;
        rec.start();
    }

    endTurn() {
        const text = (this.committed + ' ' + this.interim).trim();
        if (!text || this.state !== 'listening') return;
        this.setState('thinking');
        this.stopRecognition();

        const recorder = this.recorder;
        recorder.onstop = async () => {
            const blob = new Blob(this.chunks, { type: recorder.mimeType });
            const audio = await this.blobToBase64(blob);
            this.addMessage('You', text, 'student');
            this.renderOptions([]);
            this.ws.send(JSON.stringify({ type: 'voice_turn', text, audio }));
        };
        recorder.stop();
    }

    stopRecognition() {
        clearTimeout(this.silenceTimer);
        const rec = this.recognition;
        this.recognition = null;
        if (rec) rec.abort();
    }

    abortListening() {
        this.stopRecognition();
        if (this.recorder && this.recorder.state !== 'inactive') {
            this.recorder.onstop = null;
            this.recorder.stop();
        }
    }

    // ---------- typed / clicked answers ----------

    sendTyped() {
        const text = this.el.studentInput.value.trim();
        this.el.studentInput.value = '';
        this.sendAnswer(text);
    }

    sendAnswer(text) {
        if (!text || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        if (this.currentAudio) this.currentAudio.pause();
        this.abortListening();
        if (this.active) this.setState('thinking');
        this.addMessage('You', text, 'student');
        this.renderOptions([]);
        this.ws.send(JSON.stringify({ type: 'text_input', text }));
    }

    // ---------- server messages ----------

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/teach`);
        this.ws.onopen = () => this.updateConnectionStatus(true);
        this.ws.onmessage = (event) => this.handleMessage(JSON.parse(event.data));
        this.ws.onclose = () => {
            this.updateConnectionStatus(false);
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    handleMessage(msg) {
        if (msg.type === 'error') {
            this.addSystemMessage(`Error: ${msg.message}`);
            if (this.active) this.listen();
            return;
        }
        if (msg.type !== 'response') return;

        this.addMessage('Tutor', msg.text, 'agent');
        this.updateEmotion(msg.emotion, msg.confusion_score);
        this.setPhase(msg.phase);
        this.renderPlan(msg.plan || [], msg.current_step);
        this.renderOptions(msg.options || []);

        const audio = msg.audio ? new Audio(`data:audio/mpeg;base64,${msg.audio}`) : null;
        if (!audio) {
            if (this.active) this.listen();
        } else if (!this.active) {
            // Browsers block autoplay before a click; play it when the conversation starts.
            this.pendingAudio = audio;
        } else {
            this.speak(audio);
        }
    }

    speak(audio) {
        if (this.currentAudio) this.currentAudio.pause();
        this.currentAudio = audio;
        this.setState('speaking');
        const next = () => {
            if (this.currentAudio === audio && this.active) this.listen();
        };
        audio.onended = next;
        audio.play().catch(next);
    }

    // ---------- rendering ----------

    setPhase(phase) {
        document.querySelectorAll('.phase').forEach((el) => el.classList.toggle('active', el.dataset.phase === phase));
    }

    renderPlan(steps, current) {
        this.el.planPanel.hidden = steps.length === 0;
        this.el.planList.innerHTML = '';
        steps.forEach((step, i) => {
            const li = document.createElement('li');
            li.textContent = step;
            if (current !== null && current !== undefined) {
                if (i < current) li.className = 'done';
                if (i === current) li.className = 'current';
            }
            this.el.planList.appendChild(li);
        });
    }

    renderOptions(options) {
        this.el.options.innerHTML = '';
        options.forEach((opt, i) => {
            const letter = String.fromCharCode(65 + i);
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.innerHTML = `<b>${letter}</b>${this.escapeHtml(opt)}`;
            btn.addEventListener('click', () => this.sendAnswer(`${letter}) ${opt}`));
            this.el.options.appendChild(btn);
        });
    }

    addMessage(role, text, type) {
        const div = document.createElement('div');
        div.className = `line ${type}`;
        div.innerHTML = `<span class="who">${role}</span><p>${this.escapeHtml(text)}</p>`;
        this.el.messages.appendChild(div);
        div.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    addSystemMessage(text) {
        this.addMessage('', text, 'system');
    }

    updateEmotion(emotion, score) {
        this.el.emotionText.textContent =
            score > 0.5 ? `Sounds ${emotion} — slowing down` : '';
    }

    updateConnectionStatus(connected) {
        this.el.connectionStatus.className = `conn ${connected ? 'online' : ''}`;
        this.el.connectionStatus.title = connected ? 'Connected' : 'Disconnected';
    }

    drawLevel() {
        const data = new Uint8Array(this.analyser.fftSize);
        const tick = () => {
            if (!this.stream) {
                this.el.talkBtn.style.setProperty('--level', 0);
                return;
            }
            this.analyser.getByteTimeDomainData(data);
            let peak = 0;
            for (const v of data) peak = Math.max(peak, Math.abs(v - 128));
            const level = this.state === 'listening' ? Math.min(1, peak / 40) : 0;
            this.el.talkBtn.style.setProperty('--level', level.toFixed(2));
            requestAnimationFrame(tick);
        };
        tick();
    }

    blobToBase64(blob) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result.split(',')[1]);
            reader.readAsDataURL(blob);
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

document.addEventListener('DOMContentLoaded', () => new VoiceTeachingAgent());
