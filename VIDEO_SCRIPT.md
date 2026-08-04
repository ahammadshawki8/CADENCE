# Cadence - Video Script (3-4 minutes)

## [0:00-0:20] EMOTIONAL HOOK - The Voice That Changed Everything

**VISUALS:**
- Open with an elderly person speaking on a phone/video call
- Text overlay appears: "You sound tired..."
- Fade to black with gentle piano music

**SCRIPT:**

> "You sound tired."
>
> It's often the first sign of Parkinson's disease. A voice that once was warm and full of life now sounds flat, almost mechanical. By the time anyone realizes what's happening, the disease has been quietly changing their voice for years.
>
> For half the world without access to a neurologist, that early warning goes completely unheard. Until now.

---

## [0:20-0:35] THE PROBLEM - Why Most Voice AI Fails

**VISUALS:**
- Show "98% accuracy" claims from research papers
- Display: microphone icon with red X
- Show collapsed accuracy graph

**SCRIPT:**

> You've probably seen voice AI apps claiming ninety-five to ninety-nine percent accuracy for detecting Parkinson's disease. Here's what they don't tell you: they're not measuring the disease at all—they're measuring the microphone. When we tested the best published models across different recording devices, they collapsed to barely better than random chance. This is the dirty secret of medical voice AI.

---

## [0:35-0:50] THE SOLUTION - Introducing Cadence

**VISUALS:**
- Show Cadence logo
- Display app interface showing three tasks
- Show language selector (10 languages)

**SCRIPT:**

> Meet Cadence—a voice screening tool built on one simple principle: prove it's real before you ship it. We use three clinical tasks just like a speech therapist would: read a short passage, say "pa-ta-ka" as fast as you can, and hold a steady vowel. Thirty seconds of your voice, available in ten languages on any phone, with complete privacy because your audio is never stored. But here's what makes Cadence different: the science that proves it actually works.

---

## [0:50-1:30] THE RESEARCH - Built on Rigorous Science

**VISUALS:**
- Show multi-corpus validation diagram (3 datasets)
- Animate DANN architecture
- Display: "Real: 0.84 AUC → Shuffled: 0.38 AUC ✓ VERIFIED"

**SCRIPT:**

> We validated Cadence across three independently collected datasets in three languages: Italian, English, and Spanish. Unlike most projects that test on a single dataset, we trained on one corpus and tested on completely different recordings—different microphones, different countries, different protocols. This is what we call honest evaluation.
>
> Our interpretable acoustic features, eighty-eight measurements of voice quality, transfer at seventy-two percent accuracy—already better than the deep learning models that collapse to sixty percent. Then we applied domain-adversarial machine learning, a neural network architecture that learns to ignore the recording channel while preserving the disease signal. This pushed our accuracy to eighty percent, and with entropy regularization, we reached eighty-four percent.
>
> But here's the critical part: we ran a shuffled-source control experiment. We scrambled our training labels randomly and reran the entire pipeline. If our model was measuring the microphone instead of the disease, the accuracy would stay high. Ours dropped to thirty-eight percent—below random chance. That's how you prove a result is real, and it's a control the published field almost never runs.

---

## [1:30-2:00] THE DEMO - See It In Action

**VISUALS:**
- Screen recording: Welcome → Reading task → pa-ta-ka → Vowel → Results
- Show results screen with subsystem breakdown and SHAP chart
- Show PDF download

**SCRIPT:**

> Let me show you how it works. The app starts with a clear consent screen, then you choose your language—we support ten, including right-to-left scripts like Arabic. You read a short passage while the app captures your voice and extracts eighty-eight acoustic features using the industry-standard eGeMAPS parameter set. Then you complete the pa-ta-ka test for articulation speed and hold a steady vowel for voice quality measurements.
>
> In seconds, you receive a complete clinical report: a screening indicator, a breakdown by the four speech subsystems clinicians actually use, SHAP explanations showing which acoustic features contributed most, and a professional PDF you can share with your doctor. Every measurement is transparent, every prediction is explainable.

---

## [2:00-2:20] THE ENGINEERING - Professional Architecture

**VISUALS:**
- Show system architecture diagram
- Display: "✓ Live" "✓ Tested" "✓ Open Source"

**SCRIPT:**

