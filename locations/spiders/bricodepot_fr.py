import json
import random
from typing import Any, AsyncIterator, Iterable

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Request, Response
from scrapy.settings.default_settings import RETRY_EXCEPTIONS
from scrapy.spiders import SitemapSpider
from scrapy_camoufox.page import PageMethod

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS

# Every URL here is first served an AWS WAF challenge that resolves itself via
# JS and reloads; wait for that instead of trusting the first response.
WAIT_FOR_WAF_CHALLENGE = PageMethod(
    "wait_for_function",
    "() => !document.documentElement.outerHTML.includes('AwsWafIntegration')",
    timeout=20000,
)

CAMOUFOX_SETTINGS_FOR_AWS_WAF = DEFAULT_CAMOUFOX_SETTINGS | {
    # Default blocks everything but the document, including the WAF's own challenge.js.
    "CAMOUFOX_ABORT_REQUEST": lambda request: not request.resource_type == "document"
    and not (request.resource_type in ["script", "xhr", "fetch"] and ".awswaf.com" in request.url),
    # Concurrent challenge-solving above this starts timing out.
    "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    # WAF challenge timeouts aren't retried by default.
    "RETRY_EXCEPTIONS": RETRY_EXCEPTIONS + [PlaywrightTimeoutError],
}


class BricodepotFRSpider(SitemapSpider, CamoufoxSpider):
    name = "bricodepot_fr"
    item_attributes = {"brand": "Brico Dépôt", "brand_wikidata": "Q2889702"}
    sitemap_urls = ["https://www.bricodepot.fr/sitemaps/sitemap-magasins.xml"]
    sitemap_rules = [(r"/magasins/[^/]+$", "parse")]
    custom_settings = CAMOUFOX_SETTINGS_FOR_AWS_WAF

    async def start(self) -> AsyncIterator[Request]:
        for url in self.sitemap_urls:
            yield Request(url, callback=self._parse_sitemap, meta={"camoufox_page_methods": [WAIT_FOR_WAF_CHALLENGE]})

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            request.meta["camoufox_page_methods"] = [WAIT_FOR_WAF_CHALLENGE]
            yield request

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        store = None
        if nuxt_data := response.xpath('//script[@id="__NUXT_DATA__"]/text()').get():
            try:
                state = self.resolve_nuxt(1, json.loads(nuxt_data))
                retailer_key = next(k for k in state["data"] if k.startswith("getSingleRetailer"))
                store = state["data"][retailer_key]["items"][0]
            except (json.JSONDecodeError, KeyError, StopIteration, IndexError, TypeError):
                store = None

        if not store:
            # A settled render occasionally still lacks the payload (truncated render).
            if response.request is not None:
                if retry := get_retry_request(
                    response.request,
                    spider=self,
                    reason="no retailer data found",
                    priority_adjust=random.randint(-20, -1),
                ):
                    yield retry
            return

        item = Feature()
        item["ref"] = store["entity_id"]
        item["website"] = response.url
        item["lat"] = store["address_data"]["coordinates"]["latitude"]
        item["lon"] = store["address_data"]["coordinates"]["longitude"]
        item["street_address"] = merge_address_lines(store["address_data"]["street"])
        item["city"] = store["address_data"]["city"]
        item["postcode"] = store["address_data"]["postcode"]
        item["country"] = "FR"
        item["phone"] = store.get("contact_phone") or None
        item["email"] = store.get("contact_mail") or None

        for ld_block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            ld_data = json.loads(ld_block)
            if ld_data.get("@type") == "BreadcrumbList":
                item["branch"] = ld_data["itemListElement"][-1]["name"]
                break

        item["opening_hours"] = OpeningHours()
        for day in store["opening"]["weekly_schedule"]:
            if not day["schedule"]:
                item["opening_hours"].set_closed(day["day"])
                continue
            for period in day["schedule"]:
                item["opening_hours"].add_range(day["day"], period["start_time"], period["end_time"])

        apply_category(Categories.SHOP_DOITYOURSELF, item)
        yield item

    def resolve_nuxt(self, idx: int, payload: list, seen: frozenset | None = None) -> Any:
        # Nuxt 3's flat, index-referenced "__NUXT_DATA__" payload. See starbucks_br.py.
        if seen is None:
            seen = frozenset()

        if not isinstance(idx, int) or idx < 0 or idx >= len(payload) or idx in seen:
            return None

        seen = seen | {idx}
        node = payload[idx]

        if isinstance(node, list):
            if len(node) == 2 and node[0] in ("ShallowReactive", "Reactive", "Ref"):
                return self.resolve_nuxt(node[1], payload, seen)
            return [self.resolve_nuxt(x, payload, seen) if isinstance(x, int) else x for x in node]

        if isinstance(node, dict):
            return {k: self.resolve_nuxt(v, payload, seen) if isinstance(v, int) else v for k, v in node.items()}

        return node
