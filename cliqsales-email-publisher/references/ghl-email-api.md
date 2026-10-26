# GHL Email Campaign API Notes

Verified from HighLevel docs/scopes and live smoke tests on 2026-05-06.

The primary target for this skill is a **draft Email Campaigns V2 campaign**,
not an Email Builder template.

Relevant scopes:

```text
emails/campaigns.readonly -> GET  /emails/public/v2/locations/:locationId/campaigns/emails
emails/campaigns.write    -> POST /emails/public/v2/locations/:locationId/campaigns/email-campaign
emails/campaigns.write    -> PATCH /emails/public/v2/locations/:locationId/campaigns/:campaignId
```

Required create fields observed in live tests:

```text
name
subject
html or editorContent
timeZone
userId
```

`userId` must be a HighLevel user id. The Control Center integration stores the
user e-mail in `GHL_USER`, so the helper resolves it through
`GET /users/?locationId=:locationId` (users scope required) unless the already
resolved `GHL_USER_ID` is set. Sending the e-mail as `userId` is accepted by the
API and then processes zero recipients, so never pass `GHL_USER` through.

Official docs:

- https://marketplace.gohighlevel.com/docs/Authorization/Scopes/

Email Builder template endpoints are retained only as a legacy fallback behind
the explicit `template-draft` helper command. Normal `draft`, `batch-draft`,
`readback`, and `update` commands must use Campaigns V2.

Payload schemas can vary by GHL API version. Keep primary campaign mapping
isolated in `build_campaign_payload()`.
