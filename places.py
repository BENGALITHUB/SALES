"""Google Places API (New) client: Text Search + Place Details."""

import time

import requests

import config

logger = config.get_logger(__name__)

TEXT_SEARCH_FIELD_MASK = "places.id,places.displayName,places.formattedAddress,nextPageToken"
DETAILS_FIELD_MASK = (
    "id,displayName,formattedAddress,addressComponents,internationalPhoneNumber,websiteUri"
)


class PlacesAPIError(Exception):
    """Raised when the Google Places API returns an unrecoverable error."""


def _headers(field_mask: str) -> dict:
    if not config.API_KEY:
        raise PlacesAPIError("GOOGLE_PLACES_API_KEY is not set. Add it to your .env file.")
    return {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": config.API_KEY,
        "X-Goog-FieldMask": field_mask,
    }


def text_search_page(query: str, page_token: str | None = None) -> tuple[list[dict], str | None]:
    """Runs a single Text Search page. Returns (place stubs, next_page_token).
    Each stub has keys: id, displayName, formattedAddress.
    """
    body = {"textQuery": query, "pageSize": 20}
    if page_token:
        body["pageToken"] = page_token
        # Google requires a short delay before a pageToken becomes valid.
        time.sleep(2)

    try:
        resp = requests.post(
            config.TEXT_SEARCH_URL,
            headers=_headers(TEXT_SEARCH_FIELD_MASK),
            json=body,
            timeout=config.REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise PlacesAPIError(f"Text Search request failed: {exc}") from exc

    if resp.status_code != 200:
        raise PlacesAPIError(f"Text Search failed ({resp.status_code}): {resp.text[:300]}")

    data = resp.json()
    return data.get("places", []), data.get("nextPageToken")


def get_place_details(place_id: str) -> dict:
    """Fetch phone, website, and formatted address for a single place."""
    url = config.PLACE_DETAILS_URL.format(place_id=place_id)
    try:
        resp = requests.get(
            url, headers=_headers(DETAILS_FIELD_MASK), timeout=config.REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        logger.warning("Place Details request failed for %s: %s", place_id, exc)
        return {}

    if resp.status_code != 200:
        logger.warning(
            "Place Details failed for %s (%d): %s", place_id, resp.status_code, resp.text[:200]
        )
        return {}

    return resp.json()
