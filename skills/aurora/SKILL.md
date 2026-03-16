---
name: aurora
description: Aurora - Voice-first PWA for business operations using Nuxt 3, Clerk, and Groq Whisper
metadata:
  version: "1.0.0"
  tags: ["pwa", "voice", "nuxt", "ai"]
---
# Aurora - Voice-First Business PWA

Aurora is a Progressive Web App (PWA) with voice-first interaction for business operations.

## Architecture
- **Frontend**: Nuxt 3 (Vue.js SSR)
- **Auth**: Clerk
- **Voice**: Groq Whisper for speech-to-text
- **Database**: PostgreSQL (db: aurora) on Data Plane (10.0.1.20)
- **Cache**: Redis DB 2
- **Storage**: MinIO bucket: aurora-assets
- **Deployment**: Coolify on App Plane A (10.0.1.30)

## Key Concepts
- **Voice Commands**: Users interact primarily through voice input
- **Transcription**: Groq Whisper converts speech to text in real-time
- **Business Actions**: Voice-triggered operations (create tasks, log notes, query data)
- **PWA**: Installable on mobile devices, works offline for basic features

## When to Use This Skill
- Researching voice-first UX patterns
- Analyzing Aurora user engagement metrics
- Planning new voice commands or business actions
- Researching Groq Whisper integration best practices
- Content strategy for Aurora (tutorials, onboarding)

## Tech Stack Details
- Nuxt 3 with server-side rendering
- Clerk for authentication and user management
- Groq API for fast Whisper transcription
- PostgreSQL + pgvector for semantic search on transcripts
