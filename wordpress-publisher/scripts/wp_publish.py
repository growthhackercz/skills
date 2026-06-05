#!/usr/bin/env python3
"""Small WordPress REST publisher for Control Center skills.

Credentials are read from environment variables or an env file. Do not pass
credentials on the command line.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/wordpress.env",
    "/home/node/.openclaw/secrets/wp.env",
    "/home/node/.openclaw/.env",
)

ALLOWED_STATUSES = {"draft", "pending", "private", "publish"}
YOAST_META_MAP = {
    "_yoast_wpseo_title": "title",
    "_yoast_wpseo_metadesc": "description",
    "_yoast_wpseo_focuskw": "focus_keyphrase",
}
RANK_MATH_META_MAP = {
    "rank_math_title": "title",
    "rank_math_description": "description",
    "rank_math_focus_keyword": "focus_keyphrase",
}


class WordPressError(RuntimeError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


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
    candidates = []
    if path:
        candidates.append(path)
    openclaw_home = os.environ.get("OPENCLAW_HOME") or os.environ.get("CC_OPENCLAW_HOME")
    if openclaw_home:
        home = Path(openclaw_home).expanduser()
        if home.name not in {".openclaw", ".clawdbot"} and (home / ".openclaw").exists():
            home = home / ".openclaw"
        candidates.extend([
            str(home / "secrets" / "wordpress.env"),
            str(home / "secrets" / "wp.env"),
            str(home / ".env"),
        ])
    candidates.extend(candidate for candidate in DEFAULT_ENV_FILES if candidate not in candidates)
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


def load_wordpress_profile(profile: str | None, force: bool = False) -> None:
    skills_root = Path(__file__).resolve().parents[2]
    helper_path = skills_root / "_lib"
    if helper_path.exists():
        sys.path.insert(0, str(helper_path))
    try:
        import cc_credentials  # type: ignore
    except Exception:
        if profile:
            raise WordPressError("Control Center credential resolver is not available.")
        return

    data = cc_credentials.wordpress_profile(profile)
    if not data:
        if all(os.environ.get(key) for key in ("WP_SITE_URL", "WP_USERNAME", "WP_APPLICATION_PASSWORD")):
            return
        if profile:
            raise WordPressError(f"WordPress profile is not configured: {profile}")
        return

    values = {
        "WP_SITE_URL": data["site_url"],
        "WP_USERNAME": data["username"],
        "WP_APPLICATION_PASSWORD": data["application_password"],
    }
    for key, value in values.items():
        if force or not os.environ.get(key):
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise WordPressError(f"Missing required environment variable: {name}")
    return value


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


class WordPressClient:
    def __init__(self) -> None:
        site_url = require_env("WP_SITE_URL").rstrip("/")
        if not re.match(r"^https?://", site_url, flags=re.I):
            site_url = "https://" + site_url
        self.site_url = site_url
        self.api_base = f"{site_url}/wp-json/wp/v2"
        username = require_env("WP_USERNAME")
        password = require_env("WP_APPLICATION_PASSWORD").replace(" ", "")
        auth = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        self.headers = {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "ControlCenterWordPressPublisher/1.0",
        }

    def request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        if params:
            clean = {k: str(v) for k, v in params.items() if v is not None and v != ""}
            if clean:
                url += "?" + urllib.parse.urlencode(clean)
        body = json_dumps(data) if data is not None else None
        request = urllib.request.Request(url, data=body, headers=self.headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            safe_detail = detail[:500]
            if error.code == 401:
                raise WordPressError("Authentication failed. Check WP username and application password.", error.code)
            if error.code == 403:
                raise WordPressError("Permission denied. WordPress user needs editor/admin rights.", error.code)
            raise WordPressError(f"WordPress API returned HTTP {error.code}: {safe_detail}", error.code)
        except urllib.error.URLError as error:
            raise WordPressError(f"WordPress request failed: {error.reason}")

    def test(self) -> dict[str, Any]:
        return self.request("GET", "users/me", params={"context": "edit"})

    def categories(self) -> list[dict[str, Any]]:
        chunk = self.request("GET", "categories", params={"per_page": 100})
        return chunk if isinstance(chunk, list) else []

    def tags(self) -> list[dict[str, Any]]:
        chunk = self.request("GET", "tags", params={"per_page": 100})
        return chunk if isinstance(chunk, list) else []

    def post_meta_keys(self) -> set[str]:
        schema = self.request("OPTIONS", "posts")
        properties = schema.get("schema", {}).get("properties", {})
        meta = properties.get("meta", {})
        meta_properties = meta.get("properties", {})
        if not isinstance(meta_properties, dict):
            return set()
        return {str(key) for key in meta_properties}

    def get_or_create_category(self, name: str, create: bool = False) -> int | None:
        normalized = name.strip().lower()
        if not normalized:
            return None
        for category in self.categories():
            if str(category.get("name", "")).strip().lower() == normalized:
                return int(category["id"])
        if not create:
            raise WordPressError(f"Category not found: {name}. Re-run with --create-missing-taxonomy if approved.")
        created = self.request("POST", "categories", {"name": name.strip()})
        return int(created["id"])

    def get_or_create_tag(self, name: str, create: bool = True) -> int | None:
        normalized = name.strip().lower()
        if not normalized:
            return None
        for tag in self.tags():
            if str(tag.get("name", "")).strip().lower() == normalized:
                return int(tag["id"])
        if not create:
            return None
        created = self.request("POST", "tags", {"name": name.strip()})
        return int(created["id"])

    def create_post(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "posts", payload)

    def update_post(self, post_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", f"posts/{post_id}", payload)

    def upload_media(self, path: str, alt: str | None = None, caption: str | None = None) -> dict[str, Any]:
        media_path = Path(path)
        if not media_path.exists() or not media_path.is_file():
            raise WordPressError(f"Media file not found: {path}")
        if media_path.stat().st_size <= 0:
            raise WordPressError(f"Media file is empty: {path}")

        mime_type = mimetypes.guess_type(str(media_path))[0] or "application/octet-stream"
        filename = media_path.name
        headers = {
            "Authorization": self.headers["Authorization"],
            "Accept": "application/json",
            "Content-Type": mime_type,
            "Content-Disposition": f'attachment; filename="{filename}"',
            "User-Agent": self.headers["User-Agent"],
        }
        request = urllib.request.Request(
            f"{self.api_base}/media",
            data=media_path.read_bytes(),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read().decode("utf-8")
                media = json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            safe_detail = detail[:500]
            if error.code == 401:
                raise WordPressError("Authentication failed. Check WP username and application password.", error.code)
            if error.code == 403:
                raise WordPressError("Permission denied. WordPress user needs media upload rights.", error.code)
            raise WordPressError(f"WordPress media upload returned HTTP {error.code}: {safe_detail}", error.code)
        except urllib.error.URLError as error:
            raise WordPressError(f"WordPress media upload failed: {error.reason}")

        media_id = media.get("id")
        update_payload: dict[str, Any] = {}
        if alt:
            update_payload["alt_text"] = alt
        if caption:
            update_payload["caption"] = caption
        if media_id and update_payload:
            media = self.request("POST", f"media/{int(media_id)}", update_payload)
        return media


def split_csv(values: list[str] | None, fallback: str = "") -> list[str]:
    raw = []
    if values:
        raw.extend(values)
    if fallback:
        raw.append(fallback)
    parts: list[str] = []
    for value in raw:
        parts.extend(part.strip() for part in value.split(","))
    return [part for part in parts if part]


def strip_metadata_comment(content: str) -> str:
    return re.sub(r"^\s*<!--\s*ARTICLE METADATA.*?-->\s*", "", content, flags=re.S)


def strip_title_heading(content: str) -> str:
    """Remove the article H1 from post content; WordPress renders post title separately."""
    content = re.sub(
        r"^\s*<!--\s+wp:heading\s+\{[^}]*\"level\"\s*:\s*1[^}]*\}\s*-->\s*<h1[^>]*>.*?</h1>\s*<!--\s+/wp:heading\s+-->\s*",
        "",
        content,
        count=1,
        flags=re.I | re.S,
    )
    return re.sub(r"^\s*<h1[^>]*>.*?</h1>\s*", "", content, count=1, flags=re.I | re.S)


def extract_title(content: str) -> str | None:
    match = re.search(r"<h1[^>]*>(.*?)</h1>", content, flags=re.I | re.S)
    if not match:
        return None
    return re.sub(r"<[^>]+>", "", html.unescape(match.group(1))).strip() or None


def convert_to_gutenberg(content: str, keep_h1: bool = False) -> str:
    """Convert simple article HTML/Markdown into conservative Gutenberg blocks."""
    content = strip_metadata_comment(content).strip()
    if not keep_h1:
        content = strip_title_heading(content).strip()
    if "<!-- wp:" in content:
        return content

    blocks: list[str] = []
    token_pattern = re.compile(r"(<h[1-6][^>]*>.*?</h[1-6]>|<p[^>]*>.*?</p>|<blockquote[^>]*>.*?</blockquote>|<ul[^>]*>.*?</ul>|<ol[^>]*>.*?</ol>)", re.I | re.S)
    matches = list(token_pattern.finditer(content))

    if not matches:
        return markdown_to_gutenberg(content)

    for match in matches:
        token = match.group(1).strip()
        lower = token.lower()
        if lower.startswith("<h"):
            level_match = re.match(r"<h([1-6])", lower)
            level = int(level_match.group(1)) if level_match else 2
            attrs = "" if level == 2 else " " + json.dumps({"level": level}, separators=(",", ":"))
            blocks.append(f"<!-- wp:heading{attrs} -->\n{token}\n<!-- /wp:heading -->")
        elif lower.startswith("<p"):
            blocks.append(f"<!-- wp:paragraph -->\n{token}\n<!-- /wp:paragraph -->")
        elif lower.startswith("<blockquote"):
            blocks.append(f"<!-- wp:quote -->\n{token}\n<!-- /wp:quote -->")
        elif lower.startswith("<ul") or lower.startswith("<ol"):
            ordered = lower.startswith("<ol")
            attrs = " " + json.dumps({"ordered": True}, separators=(",", ":")) if ordered else ""
            blocks.append(f"<!-- wp:list{attrs} -->\n{token}\n<!-- /wp:list -->")

    return "\n\n".join(blocks).strip() + "\n"


def markdown_to_gutenberg(content: str) -> str:
    blocks: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(paragraph).strip()
        paragraph.clear()
        if text:
            blocks.append(f"<!-- wp:paragraph -->\n<p>{html.escape(text)}</p>\n<!-- /wp:paragraph -->")

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            continue
        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            text = html.escape(heading.group(2).strip())
            attrs = "" if level == 2 else " " + json.dumps({"level": level}, separators=(",", ":"))
            blocks.append(f"<!-- wp:heading{attrs} -->\n<h{level}>{text}</h{level}>\n<!-- /wp:heading -->")
            continue
        if line.startswith(">"):
            flush_paragraph()
            text = html.escape(line.lstrip("> ").strip())
            blocks.append(f"<!-- wp:quote -->\n<blockquote><p>{text}</p></blockquote>\n<!-- /wp:quote -->")
            continue
        paragraph.append(line)

    flush_paragraph()
    return "\n\n".join(blocks).strip() + "\n"


def read_content(path: str, convert: bool, keep_h1: bool = False) -> tuple[str, str | None]:
    raw = Path(path).read_text(encoding="utf-8")
    title = extract_title(raw)
    content = raw if keep_h1 else strip_title_heading(strip_metadata_comment(raw).strip())
    return (convert_to_gutenberg(raw, keep_h1=keep_h1) if convert else content, title)


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json_file(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise WordPressError(f"Invalid JSON file {path}: {error}") from error
    if not isinstance(data, dict):
        raise WordPressError(f"Expected JSON object in {path}")
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


def seo_meta_payload(available_keys: set[str], title: str | None, description: str | None, focus_keyphrase: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
    requested = {
        "title": title or "",
        "description": description or "",
        "focus_keyphrase": focus_keyphrase or "",
    }
    payload: dict[str, Any] = {}
    written: list[str] = []

    for mapping in (YOAST_META_MAP, RANK_MATH_META_MAP):
        for meta_key, source_key in mapping.items():
            value = requested[source_key]
            if meta_key in available_keys and value:
                payload[meta_key] = value
                written.append(meta_key)

    status = {
        "title": title,
        "description": description,
        "focus_keyphrase": focus_keyphrase,
        "excerpt_set": bool(description),
        "plugin_meta_written": written,
        "plugin_meta_available": bool(written),
    }
    if not written and any(requested.values()):
        status["plugin_meta_note"] = (
            "No writable Yoast/RankMath SEO meta fields are exposed by this site's WordPress REST schema; "
            "standard post title, slug, excerpt and tags were set instead."
        )
    return payload, status


def media_summary(media: dict[str, Any]) -> tuple[int | None, str | None]:
    media_id = first_int(media.get("id"))
    source_url = first_string(media.get("source_url"), media.get("guid", {}).get("rendered") if isinstance(media.get("guid"), dict) else None)
    return media_id, source_url


def image_block(asset: dict[str, Any]) -> str:
    media_id = first_int(asset.get("wpMediaId"), asset.get("wp_media_id"), asset.get("mediaId"), asset.get("id"))
    url = first_string(asset.get("wpUrl"), asset.get("wp_url"), asset.get("url"), asset.get("source_url"))
    if not url:
        raise WordPressError(f"Asset is missing WordPress URL: {asset.get('id') or asset.get('filename') or 'unknown'}")
    alt = first_string(asset.get("alt"), asset.get("altText"), asset.get("alt_text")) or ""
    caption = first_string(asset.get("caption")) or ""

    attrs: dict[str, Any] = {"sizeSlug": "large", "linkDestination": "none"}
    if media_id is not None:
        attrs["id"] = media_id
    attrs_json = " " + json.dumps(attrs, ensure_ascii=False, separators=(",", ":"))
    class_attr = f' class="wp-image-{media_id}"' if media_id is not None else ""
    caption_html = f"\n<figcaption>{html.escape(caption)}</figcaption>" if caption else ""
    return (
        f"<!-- wp:image{attrs_json} -->\n"
        f'<figure class="wp-block-image size-large"><img src="{html.escape(url, quote=True)}" '
        f'alt="{html.escape(alt, quote=True)}"{class_attr}/>{caption_html}</figure>\n'
        f"<!-- /wp:image -->"
    )


def insert_after_span(content: str, span_end: int, block: str) -> str:
    return f"{content[:span_end].rstrip()}\n\n{block}\n\n{content[span_end:].lstrip()}"


def find_nth_paragraph_end(content: str, ordinal: int) -> int | None:
    pattern = re.compile(r"<!-- wp:paragraph -->.*?<!-- /wp:paragraph -->", re.I | re.S)
    for index, match in enumerate(pattern.finditer(content), start=1):
        if index == ordinal:
            return match.end()
    return None


def find_nth_heading_end(content: str, level: int | None, ordinal: int) -> int | None:
    pattern = re.compile(r"<!-- wp:heading(?:\s+\{.*?\})?\s*-->.*?<!-- /wp:heading -->", re.I | re.S)
    count = 0
    for match in pattern.finditer(content):
        block = match.group(0)
        level_match = re.search(r"<h([1-6])\b", block, re.I)
        block_level = int(level_match.group(1)) if level_match else 2
        if level is not None and block_level != level:
            continue
        count += 1
        if count == ordinal:
            return match.end()
    return None


def inject_asset_blocks(content: str, asset_manifest_path: str) -> str:
    data = read_json_file(asset_manifest_path)
    assets = manifest_images(data)
    if not assets:
        return content

    result = content
    deferred: list[str] = []

    for asset in assets:
        block = image_block(asset)
        placement = first_string(asset.get("placement"), asset.get("position")) or ""
        placement = placement.lower()
        insert_at: int | None = None

        if placement == "hero" or first_string(asset.get("id")) == "hero":
            insert_at = find_nth_heading_end(result, 1, 1)
            if insert_at is None:
                insert_at = 0
        elif placement == "after_intro":
            insert_at = find_nth_paragraph_end(result, 2)
        else:
            h2_match = re.match(r"after_h2:(\d+)$", placement)
            if h2_match:
                insert_at = find_nth_heading_end(result, 2, int(h2_match.group(1)))

        if insert_at is None:
            deferred.append(block)
            continue
        result = insert_after_span(result, insert_at, block)

    if deferred:
        result = f"{result.rstrip()}\n\n" + "\n\n".join(deferred) + "\n"
    return result


def post_summary(site_url: str, post: dict[str, Any], categories: list[str], tags: list[str], seo_status: dict[str, Any] | None = None) -> dict[str, Any]:
    post_id = post.get("id")
    summary = {
        "post_id": post_id,
        "status": post.get("status"),
        "link": post.get("link"),
        "preview_url": post.get("guid", {}).get("rendered") or post.get("link"),
        "edit_url": f"{site_url}/wp-admin/post.php?post={post_id}&action=edit" if post_id else None,
        "categories": categories,
        "tags": tags,
    }
    if seo_status is not None:
        summary["seo"] = seo_status
    return summary


def command_test(client: WordPressClient, _args: argparse.Namespace) -> int:
    user = client.test()
    print(json.dumps({
        "ok": True,
        "site": client.site_url,
        "user": user.get("name") or user.get("slug"),
        "roles": user.get("roles", []),
    }, ensure_ascii=False, indent=2))
    return 0


def command_categories(client: WordPressClient, _args: argparse.Namespace) -> int:
    categories = client.categories()
    print(json.dumps([
        {"id": item.get("id"), "name": item.get("name"), "slug": item.get("slug"), "count": item.get("count")}
        for item in categories
    ], ensure_ascii=False, indent=2))
    return 0


def command_convert(_client: WordPressClient, args: argparse.Namespace) -> int:
    content, _title = read_content(args.input, convert=True, keep_h1=args.keep_h1)
    if args.asset_manifest:
        content = inject_asset_blocks(content, args.asset_manifest)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
    else:
        print(content)
    return 0


def command_assets(client: WordPressClient, args: argparse.Namespace) -> int:
    image_manifest_path = Path(args.image_manifest)
    data = read_json_file(str(image_manifest_path))
    images = manifest_images(data)
    if not images:
        raise WordPressError("Image manifest has no images.")

    assets: list[dict[str, Any]] = []
    for image in images:
        local_path = first_string(image.get("localPath"), image.get("path"), image.get("imagePath"))
        if not local_path:
            raise WordPressError(f"Image is missing localPath: {image.get('id') or image.get('filename') or 'unknown'}")
        media = client.upload_media(
            local_path,
            alt=first_string(image.get("alt"), image.get("altText")),
            caption=first_string(image.get("caption")),
        )
        media_id, source_url = media_summary(media)
        assets.append({
            "id": first_string(image.get("id")) or Path(local_path).stem,
            "placement": first_string(image.get("placement"), image.get("position")) or "",
            "localPath": local_path,
            "filename": first_string(image.get("filename")) or Path(local_path).name,
            "alt": first_string(image.get("alt"), image.get("altText")) or "",
            "caption": first_string(image.get("caption")) or "",
            "wpMediaId": media_id,
            "wpUrl": source_url,
            "status": "uploaded",
        })

    output_path = Path(args.output) if args.output else image_manifest_path.with_name("asset-manifest.json")
    asset_manifest = {
        "articleSlug": first_string(data.get("articleSlug")) or image_manifest_path.parent.name,
        "target": "wordpress",
        "sourceImageManifest": str(image_manifest_path),
        "generatedAt": iso_now(),
        "assets": assets,
    }
    output_path.write_text(json.dumps(asset_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "asset_manifest": str(output_path),
        "uploaded": len(assets),
        "assets": assets,
    }, ensure_ascii=False, indent=2))
    return 0


def command_draft(client: WordPressClient, args: argparse.Namespace) -> int:
    metadata = read_metadata(args.input, args.metadata)
    content, extracted_title = read_content(args.input, convert=not args.no_convert, keep_h1=args.keep_h1)
    if args.asset_manifest:
        if "<!-- wp:" not in content:
            content = convert_to_gutenberg(content, keep_h1=args.keep_h1)
        content = inject_asset_blocks(content, args.asset_manifest)

    metadata_title = first_string(metadata.get("title"))
    metadata_slug = first_string(metadata.get("slug"))
    metadata_description = first_string(metadata.get("metaDescription"), metadata.get("meta_description"))
    metadata_primary_keyword = first_string(metadata.get("primaryKeyword"), metadata.get("primary_keyword"))
    metadata_secondary_keywords = string_list(metadata.get("secondaryKeywords") or metadata.get("secondary_keywords"))

    title = args.title or metadata_title or extracted_title
    if not title:
        raise WordPressError("Missing title. Pass --title or include an <h1> in the content.")

    requested_status = args.status or os.environ.get("WP_DEFAULT_STATUS", "draft")
    status = requested_status.strip().lower() or "draft"
    if status not in ALLOWED_STATUSES:
        raise WordPressError(f"Invalid status: {status}")
    if status == "publish" and args.confirm_publish != "yes":
        raise WordPressError("Publishing requires --confirm-publish yes. Use draft first.")

    category_names = split_csv(args.category, os.environ.get("WP_DEFAULT_CATEGORY", ""))
    tag_names = split_csv(args.tag, os.environ.get("WP_DEFAULT_TAGS", ""))
    if not tag_names:
        tag_names = [item for item in [metadata_primary_keyword, *metadata_secondary_keywords] if item]
    category_ids = [
        category_id for category_id in (
            client.get_or_create_category(name, create=args.create_missing_taxonomy)
            for name in category_names
        ) if category_id is not None
    ]
    tag_ids = [
        tag_id for tag_id in (client.get_or_create_tag(name, create=True) for name in tag_names)
        if tag_id is not None
    ]

    seo_description = args.seo_description or args.excerpt or metadata_description
    focus_keyphrase = args.focus_keyphrase or metadata_primary_keyword
    seo_title = args.seo_title or title
    try:
        writable_meta = client.post_meta_keys()
    except WordPressError:
        writable_meta = set()
    seo_meta, seo_status = seo_meta_payload(writable_meta, seo_title, seo_description, focus_keyphrase)

    payload: dict[str, Any] = {
        "title": title,
        "content": content,
        "status": status,
    }
    slug = args.slug or metadata_slug
    if slug:
        payload["slug"] = slug
    if seo_description:
        payload["excerpt"] = seo_description
    if seo_meta:
        payload["meta"] = seo_meta
    if category_ids:
        payload["categories"] = category_ids
    if tag_ids:
        payload["tags"] = tag_ids

    post = client.create_post(payload)
    print(json.dumps(post_summary(client.site_url, post, category_names, tag_names, seo_status), ensure_ascii=False, indent=2))
    return 0


def command_publish(client: WordPressClient, args: argparse.Namespace) -> int:
    if args.confirm_publish != "yes":
        raise WordPressError("Publishing requires --confirm-publish yes.")
    post = client.update_post(args.post_id, {"status": "publish"})
    print(json.dumps(post_summary(client.site_url, post, [], []), ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control Center WordPress publisher")
    parser.add_argument("--env-file", help="Optional env file path. Defaults to OpenClaw secret paths.")
    parser.add_argument("--profile", help="Control Center WordPress profile slug. Defaults to the stored default profile.")

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("test")
    subparsers.add_parser("categories")

    convert = subparsers.add_parser("convert")
    convert.add_argument("--input", required=True)
    convert.add_argument("--output")
    convert.add_argument("--asset-manifest", help="Optional asset-manifest.json with WordPress media IDs/URLs.")
    convert.add_argument("--keep-h1", action="store_true", help="Keep the first H1 in post content. Default removes it because WordPress renders the post title separately.")

    assets = subparsers.add_parser("assets")
    assets.add_argument("--image-manifest", required=True)
    assets.add_argument("--output")

    draft = subparsers.add_parser("draft")
    draft.add_argument("--input", required=True)
    draft.add_argument("--title")
    draft.add_argument("--slug")
    draft.add_argument("--excerpt")
    draft.add_argument("--metadata", help="Optional article-metadata.json. Defaults to sibling article-metadata.json next to --input.")
    draft.add_argument("--seo-title")
    draft.add_argument("--seo-description")
    draft.add_argument("--focus-keyphrase")
    draft.add_argument("--category", action="append")
    draft.add_argument("--tag", action="append")
    draft.add_argument("--status", choices=sorted(ALLOWED_STATUSES))
    draft.add_argument("--no-convert", action="store_true", help="Send content as-is instead of wrapping Gutenberg blocks.")
    draft.add_argument("--keep-h1", action="store_true", help="Keep the first H1 in post content. Default removes it because WordPress renders the post title separately.")
    draft.add_argument("--asset-manifest", help="Optional asset-manifest.json; inserts WordPress image blocks into content.")
    draft.add_argument("--create-missing-taxonomy", action="store_true")
    draft.add_argument("--confirm-publish", choices=["yes", "no"], default="no")

    publish = subparsers.add_parser("publish")
    publish.add_argument("--post-id", required=True, type=int)
    publish.add_argument("--confirm-publish", choices=["yes", "no"], default="no")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        load_env_file(args.env_file)
        load_wordpress_profile(args.profile, force=bool(args.profile))

        if args.command == "convert":
            return command_convert(None, args)  # type: ignore[arg-type]

        client = WordPressClient()
        if args.command == "test":
            return command_test(client, args)
        if args.command == "categories":
            return command_categories(client, args)
        if args.command == "assets":
            return command_assets(client, args)
        if args.command == "draft":
            return command_draft(client, args)
        if args.command == "publish":
            return command_publish(client, args)
        parser.print_help()
        return 2
    except WordPressError as error:
        print(json.dumps({"ok": False, "error": str(error), "status": error.status}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
