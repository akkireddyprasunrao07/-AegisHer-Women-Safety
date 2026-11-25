# 🛡️ AegisHer — Women Safety Assistance Platform
**Empowering safety through instant SOS, live tracking, offline resilience, and verified support.**

---

## 📌 Problem Statement & Solution Overview

### The Gap
Delayed emergency response, fragmented safety applications, connectivity dead zones, and high-friction user interfaces under acute stress often turn critical situations into emergencies.

### Our Solution
**AegisHer** is a mobile-first **Unified Safety Ecosystem** that bridges the gap between a citizen in distress, their trusted circle, and verified emergency responders (`ERSS 112` / `Police 100`). It pairs a calm, low-friction mobile experience with a real-time web responder dashboard.

---

## ✨ Key Capabilities & Features

* **🚨 One-Tap SOS with Calm Cancel Shield:** Instant emergency trigger protected by a 3-second accidental-trigger buffer to prevent false alarms under stress.
* **🕵️ Discreet / Silent Auto-Escalate Mode:** Masks the mobile screen as a fully functional calculator while silently alerting primary and secondary trusted contacts in the background.
* **📡 Offline Dead-Zone Resilience:** Automatically caches encrypted GPS breadcrumbs locally when cellular/data connectivity drops, triggers SMS fallback alerts, and burst-syncs queued coordinates once signal returns.
* **⏱️ Proactive Safety Tools:**
  * **Timed Commute Check-In:** Countdown timer during late commutes that automatically escalates to a silent SOS if safety is not confirmed before expiry.
  * **Fake Call Deterrent:** Realistic incoming voice call simulator with a discreet in-call silent SOS trigger.
  * **Encrypted Ambient Audio Capture:** Automatically records and encrypts (`AES-256`) a 15-second ambient audio clip upon SOS activation.
* **🗺️ Real-Time Trusted Circle & Responder Dashboard:** Live GPS route tracking, geofence boundary alerts, expiring share tokens, and a tamper-proof 4-step escalation audit log (`Trigger → Capture Context → Broadcast Alert → 112/100 Escalation`).
* **📞 Geo-Indexed Verified Help Directory:** Quick-dial access to verified emergency helplines (`112`, `181`, `100`, `1091`, `108`), One Stop Centres (`Sakhi`), legal aid (`15100`), and local campus security.

---

## 🏗️ System Architecture & Tech Stack

| Layer | Planned Production Stack | Hackathon Prototype Implementation |
| :--- | :--- | :--- |
| **Mobile Client** | React Native, Expo | Interactive Mobile UI Simulator (HTML5/Tailwind & Python-served SPA) |
| **Responder Web Portal** | Next.js | Real-Time Responder & Audit Console |
| **Backend & API** | Node.js (Nest/Express) / FastAPI | Python Standard Library `ThreadingHTTPServer` REST & State Engine |
| **Realtime & Alerts** | Firebase (FCM), Socket.io, SMS Gateway | Live polling state sync + simulated multi-channel FCM/SMS/112 dispatch |
| **Maps & Geolocation** | Google Maps Platform / Mapbox | Custom SVG Geofence & Route Breadcrumb Visualizer |
| **Database & Security** | PostgreSQL + Redis, JWT, AES-256, Biometrics | Thread-safe in-memory state store, expiring links & cryptographic audit log |

---

## 📂 Repository Structure

```text
├── index.html                    # Standalone Dual-View Interactive Web Prototype (Mobile + Responder Dashboard)
├── hackkalp_safety_prototype.py  # Self-contained Python Server + Live Web Dashboard Prototype (Zero dependencies)
├── safety_prototype.py           # Python CLI + Live Web Responder Prototype
└── README.md                     # Project documentation and demo guide
```

---

## 🚀 Getting Started

### Option 1: Run the Python Full-Stack Prototype (Recommended)
No external dependencies or `pip install` required—runs purely on Python 3.10+ standard library.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/women-safety-assistance-platform.git
   cd women-safety-assistance-platform
   ```
2. **Start the prototype server:**
   ```bash
   python hackkalp_safety_prototype.py
   ```
3. **Open in browser:**  
   The app automatically launches at `http://127.0.0.1:8080`.

### Option 2: Run the Standalone HTML Prototype
Simply open `index.html` directly in any modern web browser (Chrome, Edge, Safari, Firefox) to interact with the dual-panel Mobile Simulator and Responder Dashboard.

---

## 🎤 3-Minute Live Demo Walkthrough

1. **Proactive Safety (`Safety Tools` tab):** Start the **10s Demo Timed Check-In** to show how an unconfirmed commute automatically escalates to a silent SOS, or launch the **Fake Call** deterrent.
2. **One-Tap SOS & Cancel Shield (`SOS` tab):** Tap the **SOS** button to demonstrate the 3-second accidental-trigger buffer, let it complete, and watch the 4-stage pipeline (`01 Trigger → 02 Context → 03 Broadcast → 04 112 Escalation`) light up on the Responder Dashboard.
3. **Offline Dead-Zone Sync (Top Controls):** Toggle **Dead Zone**, simulate GPS movement to queue amber offline breadcrumbs locally, then restore connectivity to watch automatic burst synchronization.
4. **Silent Escalation & Verified Directory:** Activate **Silent Mode** to disguise the phone screen as a calculator while live tracking continues, then explore the **Verified Help** directory (`112`, `181`, `100`, `1091`, `108`).

---

## 🗺️ Phased Roadmap

* **Phase 01 — Hackathon Sprint (Current):** One-tap & silent SOS triggers, 3s cancel shield, live GPS breadcrumb stream, offline caching simulation, timed check-in, fake call, and verified helpline directory.
* **Phase 02 — MVP Launch (4–6 Weeks):** Native iOS/Android builds via Expo, live SMS gateway integration, geo-indexed nearby shelter/police search, and biometric incident lock.
* **Phase 03 — Scale & Ecosystem:** Partnerships with NGOs & local authorities, smartwatch SOS triggers, and multi-language regional support.

---

## 📄 Disclaimer & Standards Alignment
* Designed with reference to India **ERSS 112**, **Police 100**, and **Medical 108** escalation workflows, alongside **GDPR/CCPA** data minimization and **AES-256** encryption principles.
* Emergency dispatch and SMS/FCM notifications in this repository are simulated for safe hackathon demonstration purposes.
