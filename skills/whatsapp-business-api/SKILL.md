---
name: whatsapp-business-api
description: Technical reference for Meta WhatsApp Business API — webhooks, message templates, media handling, rate limits, verification, and common troubleshooting.
metadata:
  version: "1.0.0"
  tags: [whatsapp, meta, api, webhooks, templates, business]
---

# WhatsApp Business API

Technical reference for supporting Whabi clients with WhatsApp Business API
integration. Load this skill when troubleshooting API issues or onboarding.

## Core Concepts

### Message Types
| Type | When | Cost |
|------|------|------|
| **Template messages** | Outside 24h window, marketing, notifications | Paid per message |
| **Session messages** | Within 24h of last customer message | Free (included in conversation) |
| **Interactive** | Buttons, lists, quick replies | Same as session/template |

### The 24-Hour Window
- Customer sends message → 24h window opens
- Within window: you can send any message type freely
- Outside window: ONLY pre-approved templates
- Window resets with each customer message

### Rate Limits
| Tier | Messages/day | How to reach |
|------|-------------|--------------|
| Tier 1 | 1,000 | New number, verified business |
| Tier 2 | 10,000 | Good quality rating for 7 days |
| Tier 3 | 100,000 | Good quality rating for 7 more days |
| Tier 4 | Unlimited | Good quality rating maintained |

**Quality rating drops if**: customers block you, report spam, or don't read messages.

## Common Troubleshooting

### "Template rejected by Meta"
- Check: no URL shorteners (bit.ly banned)
- Check: no ALL CAPS in template
- Check: variable placeholders match ({{1}}, {{2}})
- Check: template category matches content (marketing vs utility)

### "Webhook not receiving messages"
- Verify webhook URL is HTTPS (not HTTP)
- Verify verify_token matches what you set in Meta dashboard
- Check server responds with 200 to GET verification challenge
- Check server responds with 200 to POST within 20 seconds

### "Media upload failed"
- Max file sizes: image 5MB, video 16MB, document 100MB, audio 16MB
- Supported formats: JPEG/PNG (image), MP4 (video), PDF/DOC (document)
- Media URL must be publicly accessible OR use upload endpoint

### "Message not delivered"
- Check: recipient has WhatsApp installed
- Check: you're not in a rate limit cooldown
- Check: your quality rating hasn't dropped to "flagged"
- Check: the phone number format includes country code (+57...)

## Webhook Payload Structure

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "573001234567",
          "type": "text",
          "text": {"body": "Hola, necesito ayuda"},
          "timestamp": "1679000000"
        }]
      }
    }]
  }]
}
```

## Template Best Practices
- Keep under 1024 characters
- Use {{1}}, {{2}} for variables (not names)
- Category: "utility" for transactional, "marketing" for promotional
- Language: submit in the language you'll send (es for Spanish)
- Approval takes 24-48 hours