> This isn't a prototype—it's production-grade software. We built a vanilla JavaScript Progressive Web App on the frontend that's installable and works offline, paired with a stateless FastAPI backend that runs torch-free inference. Quality gates automatically reject clipped or silent audio, and we use overlapping window analysis with median pooling so one noisy second can't trigger a false alarm. The entire system is split-deployed to Vercel and Render, fully containerized with Docker, automated end-to-end testing, and completely open source—all in under one megabyte of code.

---

## [2:20-2:40] WHY CADENCE DESERVES FIRST PRIZE

**VISUALS:**
- Split screen: Research papers / Architecture / Person using phone
- Text overlays: "Research-Backed" "Production-Grade" "Genuine Impact"

**SCRIPT:**

> So why does Cadence deserve first prize? Because most hackathon projects optimize one metric on one dataset and call it done. Cadence is a different class of work: research-backed at every single layer with papers cited for every modeling decision and shuffled-source controls the field doesn't run; engineered like a product people can actually use with ten languages, accessible design, and clinically transparent reports; and solving a real problem for millions of people who can't reach a specialist in time. Scientific rigor plus serious engineering plus genuine human impact—that's what a first-prize project looks like.

---

## [2:40-3:00] CLOSING HOOK - The Question

**VISUALS:**
- Return to opening scene - elderly person now smiling with phone showing results
- Text overlay: "What if we could hear it sooner?"
- Fade to Cadence logo with URL: github.com/ahammadshawki8/CADENCE

**SCRIPT:**

> Voice changes are often the first sign of Parkinson's disease, and the last one anyone thinks to investigate. What if we could hear it sooner? What if your phone could listen in a way your family can't?
>
> That's Cadence—live now, open source, and built to prove that medical AI can be rigorous, transparent, and accessible all at once. The code is on GitHub, the app is deployed, and the research is fully documented.
>
> What are you waiting for?

---

## PRODUCTION NOTES

### Timing Breakdown:
- Emotional Hook: 20 seconds
- Problem Statement: 15 seconds
- Solution Introduction: 15 seconds
- Research Deep Dive: 40 seconds
- Live Demo: 30 seconds
- Engineering Architecture: 20 seconds
- First Prize Argument: 20 seconds
- Closing Hook: 20 seconds
- **Total: 3:00**

### Visual Assets Needed:
1. **B-roll footage:**
   - Elderly person on video call (stock footage or staged)
   - Hands holding smartphone
   - Person speaking into phone
   - Family moments (warmth, connection)

2. **Screen recordings:**
   - Full app walkthrough (welcome → results)
   - PDF download and preview
   - Mobile responsive view
   - Language switching

3. **Animated diagrams:**
   - Multi-corpus validation flow
   - DANN architecture
   - System architecture
   - Shuffled-source control experiment

4. **Code snippets:**
   - FastAPI endpoint definition
   - eGeMAPS feature extraction
   - SHAP explainer initialization
   - (Keep these brief - 2-3 seconds each)

5. **Research paper visuals:**
   - Citations appearing as overlays
   - Paper thumbnails
   - Highlighted "98% accuracy" claims (for the problem section)

### Audio Requirements:
- Clear voiceover (warm, professional, not overly dramatic)
- Subtle background music:
  - Emotional/contemplative for opening (0:00-0:45)
  - Confident/technical for research (1:10-2:00)
  - Clean/minimal for demo (2:00-2:35)
  - Inspiring for closing (3:05-3:45)
- No music during demo section (2:00-2:35) or keep very minimal

### Pacing Notes:
- **First 10 seconds are critical** - the emotional hook must land
- **Research section (1:10-2:00)** - speak clearly but confidently; use visual diagrams to support technical terms
- **Demo section (2:00-2:35)** - let the screen recording breathe; don't rush
- **Closing (3:30-3:45)** - slow down slightly for emotional impact

### Text Overlays:
- Keep on screen for 2-3 seconds minimum
- Use consistent branding (Cadence purple: #6c5ce7)
- Citations should be readable but not distracting
- Key metrics (0.84 AUC, 0.38 shuffled) should be emphasized

### Tone:
- Warm and human, not clinical
- Confident about the science, not arrogant
- Passionate about the mission, not preachy
- Professional, but accessible

