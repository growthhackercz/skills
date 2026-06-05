#!/usr/bin/env python3
"""Draft-safe CliqSales / GoHighLevel Ad Manager helper."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_ENV_FILES = (
    "/home/node/.openclaw/secrets/cliqsales.env",
    "/home/node/.openclaw/secrets/ghl.env",
    "/home/node/.openclaw/.env",
)
DEFAULT_API_BASE_URL = "https://services.leadconnectorhq.com"
DEFAULT_API_VERSION = "2023-02-21"

PLATFORM_ALIASES = {
    "meta": "facebook",
    "fb": "facebook",
    "facebook": "facebook",
    "instagram": "facebook",
    "linkedin": "linkedin",
    "linked-in": "linkedin",
    "li": "linkedin",
    "google": "google",
    "google-ads": "google",
}

DRAFT_ENDPOINTS: dict[tuple[str, str], tuple[str, str]] = {
    ("facebook", "campaign"): ("PUT", "/ad-publishing/facebook/campaigns"),
    ("facebook", "adset"): ("PUT", "/ad-publishing/facebook/adsets"),
    ("facebook", "ad_set"): ("PUT", "/ad-publishing/facebook/adsets"),
    ("facebook", "ad"): ("PUT", "/ad-publishing/facebook/ads-v2"),
    ("linkedin", "campaign_group"): ("PUT", "/ad-publishing/linkedin/ads"),
    ("linkedin", "campaign"): ("PUT", "/ad-publishing/linkedin/ads"),
    ("linkedin", "full_campaign"): ("PUT", "/ad-publishing/linkedin/ads"),
    ("linkedin", "ad"): ("PUT", "/ad-publishing/linkedin/ads"),
    ("google", "assets"): ("POST", "/ad-publishing/google/assets"),
    ("google", "campaign"): ("PUT", "/ad-publishing/google/ads"),
    ("google", "full_campaign"): ("PUT", "/ad-publishing/google/ads"),
    ("google", "ad"): ("PUT", "/ad-publishing/google/ads"),
}

READ_PROBES: dict[str, tuple[str, ...]] = {
    "facebook": ("/ad-publishing/facebook/integration", "/ad-publishing/facebook/ad-accounts"),
    "google": ("/ad-publishing/google/integration", "/ad-publishing/google/ad-accounts"),
    "linkedin": ("/ad-publishing/linkedin/integration", "/ad-publishing/linkedin/ad-accounts"),
}

LIVE_STATUS_VALUES = {"active", "enabled", "published", "publish", "live", "running"}
STATUS_KEYS = {
    "status",
    "configured_status",
    "effective_status",
    "serving_status",
    "campaign_status",
    "ad_status",
    "adset_status",
}
SENSITIVE_KEY_PARTS = ("token", "secret", "password", "authorization", "api_key", "apikey")
LINKEDIN_MEDIA_TYPES = {"STANDARD_UPDATE", "SINGLE_VIDEO", "CAROUSEL"}
LINKEDIN_OBJECTIVE_ALIASES = {
    "CONVERSIONS": "LEAD_GENERATION",
    "CONVERSION": "LEAD_GENERATION",
    "LEAD": "LEAD_GENERATION",
    "LEADS": "LEAD_GENERATION",
    "LEAD_GEN": "LEAD_GENERATION",
    "LEAD_GENERATION": "LEAD_GENERATION",
    "SIGNUP": "LEAD_GENERATION",
    "SIGNUPS": "LEAD_GENERATION",
    "TRIAL": "LEAD_GENERATION",
    "TRIAL_SIGNUPS": "LEAD_GENERATION",
    "WEBSITE": "WEBSITE_VISIT",
    "WEBSITE_TRAFFIC": "WEBSITE_VISIT",
    "WEBSITE_VISIT": "WEBSITE_VISIT",
    "WEBSITE_VISITS": "WEBSITE_VISIT",
    "TRAFFIC": "WEBSITE_VISIT",
    "AWARENESS": "BRAND_AWARENESS",
    "BRAND_AWARENESS": "BRAND_AWARENESS",
    "ENGAGEMENT": "ENGAGEMENT",
    "VIDEO": "VIDEO_VIEWS",
    "VIDEO_VIEW": "VIDEO_VIEWS",
    "VIDEO_VIEWS": "VIDEO_VIEWS",
}
LINKEDIN_MEDIA_TYPE_ALIASES = {
    "CAROUSEL": "CAROUSEL",
    "DOCUMENT_CAROUSEL": "CAROUSEL",
    "IMAGE": "STANDARD_UPDATE",
    "SINGLE_IMAGE": "STANDARD_UPDATE",
    "STANDARD_UPDATE": "STANDARD_UPDATE",
    "STATIC": "STANDARD_UPDATE",
    "VIDEO": "SINGLE_VIDEO",
    "VIDEO_15S": "SINGLE_VIDEO",
    "SINGLE_VIDEO": "SINGLE_VIDEO",
}


class AdPublishError(RuntimeError):
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
            if parsed:
                os.environ.setdefault(parsed[0], parsed[1])
        return


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise AdPublishError(f"Missing required environment variable: {name}")
    return value


def sanitize_location_id(raw: str | None) -> str | None:
    if not raw:
        return None
    value = raw.strip()
    if value.startswith("loc_"):
        value = value[4:]
    if "http" in value or "/location/" in value:
        match = re.search(r"/location/([A-Za-z0-9]+)/?", value)
        if match:
            value = match.group(1)
    if value.startswith("loc_"):
        value = value[4:]
    return value.strip() or None


def normalize_platform(value: Any) -> str:
    key = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    platform = PLATFORM_ALIASES.get(key)
    if not platform:
        raise AdPublishError(f"Unsupported platform: {value}")
    return platform


def normalize_operation(value: Any) -> str:
    operation = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    if not operation:
        raise AdPublishError("Missing draft operation")
    if "publish" in operation:
        raise AdPublishError("Live publish operations are blocked in ad-publisher")
    return operation


def read_json_file(path: str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise AdPublishError(f"Invalid JSON file {path}: {error}") from error
    if not isinstance(data, dict):
        raise AdPublishError(f"Expected JSON object in {path}")
    return data


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_lower = str(key).lower()
            if any(part in key_lower for part in SENSITIVE_KEY_PARTS):
                redacted[key] = "<redacted>"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def append_query(endpoint: str, params: dict[str, str | None]) -> str:
    clean_params = {key: value for key, value in params.items() if value}
    if not clean_params:
        return endpoint
    parsed = urllib.parse.urlsplit(endpoint)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.extend(clean_params.items())
    return urllib.parse.urlunsplit((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        urllib.parse.urlencode(query),
        parsed.fragment,
    ))


def first_string(*values: Any) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, int):
            return str(value)
    return None


def normalize_key(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", str(value or "").strip()).strip("_").upper()


def normalize_linkedin_objective(value: Any) -> str:
    key = normalize_key(value)
    if not key:
        return "LEAD_GENERATION"
    return LINKEDIN_OBJECTIVE_ALIASES.get(key, key)


def normalize_linkedin_media_type(value: Any) -> str:
    key = normalize_key(value)
    media_type = LINKEDIN_MEDIA_TYPE_ALIASES.get(key, key)
    if media_type not in LINKEDIN_MEDIA_TYPES:
        raise AdPublishError(f"LinkedIn mediaType must be one of {sorted(LINKEDIN_MEDIA_TYPES)}; got {value!r}")
    return media_type


def linkedin_media_src(media: dict[str, Any], path: str) -> str:
    src = first_string(
        media.get("src"),
        media.get("url"),
        media.get("publicUrl"),
        media.get("publicURL"),
        media.get("assetUrl"),
        media.get("assetURL"),
        media.get("mediaUrl"),
        media.get("mediaURL"),
    )
    if src:
        return src
    local_path = first_string(media.get("localPath"), media.get("path"), media.get("filePath"))
    if local_path:
        raise AdPublishError(
            f"LinkedIn media at {path} only has localPath ({local_path}); "
            "GHL Ad Manager requires a public or media-manager src URL."
        )
    raise AdPublishError(f"LinkedIn media at {path} is missing src/url")


def prepare_linkedin_media(media: Any, path: str) -> dict[str, Any]:
    if not isinstance(media, dict):
        raise AdPublishError(f"LinkedIn media at {path} must be an object")
    prepared = dict(media)
    prepared["src"] = linkedin_media_src(media, path)
    prepared.pop("url", None)
    prepared.pop("publicUrl", None)
    prepared.pop("publicURL", None)
    prepared.pop("assetUrl", None)
    prepared.pop("assetURL", None)
    prepared.pop("mediaUrl", None)
    prepared.pop("mediaURL", None)
    prepared.pop("localPath", None)
    prepared.pop("path", None)
    prepared.pop("filePath", None)
    return prepared


def infer_linkedin_media_type(payload: dict[str, Any], campaign: dict[str, Any], ads: list[dict[str, Any]]) -> str:
    explicit = first_string(campaign.get("mediaType"), payload.get("mediaType"), campaign.get("format"), payload.get("format"))
    if explicit:
        return normalize_linkedin_media_type(explicit)
    media_items = [media for ad in ads for media in ad.get("media", []) if isinstance(media, dict)]
    if any(normalize_key(media.get("type")) == "VIDEO" for media in media_items):
        return "SINGLE_VIDEO"
    if len(media_items) > 1:
        return "CAROUSEL"
    return "STANDARD_UPDATE"


def first_mapping(*values: Any) -> dict[str, Any] | None:
    for value in values:
        if isinstance(value, dict):
            return value
    return None


def utc_iso(offset_days: int = 0) -> str:
    value = datetime.now(timezone.utc) + timedelta(days=offset_days)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def number_or_default(value: Any, default: int | float) -> int | float:
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return default
        return int(parsed) if parsed.is_integer() else parsed
    return default


def normalize_linkedin_budget(payload: dict[str, Any]) -> dict[str, Any]:
    budget = dict(first_mapping(payload.get("budget")) or {})
    amount = number_or_default(
        budget.get("amount")
        or payload.get("budgetAmount")
        or payload.get("dailyBudget")
        or payload.get("amount"),
        1,
    )
    budget_type = normalize_key(budget.get("budgetType") or payload.get("budgetType") or "DAILY")
    schedule_start = first_string(
        budget.get("scheduleStartDate"),
        payload.get("scheduleStartDate"),
        payload.get("startDate"),
    ) or utc_iso()
    schedule_end = first_string(
        budget.get("scheduleEndDate"),
        payload.get("scheduleEndDate"),
        payload.get("endDate"),
    ) or utc_iso(30)
    return {
        **budget,
        "amount": amount,
        "budgetType": budget_type,
        "scheduleStartDate": schedule_start,
        "scheduleEndDate": schedule_end,
    }


def require_non_empty_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list) or not value:
        raise AdPublishError(f"{path} must be a non-empty list")
    return value


def ensure_linkedin_audience(campaign: dict[str, Any], payload: dict[str, Any], path: str) -> dict[str, Any]:
    audience = first_mapping(campaign.get("audience"), payload.get("audience"), payload.get("targeting"))
    if not audience:
        raise AdPublishError(f"{path}.audience is required for LinkedIn drafts")
    geo_locations = audience.get("geo_locations") or audience.get("geoLocations") or audience.get("locations")
    require_non_empty_list(geo_locations, f"{path}.audience.geo_locations")
    prepared = dict(audience)
    prepared["geo_locations"] = geo_locations
    prepared.setdefault("targetAudience", {"include": [], "exclude": []})
    return prepared


def prepare_linkedin_ad(ad: dict[str, Any], payload: dict[str, Any], path: str) -> dict[str, Any]:
    media = require_non_empty_list(ad.get("media"), f"{path}.media")
    destination_url = first_string(ad.get("destinationUrl"), ad.get("landingUrl"), payload.get("landingUrl"), payload.get("url"))
    if not destination_url:
        raise AdPublishError(f"{path}.destinationUrl is required for LinkedIn drafts")
    introductory_text = first_string(ad.get("introductoryText"), ad.get("introText"), ad.get("primaryText"), ad.get("text"))
    if not introductory_text:
        raise AdPublishError(f"{path}.introductoryText is required for LinkedIn drafts")
    name = first_string(ad.get("name"), ad.get("sourceAdId"), ad.get("id"), ad.get("headline"), payload.get("name"))
    if not name:
        raise AdPublishError(f"{path}.name is required for LinkedIn drafts")

    prepared = dict(ad)
    prepared["name"] = name
    prepared["introductoryText"] = introductory_text
    prepared["destinationUrl"] = destination_url
    prepared["media"] = [prepare_linkedin_media(item, f"{path}.media[{index}]") for index, item in enumerate(media)]
    headline = first_string(ad.get("headline"), ad.get("name"))
    if headline:
        prepared["headline"] = headline
    description = first_string(ad.get("description"), payload.get("description"))
    if description:
        prepared["description"] = description
    if "cta" in prepared:
        cta = first_string(prepared.get("cta"))
        if cta:
            prepared["cta"] = normalize_key(cta)
    for old_key in ("introText", "primaryText", "landingUrl", "localPath"):
        prepared.pop(old_key, None)
    return prepared


def trim_media_for_linkedin_type(ad: dict[str, Any], media_type: str, path: str) -> dict[str, Any]:
    media = ad.get("media")
    if not isinstance(media, list):
        return ad
    if media_type == "CAROUSEL":
        if len(media) < 2:
            raise AdPublishError(f"{path}.media needs at least two media items for LinkedIn CAROUSEL")
        return ad
    preferred_type = "video" if media_type == "SINGLE_VIDEO" else "image"
    matching = [item for item in media if isinstance(item, dict) and normalize_key(item.get("type")) == preferred_type.upper()]
    if not matching:
        raise AdPublishError(f"{path}.media needs a {preferred_type} item for LinkedIn {media_type}")
    trimmed = dict(ad)
    trimmed["media"] = [matching[0]]
    return trimmed


def prepare_linkedin_campaign(campaign: dict[str, Any], payload: dict[str, Any], path: str) -> dict[str, Any]:
    ads_raw = require_non_empty_list(campaign.get("ads"), f"{path}.ads")
    ads = [ad for ad in ads_raw if isinstance(ad, dict)]
    if len(ads) != len(ads_raw):
        raise AdPublishError(f"{path}.ads must contain only objects")
    media_type = infer_linkedin_media_type(payload, campaign, ads)
    prepared_ads = [
        prepare_linkedin_ad(
            trim_media_for_linkedin_type(ad, media_type, f"{path}.ads[{index}]"),
            payload,
            f"{path}.ads[{index}]",
        )
        for index, ad in enumerate(ads)
    ]
    prepared = dict(campaign)
    prepared["name"] = first_string(campaign.get("name"), payload.get("campaignName"), payload.get("name")) or "Draft LinkedIn Campaign"
    prepared["mediaType"] = media_type
    prepared["publishingStatus"] = "DRAFT"
    prepared["locale"] = first_mapping(campaign.get("locale"), payload.get("locale")) or {"language": "en", "country": "US"}
    prepared["unitCost"] = first_mapping(campaign.get("unitCost"), payload.get("unitCost")) or {"amount": 1}
    prepared["audience"] = ensure_linkedin_audience(campaign, payload, path)
    prepared["ads"] = prepared_ads
    return prepared


def prepare_linkedin_payload(payload: dict[str, Any]) -> dict[str, Any]:
    prepared = dict(payload)
    prepared["publishingStatus"] = "DRAFT"
    prepared["objectiveType"] = normalize_linkedin_objective(
        prepared.get("objectiveType") or prepared.get("objective") or prepared.get("goal")
    )
    prepared.setdefault("adBudgetOptimization", "MAXIMUM_DELIVERY")
    prepared["budget"] = normalize_linkedin_budget(prepared)
    linked_in_ad_account_id = first_string(
        prepared.get("linkedInAdAccountId"),
        prepared.get("linkedinAdAccountId"),
        prepared.get("adAccountId"),
        prepared.get("accountId"),
        os.environ.get("GHL_LINKEDIN_AD_ACCOUNT_ID"),
    )
    if linked_in_ad_account_id:
        prepared["linkedInAdAccountId"] = linked_in_ad_account_id
    campaigns_raw = prepared.get("adCampaigns")
    if campaigns_raw is None and isinstance(prepared.get("ads"), list):
        campaigns_raw = [{
            "name": first_string(prepared.get("campaignName"), prepared.get("name")),
            "mediaType": prepared.get("mediaType") or prepared.get("format"),
            "locale": prepared.get("locale"),
            "unitCost": prepared.get("unitCost"),
            "audience": prepared.get("audience") or prepared.get("targeting"),
            "ads": prepared.get("ads"),
        }]
    campaigns = require_non_empty_list(campaigns_raw, "LinkedIn payload.adCampaigns")
    campaign_objects = [campaign for campaign in campaigns if isinstance(campaign, dict)]
    if len(campaign_objects) != len(campaigns):
        raise AdPublishError("LinkedIn payload.adCampaigns must contain only objects")
    prepared["adCampaigns"] = [
        prepare_linkedin_campaign(campaign, prepared, f"LinkedIn payload.adCampaigns[{index}]")
        for index, campaign in enumerate(campaign_objects)
    ]
    prepared.pop("ads", None)
    prepared.pop("adAccountId", None)
    prepared.pop("linkedinAdAccountId", None)
    prepared.pop("accountId", None)
    prepared.pop("budgetAmount", None)
    prepared.pop("dailyBudget", None)
    prepared.pop("amount", None)
    prepared.pop("budgetType", None)
    prepared.pop("scheduleStartDate", None)
    prepared.pop("scheduleEndDate", None)
    prepared.pop("startDate", None)
    prepared.pop("endDate", None)
    prepared.pop("objective", None)
    prepared.pop("goal", None)
    return prepared


def find_response_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("id", "_id", "adId", "campaignId", "campaignGroupId", "resourceId"):
            found = first_string(value.get(key))
            if found:
                return found
        for item in value.values():
            found = find_response_id(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_response_id(item)
            if found:
                return found
    return None


def is_live_publish_action(value: str) -> bool:
    raw = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return normalized in {
        "publish",
        "publish_now",
        "publish_live",
        "live_publish",
        "go_live",
    }


def assert_no_live_publish(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).strip().lower()
            item_path = f"{path}.{key}"
            if key_lower in {"endpoint", "path"} and isinstance(item, str) and "/publish" in item.lower():
                raise AdPublishError(f"Blocked live publish endpoint at {item_path}: {item}")
            if (
                key_lower == "url"
                and isinstance(item, str)
                and "/ad-publishing/" in item.lower()
                and "/publish" in item.lower()
            ):
                raise AdPublishError(f"Blocked live publish endpoint at {item_path}: {item}")
            if key_lower in {"operation", "publishintent", "publish_intent"}:
                raw = str(item).strip().lower()
                if "publish" in raw and raw != "draft":
                    raise AdPublishError(f"Blocked live publish intent at {item_path}: {item}")
            if key_lower == "action" and isinstance(item, str) and is_live_publish_action(item):
                raise AdPublishError(f"Blocked live publish intent at {item_path}: {item}")
            if key_lower in STATUS_KEYS and isinstance(item, str):
                status = item.strip().lower()
                if status in LIVE_STATUS_VALUES:
                    raise AdPublishError(f"Blocked live status at {item_path}: {item}")
            assert_no_live_publish(item, item_path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            assert_no_live_publish(item, f"{path}[{index}]")


def draft_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    drafts = data.get("drafts")
    if isinstance(drafts, list):
        items = [item for item in drafts if isinstance(item, dict)]
    elif "platform" in data and "payload" in data:
        items = [data]
    else:
        raise AdPublishError("Input must include drafts[] or a single {platform, operation, payload} object")
    if not items:
        raise AdPublishError("No draft items found")
    return items


def resolve_request(item: dict[str, Any], default_location_id: str | None) -> dict[str, Any]:
    if item.get("draftOnly") is False:
        raise AdPublishError(f"Draft item {item.get('id') or '<unknown>'} has draftOnly=false")

    platform = normalize_platform(item.get("platform"))
    operation = normalize_operation(item.get("operation") or item.get("type") or "campaign")
    endpoint_key = (platform, operation)
    if endpoint_key not in DRAFT_ENDPOINTS:
        raise AdPublishError(f"Unsupported draft operation: {platform}/{operation}")

    method, endpoint = DRAFT_ENDPOINTS[endpoint_key]
    payload = item.get("payload")
    if not isinstance(payload, dict):
        raise AdPublishError(f"Draft item {item.get('id') or '<unknown>'} is missing payload object")

    payload = dict(payload)
    location_id = sanitize_location_id(first_string(item.get("locationId"), default_location_id))
    if location_id and "locationId" not in payload:
        payload["locationId"] = location_id
    assert_no_live_publish(payload)
    if platform == "linkedin":
        payload = prepare_linkedin_payload(payload)
        assert_no_live_publish(payload)

    return {
        "id": first_string(item.get("id")) or f"{platform}-{operation}",
        "platform": platform,
        "operation": operation,
        "method": method,
        "endpoint": endpoint,
        "payload": payload,
    }


def assert_draft_response_visible(request: dict[str, Any], response: Any) -> None:
    if request["platform"] != "linkedin":
        return
    if not isinstance(response, dict):
        raise AdPublishError(f"LinkedIn draft {request['id']} returned a non-object response")
    if not isinstance(response.get("budget"), dict):
        raise AdPublishError(
            f"GHL accepted LinkedIn draft {request['id']} but returned no root budget; "
            "the draft is not visible in the Ad Manager campaign dashboard."
        )
    if not first_string(response.get("linkedInAdAccountId")):
        raise AdPublishError(
            f"GHL accepted LinkedIn draft {request['id']} but returned no linkedInAdAccountId; "
            "the draft is not tied to a LinkedIn ad account."
        )
    campaigns = response.get("adCampaigns")
    if not isinstance(campaigns, list) or not campaigns:
        raise AdPublishError(
            f"GHL accepted LinkedIn draft {request['id']} but returned no adCampaigns; "
            "the draft is not a visible Ad Manager campaign. Use adCampaigns[].ads[] payload schema."
        )
    ad_count = 0
    for campaign in campaigns:
        if isinstance(campaign, dict) and isinstance(campaign.get("ads"), list):
            ad_count += len(campaign["ads"])
    if ad_count == 0:
        raise AdPublishError(
            f"GHL accepted LinkedIn draft {request['id']} but returned no ads; "
            "the draft is not a visible Ad Manager ad."
        )


def resolve_requests(data: dict[str, Any], env_location_id: str | None = None) -> list[dict[str, Any]]:
    if data.get("draftOnly") is False:
        raise AdPublishError("Top-level draftOnly=false is blocked")
    assert_no_live_publish(data)
    default_location_id = sanitize_location_id(first_string(data.get("locationId"), env_location_id))
    return [resolve_request(item, default_location_id) for item in draft_items(data)]


class GHLClient:
    def __init__(self) -> None:
        self.token = require_env("GHL_API_KEY")
        self.location_id = sanitize_location_id(os.environ.get("GHL_LOCATION_ID"))
        self.api_base_url = os.environ.get("GHL_API_BASE_URL", DEFAULT_API_BASE_URL).strip() or DEFAULT_API_BASE_URL
        self.api_base_url = self.api_base_url.rstrip("/")
        self.api_version = os.environ.get("GHL_API_VERSION", DEFAULT_API_VERSION).strip() or DEFAULT_API_VERSION
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ControlCenterCliqSalesAdPublisher/1.0",
        }

    def request(self, method: str, endpoint: str, data: dict[str, Any] | None = None) -> Any:
        if "/publish" in endpoint.lower():
            raise AdPublishError(f"Blocked live publish endpoint: {endpoint}")
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        req = urllib.request.Request(
            url,
            data=json_dumps(data) if data is not None else None,
            headers=self.headers,
            method=method,
        )
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
            raise AdPublishError(f"GHL API returned HTTP {error.code}: {detail_text[:1000]}", error.code, detail_obj)
        except urllib.error.URLError as error:
            raise AdPublishError(f"GHL request failed: {error.reason}")

    def ensure_linkedin_account(self, request: dict[str, Any]) -> None:
        if request["platform"] != "linkedin":
            return
        payload = request["payload"]
        if first_string(payload.get("linkedInAdAccountId")):
            return
        location_id = sanitize_location_id(first_string(payload.get("locationId"), self.location_id))
        integration = self.request(
            "GET",
            append_query("/ad-publishing/linkedin/integration", {"locationId": location_id}),
        )
        if not isinstance(integration, dict):
            raise AdPublishError(f"LinkedIn draft {request['id']} could not read integration details")
        ad_account_id = first_string(integration.get("adAccountId"), integration.get("linkedInAdAccountId"))
        if not ad_account_id:
            raise AdPublishError(
                f"LinkedIn draft {request['id']} is missing linkedInAdAccountId and the integration has no adAccountId"
            )
        payload["linkedInAdAccountId"] = ad_account_id
        if integration.get("currencyCode") and "currencyCode" not in payload:
            payload["currencyCode"] = integration["currencyCode"]
        if integration.get("organizationId") and "organizationId" not in payload:
            payload["organizationId"] = integration["organizationId"]

    def assert_linkedin_dashboard_visible(self, request: dict[str, Any], response: Any) -> None:
        if request["platform"] != "linkedin":
            return
        if not isinstance(response, dict):
            return
        response_id = find_response_id(response)
        if not response_id:
            raise AdPublishError(f"LinkedIn draft {request['id']} returned no response id")
        payload = request["payload"]
        budget = first_mapping(response.get("budget"), payload.get("budget")) or {}
        location_id = sanitize_location_id(first_string(response.get("locationId"), payload.get("locationId"), self.location_id))
        ad_account_id = first_string(response.get("linkedInAdAccountId"), payload.get("linkedInAdAccountId"))
        endpoint = append_query("/ad-publishing/campaigns", {
            "locationId": location_id,
            "startDate": first_string(budget.get("scheduleStartDate")) or utc_iso(-30),
            "endDate": first_string(budget.get("scheduleEndDate")) or utc_iso(365),
            "skip": "0",
            "limit": "1000",
            "type": "ALL",
            "linkedinAdAccountId": ad_account_id,
        })
        listing = self.request("GET", endpoint)
        items = listing.get("items") if isinstance(listing, dict) else None
        if not isinstance(items, list):
            raise AdPublishError(
                f"LinkedIn draft {request['id']} was created but dashboard list returned an unexpected response",
                detail=listing,
            )
        for item in items:
            if not isinstance(item, dict):
                continue
            if response_id in {
                first_string(item.get("id")) or "",
                first_string(item.get("parentAdId")) or "",
                first_string(item.get("_id")) or "",
            }:
                return
        raise AdPublishError(
            f"LinkedIn draft {request['id']} was created as {response_id}, "
            "but GHL Ad Manager dashboard list does not return it."
        )


def write_result(path: str | None, input_path: str | None, result: dict[str, Any]) -> None:
    output_path = path
    if not output_path and input_path:
        output_path = str(Path(input_path).with_name("ad-publish-result.json"))
    if output_path:
        Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result["resultPath"] = output_path


def command_validate(args: argparse.Namespace) -> int:
    data = read_json_file(args.input)
    requests = resolve_requests(data, os.environ.get("GHL_LOCATION_ID"))
    print(json.dumps({"ok": True, "draft_count": len(requests), "requests": requests}, ensure_ascii=False, indent=2))
    return 0


def command_test(args: argparse.Namespace) -> int:
    client = GHLClient()
    platforms = [normalize_platform(platform) for platform in (args.platform or ["facebook", "google", "linkedin"])]
    seen: set[str] = set()
    results: list[dict[str, Any]] = []
    for platform in platforms:
        if platform in seen:
            continue
        seen.add(platform)
        for endpoint in READ_PROBES[platform]:
            request_endpoint = append_query(endpoint, {"locationId": client.location_id})
            try:
                response = client.request("GET", request_endpoint)
                results.append({
                    "platform": platform,
                    "endpoint": request_endpoint,
                    "ok": True,
                    "response": redact_sensitive(response),
                })
            except AdPublishError as error:
                results.append({
                    "platform": platform,
                    "endpoint": request_endpoint,
                    "ok": False,
                    "error": str(error),
                    "status": error.status,
                    "detail": redact_sensitive(error.detail),
                })
    result = {
        "ok": all(item["ok"] for item in results),
        "base_url": client.api_base_url,
        "api_version": client.api_version,
        "token_present": True,
        "location_id_present": bool(client.location_id),
        "results": results,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def command_draft(args: argparse.Namespace) -> int:
    data = read_json_file(args.input)
    requests = resolve_requests(data, os.environ.get("GHL_LOCATION_ID"))
    if args.dry_run:
        result = {"ok": True, "dryRun": True, "draft_count": len(requests), "requests": requests}
        write_result(args.output, args.input, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if args.confirm_draft != "yes":
        raise AdPublishError("Real draft writes require --confirm-draft yes")

    client = GHLClient()
    requests = resolve_requests(data, client.location_id)
    mode = args.mode.strip().lower()
    results: list[dict[str, Any]] = []
    ok_count = 0
    failed_count = 0
    for request in requests:
        try:
            client.ensure_linkedin_account(request)
            response = client.request(request["method"], request["endpoint"], data=request["payload"])
            assert_draft_response_visible(request, response)
            client.assert_linkedin_dashboard_visible(request, response)
            ok_count += 1
            results.append({
                "id": request["id"],
                "platform": request["platform"],
                "operation": request["operation"],
                "endpoint": request["endpoint"],
                "ok": True,
                "responseId": find_response_id(response),
                "response": redact_sensitive(response),
            })
        except Exception as error:  # noqa: BLE001
            failed_count += 1
            item: dict[str, Any] = {
                "id": request["id"],
                "platform": request["platform"],
                "operation": request["operation"],
                "endpoint": request["endpoint"],
                "ok": False,
                "error": str(error),
            }
            if isinstance(error, AdPublishError):
                item["status"] = error.status
                item["detail"] = redact_sensitive(error.detail)
            results.append(item)
            if mode == "strict":
                break
    result = {
        "ok": failed_count == 0,
        "mode": mode,
        "dryRun": False,
        "total": len(requests),
        "created": ok_count,
        "failed": failed_count,
        "results": results,
    }
    write_result(args.output, args.input, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if failed_count == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Draft-safe CliqSales/GHL Ad Manager helper")
    parser.add_argument("--env-file", help="Optional env file path.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--input", required=True)
    test = sub.add_parser("test")
    test.add_argument("--platform", action="append")
    draft = sub.add_parser("draft")
    draft.add_argument("--input", required=True)
    draft.add_argument("--mode", choices=["continue", "strict"], default="continue")
    draft.add_argument("--confirm-draft", choices=["yes", "no"], default="no")
    draft.add_argument("--dry-run", action="store_true")
    draft.add_argument("--output")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    load_env_file(args.env_file)
    try:
        if args.command == "validate":
            return command_validate(args)
        if args.command == "test":
            return command_test(args)
        if args.command == "draft":
            return command_draft(args)
        raise AdPublishError(f"Unknown command: {args.command}")
    except AdPublishError as error:
        print(json.dumps({
            "ok": False,
            "error": str(error),
            "status": error.status,
            "detail": redact_sensitive(error.detail),
        }, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
