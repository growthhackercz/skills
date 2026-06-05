# SmartEmailing API Notes

Verified on 2026-05-05 by read-only API probe and public PHP wrapper.

Base URL:

```text
https://app.smartemailing.cz/api/v3
```

Auth:

```text
Basic auth: username + API key
```

Read-only endpoints verified with test credentials:

```text
GET /ping
GET /contactlists
GET /contacts
GET /emails
GET /newsletters
GET /customfields
```

Create saved email:

```text
POST /emails
```

Payload from `pionl/smart-emailing-v3` `EmailCreateRequest`:

```json
{
  "title": "Email title",
  "name": "Email name",
  "htmlbody": "<html>...</html>",
  "textbody": "Plain text"
}
```

Newsletter endpoint from `NewsletterRequest`:

```text
POST /newsletter
```

Payload:

```json
{
  "email_id": 123,
  "contactlists": [456]
}
```

Treat `/newsletter` as send/campaign creation step, not an automatic draft step.

Sources:

- https://app.smartemailing.cz/docs/api/v3/index.html
- https://github.com/pionl/smart-emailing-v3
