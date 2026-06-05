#!/usr/bin/env python3
"""Small CliqSales/GoHighLevel Blog API publisher for Control Center skills.

Credentials are read from environment variables or an env file. Do not pass
credentials on the command line.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import mimetypes
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any


DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/cliqsales.env",
    "/home/node/.openclaw/secrets/ghl.env",
    "/home/node/.openclaw/.env",
)

DEFAULT_API_BASE_URL = "https://services.leadconnectorhq.com"
DEFAULT_API_VERSION = "2021-07-28"
ALLOWED_STATUSES = {"DRAFT", "PUBLISHED", "SCHEDULED", "ARCHIVED"}


class GHLError(RuntimeError):
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
            os.environ.setdefault(key, value)
        return


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise GHLError(f"Missing required environment variable: {name}")
    return value


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def first_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
    return None


def string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def split_csv(values: list[str] | None, fallback: str = "") -> list[str]:
    raw: list[str] = []
    if values:
        raw.extend(values)
    if fallback:
        raw.append(fallback)
    parts: list[str] = []
    for value in raw:
        parts.extend(part.strip() for part in value.split(","))
    return [part for part in parts if part]


def slugify(value: str) -> str:
    normalized = html.unescape(value).strip().lower()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-")


def strip_metadata_comment(content: str) -> str:
    return re.sub(r"^\s*<!--\s*ARTICLE METADATA.*?-->\s*", "", content, flags=re.S)


def strip_title_heading(content: str) -> str:
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", content, count=1, flags=re.I | re.S)


def extract_title(content: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", content, flags=re.I | re.S)
    if not match:
        return None
    return re.sub(r"<[^>]+>", "", html.unescape(match.group(1))).strip() or None


def read_content(path: str, keep_h1: bool = False) -> tuple[str, str | None]:
    raw = Path(path).read_text(encoding="utf-8")
    title = extract_title(raw)
    content = strip_metadata_comment(raw).strip()
    if not keep_h1:
        content = strip_title_heading(content).strip()
    return content, title


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json_file(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise GHLError(f"Invalid JSON file {path}: {error}") from error
    if not isinstance(data, dict):
        raise GHLError(f"Expected JSON object in {path}")
    return data


def infer_metadata_path(input_path: str) -> str | None:
    candidate = Path(input_path).with_name("article-metadata.json")
    return str(candidate) if candidate.exists() else None


def read_metadata(input_path: str, metadata_path: str | None) -> dict[str, Any]:
    path = metadata_path or infer_metadata_path(input_path)
    if not path:
        return {}
    return read_json_file(path)


def manifest_images(data: dict[str, Any]) -> list[dict[str, Any]]:
    images = data.get("images")
    if isinstance(images, list):
        return [item for item in images if isinstance(item, dict)]
    assets = data.get("assets")
    if isinstance(assets, list):
        return [item for item in assets if isinstance(item, dict)]
    return []


def insert_after_span(content: str, span_end: int, block: str) -> str:
    return f"{content[:span_end].rstrip()}\n\n{block}\n\n{content[span_end:].lstrip()}"


def find_nth_tag_end(content: str, tag: str, ordinal: int) -> int | None:
    pattern = re.compile(rf"<{tag}[^>]*>.*?</{tag}>", re.I | re.S)
    for index, match in enumerate(pattern.finditer(content), start=1):
        if index == ordinal:
            return match.end()
    return None


def image_html(asset: dict[str, Any]) -> str:
    url = first_string(
        asset.get("ghlUrl"),
        asset.get("ghl_url"),
        asset.get("wpUrl"),
        asset.get("wp_url"),
        asset.get("url"),
        asset.get("source_url"),
    )
    if not url:
        raise GHLError(f"Asset is missing public URL: {asset.get('id') or asset.get('filename') or 'unknown'}")
    alt = first_string(asset.get("alt"), asset.get("altText"), asset.get("alt_text")) or ""
    caption = first_string(asset.get("caption")) or ""
    if caption:
        return (
            f"<figure><img src=\"{html.escape(url, quote=True)}\" alt=\"{html.escape(alt, quote=True)}\"/>"
            f"<figcaption>{html.escape(caption)}</figcaption></figure>"
        )
    return f"<figure><img src=\"{html.escape(url, quote=True)}\" alt=\"{html.escape(alt, quote=True)}\"/></figure>"


def inject_asset_images_html(content: str, asset_manifest_path: str) -> str:
    data = read_json_file(asset_manifest_path)
    assets = manifest_images(data)
    if not assets:
        return content

    result = content
    deferred: list[str] = []

    for asset in assets:
        block = image_html(asset)
        placement = (first_string(asset.get("placement"), asset.get("position")) or "").lower()
        insert_at: int | None = None

        if placement == "hero" or first_string(asset.get("id")) == "hero":
            insert_at = find_nth_tag_end(result, "h1", 1)
            if insert_at is None:
                insert_at = 0
        elif placement == "after_intro":
            insert_at = find_nth_tag_end(result, "p", 1)
        else:
            h2_match = re.match(r"after_h2:(\d+)$", placement)
            if h2_match:
                insert_at = find_nth_tag_end(result, "h2", int(h2_match.group(1)))

        if insert_at is None:
            deferred.append(block)
            continue
        result = insert_after_span(result, insert_at, block)

    if deferred:
        result = f"{result.rstrip()}\n\n" + "\n\n".join(deferred) + "\n"
    return result


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


def extract_public_url(payload: Any) -> str | None:
    value = find_in_tree(payload, {"url", "fileUrl", "publicUrl", "sourceUrl", "cdnUrl", "signedUrl"})
    return value.strip() if isinstance(value, str) and value.strip() else None


def extract_media_id(payload: Any) -> str | None:
    value = find_in_tree(payload, {"id", "_id", "mediaId", "fileId"})
    if isinstance(value, (str, int)):
        return str(value)
    return None


def build_multipart_body(fields: dict[str, str], file_field: str, file_path: str) -> tuple[bytes, str]:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise GHLError(f"Media file not found: {file_path}")
    if path.stat().st_size <= 0:
        raise GHLError(f"Media file is empty: {file_path}")

    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    boundary = f"----CodexBoundary{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for key, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8"),
                str(value).encode("utf-8"),
                b"\r\n",
            ]
        )

    chunks.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\n'.encode("utf-8"),
            f"Content-Type: {mime_type}\r\n\r\n".encode("utf-8"),
            path.read_bytes(),
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ]
    )

    return b"".join(chunks), boundary


def sanitize_location_id(raw: str) -> str:
    value = raw.strip()
    if not value:
        return value

    if value.startswith("loc_"):
        value = value[4:]

    if "http" in value or "/location/" in value:
        match = re.search(r"/location/([A-Za-z0-9]+)/?", value)
        if match:
            value = match.group(1)

    if value.startswith("loc_"):
        value = value[4:]

    return value.strip()


def credential_diagnostics(token: str, location_raw: str, location_clean: str) -> dict[str, Any]:
    return {
        "token_present": bool(token),
        "token_starts_with_pit": token.startswith("pit-"),
        "token_contains_literal_vars": ("$" in token or "{{" in token or "}}" in token),
        "location_value": location_raw,
        "location_clean": location_clean,
        "location_starts_with_loc_prefix": location_raw.startswith("loc_"),
        "location_contains_http_or_slash": ("http" in location_raw or "/" in location_raw),
    }


class GHLClient:
    def __init__(self) -> None:
        self.token = require_env("GHL_API_KEY")
        self.location_raw = require_env("GHL_LOCATION_ID")
        self.location_id = sanitize_location_id(self.location_raw)
        if not self.location_id:
            raise GHLError("GHL_LOCATION_ID is empty after sanitization")

        self.api_base_url = os.environ.get("GHL_API_BASE_URL", DEFAULT_API_BASE_URL).strip() or DEFAULT_API_BASE_URL
        self.api_base_url = self.api_base_url.rstrip("/")
        self.api_version = os.environ.get("GHL_API_VERSION", DEFAULT_API_VERSION).strip() or DEFAULT_API_VERSION

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ControlCenterCliqSalesPublisher/1.0",
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

        request = urllib.request.Request(url, data=body, headers=request_headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
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
                raise GHLError(f"Authentication failed (401). {safe_detail}", error.code, detail_obj)
            if error.code == 403:
                raise GHLError(f"Permission denied (403). {safe_detail}", error.code, detail_obj)
            raise GHLError(f"GHL API returned HTTP {error.code}: {safe_detail}", error.code, detail_obj)
        except urllib.error.URLError as error:
            raise GHLError(f"GHL request failed: {error.reason}")

    def list_blogs(self) -> Any:
        return self.request("GET", "/blogs/site/all", params={"locationId": self.location_id})

    def list_authors(self, limit: int = 10, offset: int = 0) -> Any:
        return self.request(
            "GET",
            "/blogs/authors",
            params={"locationId": self.location_id, "limit": limit, "offset": offset},
        )

    def list_categories(self, limit: int = 10, offset: int = 0) -> Any:
        return self.request(
            "GET",
            "/blogs/categories",
            params={"locationId": self.location_id, "limit": limit, "offset": offset},
        )

    def list_posts(self, blog_id: str, limit: int = 10, offset: int = 0) -> Any:
        safe_limit = max(1, min(limit, 10))
        safe_offset = max(0, offset)
        return self.request(
            "GET",
            "/blogs/posts/all",
            params={
                "locationId": self.location_id,
                "blogId": blog_id,
                "limit": safe_limit,
                "offset": safe_offset,
            },
        )

    def check_slug(self, slug: str) -> bool:
        response = self.request(
            "GET",
            "/blogs/posts/url-slug-exists",
            params={"locationId": self.location_id, "urlSlug": slug},
        )
        if isinstance(response, dict):
            exists = response.get("exists")
            if isinstance(exists, bool):
                return exists
        raise GHLError(f"Unexpected slug check response format: {response}")

    def create_post(self, payload: dict[str, Any]) -> Any:
        return self.request("POST", "/blogs/posts", data=payload)

    def update_post(self, post_id: str, payload: dict[str, Any]) -> Any:
        return self.request("PUT", f"/blogs/posts/{post_id}", data=payload)

    def get_location(self) -> Any:
        return self.request("GET", f"/locations/{self.location_id}")

    def upload_media_file(self, file_path: str) -> Any:
        body, boundary = build_multipart_body({"hosted": "false"}, "file", file_path)
        headers = {
            "Authorization": self.headers["Authorization"],
            "Version": self.headers["Version"],
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": self.headers["User-Agent"],
        }
        return self.request(
            "POST",
            "/medias/upload-file",
            params={"locationId": self.location_id},
            headers=headers,
            raw_body=body,
        )


def normalize_collection(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("blogs", "authors", "categories", "posts", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def summarize_post(payload: Any) -> dict[str, Any]:
    post: dict[str, Any]
    if isinstance(payload, dict) and isinstance(payload.get("blogPost"), dict):
        post = payload["blogPost"]
    elif isinstance(payload, dict):
        post = payload
    else:
        post = {}

    post_id = first_string(post.get("_id"), post.get("id"))
    slug = first_string(post.get("urlSlug"), post.get("slug"))
    status = first_string(post.get("status"))
    blog_id = first_string(post.get("blogId"))
    title = first_string(post.get("title"))
    link = first_string(post.get("url"), post.get("link"), post.get("publicUrl"), post.get("postUrl"))

    return {
        "post_id": post_id,
        "title": title,
        "status": status,
        "slug": slug,
        "blog_id": blog_id,
        "link": link,
    }


def command_test(client: GHLClient, _args: argparse.Namespace) -> int:
    diagnostics = credential_diagnostics(client.token, client.location_raw, client.location_id)
    blogs = client.list_blogs()
    blog_items = normalize_collection(blogs)

    print(
        json.dumps(
            {
                "ok": True,
                "base_url": client.api_base_url,
                "api_version": client.api_version,
                "location_id": client.location_id,
                "credential_check": diagnostics,
                "blogs_count": len(blog_items),
                "blogs": blog_items,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def command_blogs(client: GHLClient, _args: argparse.Namespace) -> int:
    response = client.list_blogs()
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def command_authors(client: GHLClient, args: argparse.Namespace) -> int:
    response = client.list_authors(limit=args.limit, offset=args.offset)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def command_categories(client: GHLClient, args: argparse.Namespace) -> int:
    response = client.list_categories(limit=args.limit, offset=args.offset)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def command_posts(client: GHLClient, args: argparse.Namespace) -> int:
    response = client.list_posts(blog_id=args.blog_id, limit=args.limit, offset=args.offset)
    print(json.dumps(response, ensure_ascii=False, indent=2))
    return 0


def command_check_slug(client: GHLClient, args: argparse.Namespace) -> int:
    exists = client.check_slug(args.slug)
    print(json.dumps({"slug": args.slug, "exists": exists}, ensure_ascii=False, indent=2))
    return 0


def command_assets(client: GHLClient, args: argparse.Namespace) -> int:
    image_manifest_path = Path(args.image_manifest)
    data = read_json_file(str(image_manifest_path))
    images = manifest_images(data)
    if not images:
        raise GHLError("Image manifest has no images.")

    assets: list[dict[str, Any]] = []
    for image in images:
        local_path = first_string(image.get("localPath"), image.get("path"), image.get("imagePath"))
        if not local_path:
            raise GHLError(f"Image is missing localPath: {image.get('id') or image.get('filename') or 'unknown'}")

        upload_response = client.upload_media_file(local_path)
        public_url = extract_public_url(upload_response)
        media_id = extract_media_id(upload_response)

        if not public_url:
            raise GHLError(
                "GHL media upload returned no public URL. "
                f"Response: {json.dumps(upload_response, ensure_ascii=False)[:500]}"
            )

        assets.append(
            {
                "id": first_string(image.get("id")) or Path(local_path).stem,
                "placement": first_string(image.get("placement"), image.get("position")) or "",
                "localPath": local_path,
                "filename": first_string(image.get("filename")) or Path(local_path).name,
                "alt": first_string(image.get("alt"), image.get("altText")) or "",
                "caption": first_string(image.get("caption")) or "",
                "ghlMediaId": media_id,
                "ghlUrl": public_url,
                "status": "uploaded",
            }
        )

    output_path = Path(args.output) if args.output else image_manifest_path.with_name("asset-manifest.json")
    asset_manifest = {
        "articleSlug": first_string(data.get("articleSlug")) or image_manifest_path.parent.name,
        "target": "cliqsales",
        "sourceImageManifest": str(image_manifest_path),
        "generatedAt": iso_now(),
        "assets": assets,
    }
    output_path.write_text(json.dumps(asset_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "asset_manifest": str(output_path),
                "uploaded": len(assets),
                "assets": assets,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def hero_from_manifest(path: str | None) -> tuple[str | None, str | None]:
    if not path:
        return None, None
    data = read_json_file(path)
    assets = manifest_images(data)
    if not assets:
        return None, None

    hero: dict[str, Any] | None = None
    for asset in assets:
        placement = (first_string(asset.get("placement"), asset.get("position")) or "").lower()
        if placement == "hero" or first_string(asset.get("id")) == "hero":
            hero = asset
            break
    if hero is None:
        hero = assets[0]

    url = first_string(
        hero.get("ghlUrl"),
        hero.get("ghl_url"),
        hero.get("wpUrl"),
        hero.get("wp_url"),
        hero.get("url"),
        hero.get("source_url"),
    )
    alt = first_string(hero.get("alt"), hero.get("altText"), hero.get("alt_text"))
    return url, alt


def command_draft(client: GHLClient, args: argparse.Namespace) -> int:
    metadata = read_metadata(args.input, args.metadata)
    content, extracted_title = read_content(args.input, keep_h1=args.keep_h1)

    if args.asset_manifest:
        content = inject_asset_images_html(content, args.asset_manifest)

    metadata_title = first_string(metadata.get("title"))
    metadata_slug = first_string(metadata.get("slug"))
    metadata_description = first_string(metadata.get("metaDescription"), metadata.get("meta_description"))
    metadata_primary_keyword = first_string(metadata.get("primaryKeyword"), metadata.get("primary_keyword"))
    metadata_secondary_keywords = string_list(metadata.get("secondaryKeywords") or metadata.get("secondary_keywords"))

    title = args.title or metadata_title or extracted_title
    if not title:
        raise GHLError("Missing title. Pass --title or include an <h1> in the content.")

    slug = args.slug or metadata_slug or slugify(title)
    if not slug:
        raise GHLError("Missing slug. Pass --slug or provide title/metadata.")

    requested_status = args.status or os.environ.get("GHL_DEFAULT_STATUS", "DRAFT")
    status = requested_status.strip().upper() or "DRAFT"
    if status not in ALLOWED_STATUSES:
        raise GHLError(f"Invalid status: {status}")
    if status != "DRAFT" and args.confirm_publish != "yes":
        raise GHLError("Non-draft status requires --confirm-publish yes.")
    if status == "SCHEDULED" and not args.published_at:
        raise GHLError("SCHEDULED status requires --published-at ISO datetime.")

    if not args.skip_slug_check:
        slug_exists = client.check_slug(slug)
        if slug_exists:
            raise GHLError(f"Slug already exists: {slug}")

    category_ids = split_csv(args.category)
    tag_names = split_csv(args.tag)
    if not tag_names:
        tag_names = [item for item in [metadata_primary_keyword, *metadata_secondary_keywords] if item]

    description = args.description or metadata_description
    hero_url, hero_alt = hero_from_manifest(args.asset_manifest)

    payload: dict[str, Any] = {
        "locationId": client.location_id,
        "blogId": args.blog_id,
        "title": title,
        "urlSlug": slug,
        "rawHTML": content,
        "status": status,
    }
    if description:
        payload["description"] = description
    if hero_url:
        payload["imageUrl"] = hero_url
    if hero_alt:
        payload["imageAltText"] = hero_alt
    if args.author:
        payload["author"] = args.author
    if category_ids:
        payload["categories"] = category_ids
    if tag_names:
        payload["tags"] = tag_names
    if status == "SCHEDULED" and args.published_at:
        payload["publishedAt"] = args.published_at

    response = client.create_post(payload)
    summary = summarize_post(response)
    summary["requested_status"] = status
    summary["slug_checked"] = not args.skip_slug_check

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def command_publish(client: GHLClient, args: argparse.Namespace) -> int:
    if args.confirm_publish != "yes":
        raise GHLError("Publishing requires --confirm-publish yes.")
    response = client.update_post(args.post_id, {"status": "PUBLISHED"})
    summary = summarize_post(response)
    summary["requested_status"] = "PUBLISHED"
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Center CliqSales/GHL blog publisher")
    parser.add_argument("--env-file", help="Optional env file path. Defaults to OpenClaw secret paths.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("test")
    subparsers.add_parser("blogs")

    authors = subparsers.add_parser("authors")
    authors.add_argument("--limit", type=int, default=10)
    authors.add_argument("--offset", type=int, default=0)

    categories = subparsers.add_parser("categories")
    categories.add_argument("--limit", type=int, default=10)
    categories.add_argument("--offset", type=int, default=0)

    posts = subparsers.add_parser("posts")
    posts.add_argument("--blog-id", required=True)
    posts.add_argument("--limit", type=int, default=10)
    posts.add_argument("--offset", type=int, default=0)

    check_slug = subparsers.add_parser("check-slug")
    check_slug.add_argument("--slug", required=True)

    assets = subparsers.add_parser("assets")
    assets.add_argument("--image-manifest", required=True)
    assets.add_argument("--output")

    draft = subparsers.add_parser("draft")
    draft.add_argument("--input", required=True)
    draft.add_argument("--blog-id", required=True)
    draft.add_argument("--title")
    draft.add_argument("--slug")
    draft.add_argument("--description")
    draft.add_argument("--metadata", help="Optional article-metadata.json. Defaults to sibling file next to --input.")
    draft.add_argument("--author")
    draft.add_argument("--category", action="append")
    draft.add_argument("--tag", action="append")
    draft.add_argument("--status", choices=sorted(ALLOWED_STATUSES))
    draft.add_argument("--published-at", help="ISO datetime required for SCHEDULED status")
    draft.add_argument("--asset-manifest", help="Optional asset-manifest.json; inserts image tags into rawHTML.")
    draft.add_argument("--keep-h1", action="store_true", help="Keep first H1 in rawHTML. Default removes it.")
    draft.add_argument("--skip-slug-check", action="store_true", help="Skip /url-slug-exists pre-check.")
    draft.add_argument("--confirm-publish", choices=["yes", "no"], default="no")

    publish = subparsers.add_parser("publish")
    publish.add_argument("--post-id", required=True)
    publish.add_argument("--confirm-publish", choices=["yes", "no"], default="no")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    load_env_file(args.env_file)

    try:
        client = GHLClient()
        if args.command == "test":
            return command_test(client, args)
        if args.command == "blogs":
            return command_blogs(client, args)
        if args.command == "authors":
            return command_authors(client, args)
        if args.command == "categories":
            return command_categories(client, args)
        if args.command == "posts":
            return command_posts(client, args)
        if args.command == "check-slug":
            return command_check_slug(client, args)
        if args.command == "assets":
            return command_assets(client, args)
        if args.command == "draft":
            return command_draft(client, args)
        if args.command == "publish":
            return command_publish(client, args)

        raise GHLError(f"Unknown command: {args.command}")
    except GHLError as error:
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
