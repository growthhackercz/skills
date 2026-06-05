#!/usr/bin/env python3
"""CliqSales / GoHighLevel Social Planner publisher helper.

Draft-first utility for creating single or batch social posts.
Credentials are read from env or env file.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore[assignment]


DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/cliqsales.env",
    "/home/node/.openclaw/secrets/ghl.env",
    "/home/node/.openclaw/.env",
)
DEFAULT_API_BASE_URL = "https://services.leadconnectorhq.com"
DEFAULT_API_VERSION = "2021-07-28"
DEFAULT_TIMEZONE = "Europe/Prague"
ALLOWED_STATUSES = {"draft", "scheduled", "published"}
POST_NAMED_CONTAINER_KEYS = ("post", "socialPost", "socialMediaPost")
POST_GENERIC_CONTAINER_KEYS = ("data", "result", "results", "item", "record")
POST_ID_KEYS = ("postId", "socialPostId", "socialMediaPostId", "_id", "id")
POST_SHAPE_KEYS = {"summary", "caption", "content", "status", "accountIds", "scheduleDate", "type"}
NON_POST_CONTAINER_KEYS = {"accounts", "account", "users", "user", "media", "medias", "files", "file"}
PLATFORM_ALIASES = {
    "fb": "facebook",
    "facebook-page": "facebook",
    "ig": "instagram",
    "insta": "instagram",
    "li": "linkedin",
    "linked-in": "linkedin",
}


class SocialError(RuntimeError):
    def __init__(self, message: str, status: int | None = None, detail: Any | None = None):
        super().__init__(message)
        self.status = status
        self.detail = detail


def parse_env_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip()
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
        return None
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        value = value[1:-1]
    return key, value


def load_env_file(path: str | None) -> None:
    candidates = [path] if path else list(DEFAULT_ENV_FILES)
    for candidate in candidates:
        if not candidate:
            continue
        env_path = Path(candidate)
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            parsed = parse_env_line(line)
            if not parsed:
                continue
            key, value = parsed
            os.environ[key] = value
        return


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SocialError(f"Missing required environment variable: {name}")
    return value


def sanitize_location_id(raw: str) -> str:
    value = raw.strip()
    if value.startswith("loc_"):
        value = value[4:]
    if "http" in value or "/location/" in value:
        match = re.search(r"/location/([A-Za-z0-9]+)/?", value)
        if match:
            value = match.group(1)
    if value.startswith("loc_"):
        value = value[4:]
    return value.strip()


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def string_value(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, int):
        return str(value)
    return None


def string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "ano"}
    return False


def find_in_tree(value: Any, keys: set[str]) -> Any | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys and item not in (None, ""):
                return item
        for item in value.values():
            found = find_in_tree(item, keys)
            if found not in (None, ""):
                return found
    if isinstance(value, list):
        for item in value:
            found = find_in_tree(item, keys)
            if found not in (None, ""):
                return found
    return None


def normalize_items(payload: Any, possible_keys: tuple[str, ...]) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in possible_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = normalize_items(value, possible_keys)
                if nested:
                    return nested
        for value in payload.values():
            if isinstance(value, dict):
                nested = normalize_items(value, possible_keys)
                if nested:
                    return nested
    return []


def normalize_lookup_key(value: Any) -> str | None:
    raw = string_value(value)
    if not raw:
        return None
    key = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return PLATFORM_ALIASES.get(key, key) if key else None


def parse_schedule(value: str | None, timezone: str | None) -> str | None:
    if not value:
        return None

    raw = value.strip()
    if not raw:
        return None
    if raw.lower() in {"tbd", "todo", "n/a", "na", "none", "null", "-", "neuvedeno", "nezadano", "nezadáno"}:
        return None

    # Already ISO with timezone/Z
    if raw.endswith("Z") or re.search(r"[+-]\d\d:\d\d$", raw):
        return raw

    formats = ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")
    parsed = None
    for fmt in formats:
        try:
            parsed = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    if parsed is None:
        raise SocialError(f"Invalid schedule date format: {value}")

    tz_name = timezone or DEFAULT_TIMEZONE
    if ZoneInfo is None:
        raise SocialError("Timezone support is unavailable in this Python runtime")
    tz = ZoneInfo(tz_name)
    aware = parsed.replace(tzinfo=tz)
    return aware.isoformat()


def build_multipart_body(file_field: str, file_path: str) -> tuple[bytes, str]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise SocialError(f"Media file not found: {file_path}")
    if path.stat().st_size <= 0:
        raise SocialError(f"Media file is empty: {file_path}")

    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"

    body = b"".join(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )
    return body, boundary


def direct_post_id_from_object(value: dict[str, Any]) -> str | None:
    for key in POST_ID_KEYS[:3]:
        post_id = string_value(value.get(key))
        if post_id:
            return post_id

    if any(key in value for key in NON_POST_CONTAINER_KEYS):
        return None

    if value.keys() & POST_SHAPE_KEYS or len(value) <= 3:
        for key in POST_ID_KEYS[3:]:
            post_id = string_value(value.get(key))
            if post_id:
                return post_id

    return None


def post_id_from_known_shape(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in POST_NAMED_CONTAINER_KEYS:
            nested = payload.get(key)
            if nested is payload:
                continue
            found = post_id_from_known_shape(nested)
            if found:
                return found

        direct = direct_post_id_from_object(payload)
        if direct:
            return direct

        for key in POST_GENERIC_CONTAINER_KEYS:
            nested = payload.get(key)
            if nested is payload:
                continue
            found = post_id_from_known_shape(nested)
            if found:
                return found

        for key in ("posts", "items"):
            nested = payload.get(key)
            if isinstance(nested, list) and len(nested) == 1:
                found = post_id_from_known_shape(nested[0])
                if found:
                    return found

    if isinstance(payload, list) and len(payload) == 1:
        return post_id_from_known_shape(payload[0])

    return None


def post_id_from_response(payload: Any) -> str | None:
    return post_id_from_known_shape(payload)


def media_url_from_response(payload: Any) -> str | None:
    value = find_in_tree(payload, {"url", "fileUrl", "publicUrl", "sourceUrl", "cdnUrl", "signedUrl"})
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def media_items_from_urls(urls: list[str]) -> list[dict[str, str]]:
    return [{"url": url, "type": "image"} for url in urls if url.strip()]


def assert_success_response(payload: Any, action: str) -> None:
    if not isinstance(payload, dict):
        return

    status_code = payload.get("statusCode") or payload.get("status")
    if isinstance(status_code, int) and status_code >= 400:
        raise SocialError(f"{action} failed with status {status_code}", status_code, payload)

    success = payload.get("success")
    ok = payload.get("ok")
    if success is False or ok is False:
        raise SocialError(f"{action} failed", None, payload)


def upload_media_files(client: "SocialClient", media_files: list[str]) -> list[dict[str, str]]:
    uploads: list[dict[str, str]] = []
    for media_file in media_files:
        uploaded = client.upload_media(media_file)
        assert_success_response(uploaded, f"Media upload for {media_file}")
        url = media_url_from_response(uploaded)
        if not url:
            raise SocialError(f"Uploaded media has no public URL in response for file: {media_file}", detail=uploaded)
        uploads.append({"file": media_file, "url": url})
    return uploads


class SocialClient:
    def __init__(self) -> None:
        self.token = require_env("GHL_API_KEY")
        self.location_id = sanitize_location_id(require_env("GHL_LOCATION_ID"))
        if not self.location_id:
            raise SocialError("GHL_LOCATION_ID is empty after sanitization")

        self.api_base_url = os.environ.get("GHL_API_BASE_URL", DEFAULT_API_BASE_URL).strip() or DEFAULT_API_BASE_URL
        self.api_base_url = self.api_base_url.rstrip("/")
        self.api_version = os.environ.get("GHL_API_VERSION", DEFAULT_API_VERSION).strip() or DEFAULT_API_VERSION

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ControlCenterCliqSalesSocialPublisher/1.0",
        }

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raw_body: bytes | None = None,
    ) -> Any:
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        if params:
            clean = {k: str(v) for k, v in params.items() if v is not None and v != ""}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)

        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)

        body = raw_body if raw_body is not None else (json_dumps(data) if data is not None else None)

        req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read().decode("utf-8", errors="replace")
                if not raw:
                    return {}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"raw": raw}
        except urllib.error.HTTPError as error:
            detail_text = error.read().decode("utf-8", errors="replace")
            try:
                detail_obj = json.loads(detail_text) if detail_text else {}
            except json.JSONDecodeError:
                detail_obj = detail_text
            safe_detail = detail_text[:800] if detail_text else str(detail_obj)
            if error.code == 401:
                raise SocialError(f"Authentication failed (401). {safe_detail}", error.code, detail_obj)
            if error.code == 403:
                raise SocialError(f"Permission denied (403). {safe_detail}", error.code, detail_obj)
            raise SocialError(f"GHL API returned HTTP {error.code}: {safe_detail}", error.code, detail_obj)
        except urllib.error.URLError as error:
            raise SocialError(f"GHL request failed: {error.reason}")

    def accounts(self) -> Any:
        return self.request("GET", f"/social-media-posting/{self.location_id}/accounts")

    def categories(self) -> Any:
        return self.request("GET", f"/social-media-posting/{self.location_id}/categories")

    def tags(self) -> Any:
        return self.request("GET", f"/social-media-posting/{self.location_id}/tags")

    def users(self) -> Any:
        return self.request("GET", "/users/", params={"locationId": self.location_id})

    def posts_list(self, limit: str = "10", skip: str = "0") -> Any:
        return self.request(
            "POST",
            f"/social-media-posting/{self.location_id}/posts/list",
            data={"limit": str(limit), "skip": str(skip)},
        )

    def create_post(self, payload: dict[str, Any]) -> Any:
        return self.request("POST", f"/social-media-posting/{self.location_id}/posts", data=payload)

    def update_post(self, post_id: str, payload: dict[str, Any]) -> Any:
        return self.request("PUT", f"/social-media-posting/{self.location_id}/posts/{post_id}", data=payload)

    def upload_media(self, file_path: str) -> Any:
        body, boundary = build_multipart_body("file", file_path)
        headers = {
            "Authorization": self.headers["Authorization"],
            "Version": self.headers["Version"],
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": self.headers["User-Agent"],
        }
        return self.request("POST", "/medias/upload-file", params={"locationId": self.location_id}, headers=headers, raw_body=body)


def infer_user_id(users_payload: Any) -> str | None:
    users = normalize_items(users_payload, ("users", "data", "items"))
    if len(users) == 1:
        return user_id_from_object(users[0])
    return None


def user_id_from_object(user: dict[str, Any]) -> str | None:
    for key in ("userId", "_id", "id"):
        value = string_value(user.get(key))
        if value:
            return value
    return None


def user_email_from_object(user: dict[str, Any]) -> str | None:
    return first_string(user.get("email"), user.get("emailAddress"), user.get("primaryEmail"))


def infer_user_id_by_email(users_payload: Any, email: str) -> str | None:
    users = normalize_items(users_payload, ("users", "data", "items"))
    wanted = email.strip().lower()
    matches = [
        user
        for user in users
        if (user_email_from_object(user) or "").strip().lower() == wanted
    ]
    if len(matches) != 1:
        return None
    return user_id_from_object(matches[0])


def is_email_reference(value: str | None) -> bool:
    return bool(value and "@" in value)


def user_reference_kind(value: str | None) -> str:
    if not value:
        return "missing"
    return "email" if is_email_reference(value) else "id"


def resolve_user_reference(client: SocialClient, reference: str | None, source: str) -> str:
    value = first_string(reference)
    if not value:
        raise SocialError(
            "GHL Social Planner requires a user. Set GHL_USER to a user ID or email, pass --user, or set item user."
        )

    if not is_email_reference(value):
        return value

    try:
        users_payload = client.users()
    except SocialError as error:
        raise SocialError(
            f"{source} is an email, but /users/ lookup failed. Use a GHL user ID instead or create a token with users scope.",
            error.status,
            error.detail,
        ) from error

    inferred = infer_user_id_by_email(users_payload, value)
    if inferred:
        return inferred

    raise SocialError(f"Unable to resolve {source} email to exactly one GHL user: {value}")


def default_user_reference(explicit: str | None) -> str | None:
    return first_string(
        explicit,
        os.environ.get("GHL_USER"),
    )


def item_user_reference(item: dict[str, Any]) -> str | None:
    return first_string(item.get("user"), item.get("userRef"), item.get("userId"), item.get("user_id"))


def account_id_from_object(account: dict[str, Any]) -> str | None:
    for key in ("accountId", "_id", "id"):
        value = string_value(account.get(key))
        if value:
            return value
    return None


def account_lookup_keys(account: dict[str, Any]) -> list[str]:
    raw_keys = [
        account.get("platform"),
        account.get("provider"),
        account.get("channel"),
        account.get("platformType"),
        account.get("type"),
        account.get("name"),
        account.get("label"),
        account.get("displayName"),
        account.get("accountName"),
        account.get("pageName"),
        account.get("profileName"),
        account.get("username"),
    ]

    keys: list[str] = []
    for raw in raw_keys:
        key = normalize_lookup_key(raw)
        if key and key not in keys:
            keys.append(key)
    return keys


def build_auto_account_map(accounts_payload: Any) -> tuple[dict[str, str], dict[str, list[str]]]:
    accounts = normalize_items(accounts_payload, ("accounts", "data", "items"))
    grouped: dict[str, list[str]] = {}
    for account in accounts:
        if account.get("deleted") or account.get("isExpired"):
            continue
        account_id = account_id_from_object(account)
        if not account_id:
            continue
        for key in account_lookup_keys(account):
            grouped.setdefault(key, [])
            if account_id not in grouped[key]:
                grouped[key].append(account_id)

    resolved = {key: ids[0] for key, ids in grouped.items() if len(ids) == 1}
    ambiguous = {key: ids for key, ids in grouped.items() if len(ids) > 1}
    return resolved, ambiguous


def item_account_lookup_keys(item: dict[str, Any]) -> list[str]:
    keys: list[str] = []
    for raw in (item.get("accountKey"), item.get("accountLabel"), item.get("platform"), item.get("channel")):
        key = normalize_lookup_key(raw)
        if key and key not in keys:
            keys.append(key)
    return keys


def item_needs_account_mapping(
    item: dict[str, Any],
    default_accounts: list[str],
    account_map: dict[str, str],
) -> bool:
    if string_list(item.get("accountIds")) or first_string(item.get("accountId")) or default_accounts:
        return False
    keys = item_account_lookup_keys(item)
    return bool(keys) and not any(key in account_map for key in keys)


def resolve_account_ids(item: dict[str, Any], default_accounts: list[str], account_map: dict[str, str]) -> list[str]:
    explicit = string_list(item.get("accountIds"))
    if explicit:
        return explicit

    single = first_string(item.get("accountId"))
    if single:
        return [single]

    for key in item_account_lookup_keys(item):
        mapped = account_map.get(key)
        if mapped:
            return [mapped]

    return list(default_accounts)


def parse_account_map(value: str | None) -> dict[str, str]:
    if not value:
        return {}
    output: dict[str, str] = {}
    for chunk in value.split(","):
        part = chunk.strip()
        if not part:
            continue
        if ":" not in part:
            raise SocialError(f"Invalid account map item: {part}. Expected platform:accountId")
        key, account_id = part.split(":", 1)
        key = normalize_lookup_key(key)
        account_id = account_id.strip()
        if key and account_id:
            output[key] = account_id
    return output


def create_payload_from_item(
    item: dict[str, Any],
    default_type: str,
    default_timezone: str,
    default_user_id: str | None,
    default_accounts: list[str],
    account_map: dict[str, str],
) -> dict[str, Any]:
    summary = first_string(item.get("summary"), item.get("caption"), item.get("text"))
    if not summary:
        raise SocialError("Missing summary/caption/text in batch item")

    account_ids = resolve_account_ids(item, default_accounts, account_map)
    if not account_ids:
        raise SocialError("Missing accountIds (no item account, no platform map, and no default account IDs)")

    schedule_local = first_string(item.get("scheduleLocal"), item.get("scheduleDateLocal"))
    schedule_date = first_string(item.get("scheduleDate"))
    timezone = first_string(item.get("timezone"), default_timezone) or DEFAULT_TIMEZONE

    if not schedule_date:
        schedule_date = parse_schedule(schedule_local, timezone)

    raw_status = first_string(item.get("status"), "draft") or "draft"
    status = raw_status.strip().lower()
    if status not in ALLOWED_STATUSES:
        raise SocialError(f"Invalid post status in batch item: {status}")

    payload: dict[str, Any] = {
        "accountIds": account_ids,
        "summary": summary,
        "type": first_string(item.get("type"), default_type) or "post",
        "status": status,
    }
    user_id = first_string(item.get("userId"), item.get("user_id"), default_user_id)
    if not user_id:
        raise SocialError("GHL Social Planner requires a user. Add item user, pass --user, or set GHL_USER.")
    payload["userId"] = user_id

    if status == "scheduled" and not schedule_date:
        raise SocialError("Scheduled post requires scheduleDate or scheduleLocal")
    if schedule_date:
        payload["scheduleDate"] = schedule_date

    media_urls = string_list(item.get("mediaUrls") or item.get("media_urls"))
    media_required = bool_value(item.get("mediaRequired")) or bool_value(item.get("media_required"))
    if media_urls:
        payload["media"] = media_items_from_urls(media_urls)
    elif media_required:
        raise SocialError(
            "Media is required for this item, but no mediaUrls were provided. Generate/upload images before creating the draft."
        )

    return payload


def command_test(client: SocialClient, _args: argparse.Namespace) -> int:
    accounts = normalize_items(client.accounts(), ("accounts", "data", "items"))
    posts = client.posts_list(limit="3", skip="0")
    user_ref = default_user_reference(None)

    print(
        json.dumps(
            {
                "ok": True,
                "base_url": client.api_base_url,
                "api_version": client.api_version,
                "location_id": client.location_id,
                "token_present": True,
                "token_starts_with_pit": client.token.startswith("pit-"),
                "accounts_count": len(accounts),
                "user_default_present": bool(user_ref),
                "user_default_kind": user_reference_kind(user_ref),
                "users_check": "skipped_use_GHL_USER_or_item_user",
                "posts_list_probe": posts,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_accounts(client: SocialClient, _args: argparse.Namespace) -> int:
    print(json.dumps(client.accounts(), ensure_ascii=False, indent=2))
    return 0


def command_categories(client: SocialClient, _args: argparse.Namespace) -> int:
    print(json.dumps(client.categories(), ensure_ascii=False, indent=2))
    return 0


def command_tags(client: SocialClient, _args: argparse.Namespace) -> int:
    print(json.dumps(client.tags(), ensure_ascii=False, indent=2))
    return 0


def command_users(client: SocialClient, _args: argparse.Namespace) -> int:
    print(json.dumps(client.users(), ensure_ascii=False, indent=2))
    return 0


def command_posts_list(client: SocialClient, args: argparse.Namespace) -> int:
    print(json.dumps(client.posts_list(limit=str(args.limit), skip=str(args.skip)), ensure_ascii=False, indent=2))
    return 0


def resolve_default_user_id(client: SocialClient, explicit: str | None) -> str:
    return resolve_user_reference(client, default_user_reference(explicit), "default user")


def command_draft(client: SocialClient, args: argparse.Namespace) -> int:
    default_user_id = resolve_default_user_id(client, args.user)
    schedule_date = parse_schedule(args.schedule_local, args.timezone)

    status = (args.status or "draft").strip().lower()
    if status not in ALLOWED_STATUSES:
        raise SocialError(f"Invalid status: {status}")
    if status != "draft" and args.confirm_publish != "yes":
        raise SocialError("Non-draft status requires --confirm-publish yes")

    payload: dict[str, Any] = {
        "accountIds": args.account_id,
        "summary": args.summary,
        "type": args.type,
        "status": status,
    }
    if default_user_id:
        payload["userId"] = default_user_id
    if schedule_date:
        payload["scheduleDate"] = schedule_date

    if status == "scheduled" and "scheduleDate" not in payload:
        raise SocialError("Scheduled status requires --schedule-local")

    media_urls = list(args.media_url or [])
    media_uploads = upload_media_files(client, list(args.media_file or []))
    media_urls.extend(upload["url"] for upload in media_uploads)
    if args.media_required == "yes" and not media_urls:
        raise SocialError("Media is required, but no --media-url or --media-file was provided")
    if media_urls:
        payload["media"] = media_items_from_urls(media_urls)

    response = client.create_post(payload)
    assert_success_response(response, "Create post")
    post_id = post_id_from_response(response)

    result = {
        "ok": True,
        "mode": "single",
        "requested_status": status,
        "post_id": post_id,
        "media_count": len(payload.get("media", [])),
        "uploaded_media": media_uploads,
        "response": response,
    }
    if not post_id:
        result["warning"] = "Create post response did not include a recognizable social post id."
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_batch_draft(client: SocialClient, args: argparse.Namespace) -> int:
    mode = args.mode.strip().lower()
    if mode not in {"continue", "strict"}:
        raise SocialError("Invalid mode. Use continue or strict")

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SocialError("Batch input must be a JSON object")

    posts = data.get("posts")
    if not isinstance(posts, list) or not posts:
        raise SocialError("Batch input must include non-empty posts[] array")

    timezone = first_string(args.timezone, data.get("timezone"), DEFAULT_TIMEZONE) or DEFAULT_TIMEZONE
    resolved_user_id: str | None = None
    raw_default_user = default_user_reference(args.user)
    if not resolved_user_id and any(
        isinstance(item, dict) and not item_user_reference(item) for item in posts
    ):
        resolved_user_id = resolve_user_reference(client, raw_default_user, "default user")
    default_accounts = list(args.account_id or [])
    manual_account_map = parse_account_map(args.account_map)
    account_map = dict(manual_account_map)

    account_mapping_report: dict[str, Any] = {
        "auto_lookup": "skipped",
        "manual_keys": sorted(manual_account_map.keys()),
    }
    needs_account_map = any(
        item_needs_account_mapping(item, default_accounts, account_map) for item in posts if isinstance(item, dict)
    )
    if needs_account_map:
        try:
            auto_map, ambiguous = build_auto_account_map(client.accounts())
            auto_keys: list[str] = []
            for key, account_id in auto_map.items():
                if key not in account_map:
                    account_map[key] = account_id
                    auto_keys.append(key)
            account_mapping_report = {
                "auto_lookup": "ok",
                "manual_keys": sorted(manual_account_map.keys()),
                "auto_keys": sorted(auto_keys),
                "ambiguous_keys": sorted(ambiguous.keys()),
            }
        except SocialError as error:
            account_mapping_report = {
                "auto_lookup": "failed",
                "manual_keys": sorted(account_map.keys()),
                "warning": "Accounts lookup failed. Items without accountId/accountIds or --account-map will fail.",
                "error": str(error),
                "status": error.status,
            }

    results: list[dict[str, Any]] = []
    ok_count = 0
    failed_count = 0

    for index, raw_item in enumerate(posts, start=1):
        if not isinstance(raw_item, dict):
            failed_count += 1
            results.append({"index": index, "ok": False, "error": "Item is not an object"})
            if mode == "strict":
                break
            continue

        item_id = first_string(raw_item.get("id")) or f"item-{index}"

        try:
            item = dict(raw_item)
            raw_item_user = item_user_reference(item)
            if raw_item_user:
                item["userId"] = resolve_user_reference(client, raw_item_user, f"item {item_id} user")
            elif resolved_user_id:
                item["userId"] = resolved_user_id

            media_uploads: list[dict[str, str]] = []
            media_files = string_list(item.get("mediaFiles") or item.get("media_files"))
            if media_files:
                media_urls = string_list(item.get("mediaUrls") or item.get("media_urls"))
                media_uploads = upload_media_files(client, media_files)
                media_urls.extend(upload["url"] for upload in media_uploads)
                item["mediaUrls"] = media_urls

            payload = create_payload_from_item(
                item,
                default_type=args.type,
                default_timezone=timezone,
                default_user_id=None,
                default_accounts=default_accounts,
                account_map=account_map,
            )
            if payload.get("status") != "draft" and args.confirm_publish != "yes":
                raise SocialError(
                    f"Item {item_id} requests status '{payload.get('status')}'. Non-draft in batch requires --confirm-publish yes"
                )

            response = client.create_post(payload)
            assert_success_response(response, "Create post")
            post_id = post_id_from_response(response)

            ok_count += 1
            result = {
                "index": index,
                "id": item_id,
                "ok": True,
                "post_id": post_id,
                "status": payload.get("status"),
                "media_count": len(payload.get("media", [])),
                "uploaded_media": media_uploads,
            }
            if not post_id:
                result["warning"] = "Create post response did not include a recognizable social post id."
            results.append(result)
        except Exception as error:  # noqa: BLE001
            failed_count += 1
            results.append({"index": index, "id": item_id, "ok": False, "error": str(error)})
            if mode == "strict":
                break

    print(
        json.dumps(
            {
                "ok": failed_count == 0,
                "mode": mode,
                "total": len(posts),
                "created": ok_count,
                "failed": failed_count,
                "account_mapping": account_mapping_report,
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_upload_media(client: SocialClient, args: argparse.Namespace) -> int:
    response = client.upload_media(args.file)
    assert_success_response(response, "Media upload")
    url = media_url_from_response(response)
    if not url:
        raise SocialError("Media upload response did not include a public URL")
    print(json.dumps({"ok": True, "url": url, "response": response}, ensure_ascii=False, indent=2))
    return 0


def command_attach_media(client: SocialClient, args: argparse.Namespace) -> int:
    media_urls = list(args.media_url or [])
    if args.file:
        uploaded = client.upload_media(args.file)
        assert_success_response(uploaded, "Media upload")
        url = media_url_from_response(uploaded)
        if not url:
            raise SocialError("Uploaded media has no public URL in response")
        media_urls.append(url)

    if not media_urls:
        raise SocialError("No media provided. Use --media-url or --file")

    payload = {"media": media_items_from_urls(media_urls)}
    response = client.update_post(args.post_id, payload)
    assert_success_response(response, "Attach media")
    print(json.dumps({"ok": True, "post_id": args.post_id, "media_count": len(media_urls), "response": response}, ensure_ascii=False, indent=2))
    return 0


def command_publish(client: SocialClient, args: argparse.Namespace) -> int:
    if args.confirm_publish != "yes":
        raise SocialError("Publishing requires --confirm-publish yes")
    response = client.update_post(args.post_id, {"status": "published"})
    assert_success_response(response, "Publish post")
    print(json.dumps({"ok": True, "post_id": args.post_id, "status": "published", "response": response}, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CliqSales/GHL Social Planner publisher")
    parser.add_argument("--env-file", help="Optional env file path.")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("test")
    sub.add_parser("accounts")
    sub.add_parser("categories")
    sub.add_parser("tags")
    sub.add_parser("users")

    posts_list = sub.add_parser("posts-list")
    posts_list.add_argument("--limit", default="10")
    posts_list.add_argument("--skip", default="0")

    draft = sub.add_parser("draft")
    draft.add_argument("--account-id", action="append", required=True)
    draft.add_argument("--summary", required=True)
    draft.add_argument("--type", default="post")
    draft.add_argument("--status", choices=sorted(ALLOWED_STATUSES), default="draft")
    draft.add_argument("--schedule-local", help="Local datetime, e.g. 2026-05-01 09:00")
    draft.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    draft.add_argument("--user", help="GHL user ID or email.")
    draft.add_argument("--confirm-publish", choices=["yes", "no"], default="no")
    draft.add_argument("--media-url", action="append")
    draft.add_argument("--media-file", action="append")
    draft.add_argument("--media-required", choices=["yes", "no"], default="no")

    batch = sub.add_parser("batch-draft")
    batch.add_argument("--input", required=True, help="Path to social-posts.json")
    batch.add_argument("--mode", choices=["continue", "strict"], default="continue")
    batch.add_argument("--type", default="post")
    batch.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    batch.add_argument("--user", help="Default GHL user ID or email.")
    batch.add_argument("--account-id", action="append", help="Default account ID; can be repeated")
    batch.add_argument("--account-map", help="platform_or_label:accountId,platform_or_label:accountId")
    batch.add_argument("--confirm-publish", choices=["yes", "no"], default="no")

    upload = sub.add_parser("upload-media")
    upload.add_argument("--file", required=True)

    attach = sub.add_parser("attach-media")
    attach.add_argument("--post-id", required=True)
    attach.add_argument("--media-url", action="append")
    attach.add_argument("--file")

    publish = sub.add_parser("publish")
    publish.add_argument("--post-id", required=True)
    publish.add_argument("--confirm-publish", choices=["yes", "no"], default="no")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    load_env_file(args.env_file)

    try:
        client = SocialClient()

        if args.command == "test":
            return command_test(client, args)
        if args.command == "accounts":
            return command_accounts(client, args)
        if args.command == "categories":
            return command_categories(client, args)
        if args.command == "tags":
            return command_tags(client, args)
        if args.command == "users":
            return command_users(client, args)
        if args.command == "posts-list":
            return command_posts_list(client, args)
        if args.command == "draft":
            return command_draft(client, args)
        if args.command == "batch-draft":
            return command_batch_draft(client, args)
        if args.command == "upload-media":
            return command_upload_media(client, args)
        if args.command == "attach-media":
            return command_attach_media(client, args)
        if args.command == "publish":
            return command_publish(client, args)

        raise SocialError(f"Unknown command: {args.command}")
    except SocialError as error:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": str(error),
                    "status": error.status,
                    "detail": error.detail,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
