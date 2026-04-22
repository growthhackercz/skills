---
category: Support & Ops
---

# Skill: Response Templates

Maintain a library of proven response templates. Personalize per customer. Track what works. Iterate.

## Template Storage

Store templates in `memory/response-templates.json`:

```json
{
  "templates": [
    {
      "id": "password-reset",
      "category": "account",
      "trigger": "Customer can't log in or needs password reset",
      "template": "Hi {name},\n\nHere's how to reset your password:\n\n1. Go to {product_url}/reset\n2. Enter your email address\n3. Check your inbox (and spam folder) for the reset link\n4. Click the link and set a new password\n\nIf the email doesn't show up within a few minutes, let me know and I'll look into it from our end.\n\n{signoff}",
      "variables": ["name", "product_url", "signoff"],
      "useCount": 0,
      "resolvedCount": 0,
      "avgSatisfaction": null,
      "lastUsed": null,
      "notes": ""
    }
  ]
}
```

## Core Template Library

Start with these. Customize for your product:

### Account Issues
- **password-reset** - Password reset instructions
- **account-locked** - Account locked/suspended explanation
- **login-trouble** - General login troubleshooting steps
- **account-deletion** - Account deletion request handling

### Billing
- **refund-approved** - Refund confirmation
- **refund-denied** - Refund denial with reasoning
- **billing-question** - Charge explanation
- **plan-change** - How to upgrade/downgrade
- **cancellation-save** - Retention response when customer wants to cancel

### Bugs
- **bug-acknowledged** - We see the bug, we're on it
- **bug-workaround** - Bug exists, here's how to work around it
- **bug-fixed** - The fix is deployed, please try again
- **cant-reproduce** - Need more details to reproduce

### How-To
- **getting-started** - Onboarding basics
- **feature-guide** - How to use a specific feature
- **integration-setup** - Third-party integration steps

### General
- **feature-request-ack** - Thanks for the suggestion, logged it
- **positive-feedback-thanks** - Thanks for the kind words
- **follow-up-check** - Checking in after resolution
- **escalation-notice** - Letting customer know we've escalated

## Using Templates

### 1. Match

When a ticket comes in, identify the closest template match. Consider:
- What category is the issue?
- What is the customer actually asking?
- Is there an exact match, or do we need to adapt?

### 2. Personalize

Never send a template raw. Always:
- Use the customer's name
- Reference their specific situation ("I see you're trying to connect your Stripe account...")
- Match their tone (technical customer gets technical details)
- Add context from their account or history
- Remove steps that don't apply to their situation

### 3. Send and Log

After sending, update the template record:
```json
{
  "useCount": 15,
  "resolvedCount": 12,
  "avgSatisfaction": 4.2,
  "lastUsed": "2025-01-15"
}
```

## Template Effectiveness

Track which templates actually resolve issues:

**Resolution rate** = resolvedCount / useCount
- Above 80%: template is working well
- 50-80%: review and improve
- Below 50%: rewrite or split into more specific templates

**Satisfaction correlation**: If a template has low CSAT scores, the response might be technically correct but tone-deaf. Review the language.

## A/B Testing

When you want to improve a template:

1. Create a variant (e.g., "password-reset-v2")
2. Use the original and variant alternately
3. Track resolution rate and satisfaction for each
4. After 20+ uses of each, compare results
5. Keep the winner, archive the loser

Store test results in `memory/template-tests.json`:
```json
{
  "tests": [
    {
      "original": "bug-acknowledged",
      "variant": "bug-acknowledged-v2",
      "change": "Added estimated fix timeline and workaround upfront",
      "originalStats": { "uses": 25, "resolved": 18, "avgSat": 3.8 },
      "variantStats": { "uses": 22, "resolved": 20, "avgSat": 4.4 },
      "winner": "variant",
      "decidedDate": "2025-01-20"
    }
  ]
}
```

## Creating New Templates

When you find yourself writing similar responses 3+ times:

1. Draft a template from the best version you wrote
2. Identify the variables (customer name, product area, specific details)
3. Add it to the library
4. Start tracking usage

**Good template qualities:**
- Solves the problem in one response when possible
- Starts with acknowledgment, not instructions
- Steps are numbered and specific
- Ends with a clear next step
- Sounds like a person wrote it, not a system generated it

## Rules

- Templates are starting points, not autopilot. Always read the ticket and personalize.
- If a customer has contacted before, reference the history. "I see you ran into this last week too" shows you're paying attention.
- Don't use templates for angry customers. Write those responses fresh, with care.
- Review the template library monthly. Kill templates nobody uses. Update ones that reference old features.
- When a template needs product-specific details, leave clear variable markers so you don't accidentally send `{product_url}` to a customer.