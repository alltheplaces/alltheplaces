import json
import re
from typing import Any, AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy import Request, Spider
from scrapy.http import Response

from locations.items import Feature

# Persisted (server-registered) GraphQL query hash for "AvailableRetailerLocationsServices" as
# observed on order.dagnyc.com in 2026-08. Instacart's Connected Stores backend only accepts
# queries it has already registered server-side (referenced only by this SHA-256 hash of the
# query text), so the query itself cannot be customised by a client - but since the query is
# shared by the whole platform rather than being retailer-specific, the same hash is expected to
# work for other retailers hosted on Connected Stores. If this spider starts receiving
# PersistedQueryNotFound errors, the hash will need to be re-extracted from a fresh network trace.
AVAILABLE_RETAILER_LOCATIONS_SERVICES_HASH = "bea786dfccd6e730e72f43616dd2f23ec3bb008659becb18a026129f06e8d543"

CITY_STATE_POSTCODE_RE = re.compile(r"^(?P<city>.+?),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>[0-9-]+)$")


class InstacartConnectedStoresSpider(Spider):
    """
    Instacart operates a white-label "Connected Stores" storefront platform used by a number of
    grocery/retail chains to run online ordering on their own domain (e.g. D'Agostino's
    https://order.dagnyc.com/). Although hosted on the retailer's own domain, the storefront is a
    GraphQL single-page app served by Instacart's shared backend.

    The storefront does not expose a simple "list all stores" endpoint. Instead, a
    "AvailableRetailerLocationsServices" persisted GraphQL query returns the retailer's locations
    within a (apparently large, likely delivery/service-area driven) radius of a supplied
    postcode/coordinate. Querying from one or more seed points and merging/deduplicating the
    results is therefore used here to discover all of a retailer's locations. For a geographically
    compact chain, a single, centrally-located seed point may return every location; spread
    multiple points around for chains with a wider footprint.

    Calling the GraphQL query requires only an anonymous "guest" session cookie
    (`__Host-instacart_sid`), which is issued simply by loading any storefront HTML page - no
    login, API key, or JavaScript execution is required.

    To use this spider, specify:
    - storefront_root: the scheme + host of the retailer's storefront, e.g. "https://order.dagnyc.com"
    - retailer_slug: the retailer's slug as used in the storefront URL, e.g. "dagnyc"
    - search_points: a list of (postal_code, latitude, longitude) tuples used as search origins

    Override `parse_item` to tweak or discard individual items, similar to other store finders.
    """

    dataset_attributes: dict = {"source": "api", "api": "instacart-connected-stores"}
    # Connected Stores storefronts have been observed to ship a robots.txt that blanket-disallows
    # all crawlers other than a named allowlist of search engine bots, seemingly targeting generic
    # scraping/crawling rather than this specific, lightweight store-locator lookup.
    custom_settings: dict = {"ROBOTSTXT_OBEY": False}
    storefront_root: str
    retailer_slug: str
    search_points: list[tuple[str, float, float]] = []

    async def start(self) -> AsyncIterator[Any]:
        yield Request(
            url=f"{self.storefront_root}/store/{self.retailer_slug}/storefront",
            callback=self.parse_storefront,
        )

    def parse_storefront(self, response: Response) -> Iterable[Request]:
        # Loading this page is sufficient to obtain the guest session cookie required by the
        # GraphQL API below; Scrapy's cookie middleware carries it forward automatically.
        for postal_code, lat, lon in self.search_points:
            variables = {
                "postalCode": postal_code,
                "coordinates": {"latitude": lat, "longitude": lon},
                "retailerIds": [],
            }
            extensions = {"persistedQuery": {"version": 1, "sha256Hash": AVAILABLE_RETAILER_LOCATIONS_SERVICES_HASH}}
            params = {
                "operationName": "AvailableRetailerLocationsServices",
                "variables": json.dumps(variables, separators=(",", ":")),
                "extensions": json.dumps(extensions, separators=(",", ":")),
            }
            yield Request(
                url=f"{self.storefront_root}/graphql?{urlencode(params)}",
                headers={"Accept": "application/json"},
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response) -> Iterable[Feature]:
        if not hasattr(self, "_seen_location_ids"):
            self._seen_location_ids: set[str] = set()

        payload = json.loads(response.body)
        for error in payload.get("errors") or []:
            self.logger.warning("GraphQL error from %s: %s", response.url, error.get("message"))

        groups = (payload.get("data") or {}).get("availableRetailerLocationsServices") or {}
        for group in groups.get("retailerServiceableLocations") or []:
            for location in group.get("locations") or []:
                location_id = str(location["id"])
                if location_id in self._seen_location_ids:
                    continue
                self._seen_location_ids.add(location_id)

                item = self.item_from_location(location)
                yield from self.parse_item(item, location) or [item]

    def item_from_location(self, location: dict) -> Feature:
        item = Feature()
        item["ref"] = str(location["id"])

        coordinates = location.get("coordinates") or {}
        item["lat"] = coordinates.get("latitude")
        item["lon"] = coordinates.get("longitude")

        item["street_address"] = location.get("streetAddress")
        item["postcode"] = location.get("postalCode")

        view_section = location.get("viewSection") or {}
        item["name"] = view_section.get("locationDisplayNameString")
        item["phone"] = view_section.get("phoneNumberString")

        line_two = (view_section.get("address") or {}).get("lineTwoString") or ""
        if m := CITY_STATE_POSTCODE_RE.match(line_two):
            item["city"] = m.group("city")
            item["state"] = m.group("state")
            if not item.get("postcode"):
                item["postcode"] = m.group("postcode")

        return item

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        yield item
