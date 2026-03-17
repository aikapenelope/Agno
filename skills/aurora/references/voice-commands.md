# Aurora Voice Commands Reference

## Task Management
| Voice Command | Action |
|---|---|
| "Create task [description]" | Creates task in PostgreSQL |
| "List my tasks" | Shows pending tasks |
| "Complete task [name]" | Marks task as done |
| "Remind me to [action] at [time]" | Creates scheduled reminder |

## Notes
| Voice Command | Action |
|---|---|
| "Take a note: [content]" | Creates note with timestamp |
| "Search notes about [topic]" | Semantic search via pgvector |
| "Read my last note" | Retrieves most recent note |

## Business Operations
| Voice Command | Action |
|---|---|
| "How many clients this week?" | Queries PostgreSQL stats |
| "Schedule meeting with [name]" | Creates calendar entry |
| "Send follow-up to [name]" | Triggers n8n workflow |

## Groq Whisper Settings
- Model: whisper-large-v3-turbo
- Language: auto-detect (Spanish/English)
- Response format: json (with timestamps)
- Temperature: 0 (deterministic transcription)
