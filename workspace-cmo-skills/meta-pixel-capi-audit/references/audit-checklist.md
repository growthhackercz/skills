# Meta Pixel CAPI Audit Checklist

Evidence JSON pro helper má být sanitized:

```json
{
  "pixelId": "123456789",
  "platform": "nextjs",
  "events": [
    {
      "eventName": "Lead",
      "browserPixel": true,
      "serverCapi": true,
      "eventIdDedup": true,
      "matchingFields": ["em", "ph", "fbp", "fbc", "client_ip_address", "client_user_agent"],
      "testEventSeen": true
    }
  ]
}
```

Nikdy nevkládej raw email, telefon, jméno, IP adresu nebo tokeny. `matchingFields`
jsou jen názvy polí, ne hodnoty.

## Core Checks

- browser pixel installed
- CAPI/server event configured for core conversion events
- browser and server share the same `event_id`
- advanced matching includes `em` and ideally `ph`
- `_fbp` and `_fbc` are captured when available
- IP address and user agent are passed server-side
- Events Manager Test Events or Diagnostics evidence exists

## EMQ Targets

- Purchase: `9.3+` excellent, `8.0-9.2` good, below `8.0` needs work.
- Lead: `8.0+` excellent, `6.5-7.9` good, below `6.5` needs work.

All scores from this helper are estimates. Verify actual score in Meta Events
Manager.
