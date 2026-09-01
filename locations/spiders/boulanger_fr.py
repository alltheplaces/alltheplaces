import json
import random
from typing import Iterable

from scrapy.downloadermiddlewares.retry import get_retry_request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.pipelines.address_clean_up import merge_address_lines


class BoulangerFRSpider(SitemapSpider):
    name = "boulanger_fr"
    item_attributes = {"brand": "Boulanger", "brand_wikidata": "Q2921695"}
    sitemap_urls = ["https://www.boulanger.com/sitemap_magasins.xml"]
    # Sitemap also lists brand shop-in-shops ("espaces") and news posts ("actualites");
    # only the 4-segment region/department/city/address paths are actual store pages.
    sitemap_rules = [(r"/magasins/(?!espaces/|actualites/)[^/]+/[^/]+/[^/]+/[^/]+$", "parse")]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self):
        # Akamai-protected, so even the initial sitemap fetch needs Zyte. httpResponseHeaders is
        # required alongside httpResponseBody, or scrapy-zyte-api returns an unparseable binary Response.
        async for request in super().start():
            request.meta["zyte_api"] = {"httpResponseBody": True, "httpResponseHeaders": True}
            yield request

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {"httpResponseBody": True, "httpResponseHeaders": True}
            yield request

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        # No JSON-LD; this Yext Pages template embeds the full location profile here instead.
        raw = response.css("#js-map-config-dir-map::text").get()
        entities = json.loads(raw).get("entities") if raw else None
        if not entities:
            # Zyte occasionally hands back a genuine 200 with a truncated render; retry rather
            # than silently losing the store.
            if response.request is not None:
                if retry := get_retry_request(
                    response.request,
                    spider=self,
                    reason="no map-config JSON found",
                    priority_adjust=random.randint(-20, -1),
                ):
                    yield retry
            return
        profile = entities[0]["profile"]

        item = DictParser.parse(profile)
        item["ref"] = profile["meta"]["id"]
        item["website"] = response.url  # profile's own websiteUrl can point at a stale domain
        item.pop("phone")  # same national hotline (09 69 32 32 23) on every store, not per-branch
        item["state"] = None  # a French département name, not a real addr:state value
        item["branch"] = " ".join(item.pop("name", "").removeprefix("Boulanger").strip(" -").split())

        address = profile.get("address") or {}
        item["street_address"] = merge_address_lines([address.get("line1"), address.get("line2"), address.get("line3")])

        item["opening_hours"] = self.parse_hours(profile.get("hours", {}).get("normalHours", []))

        if profile.get("closed") is True:
            set_closed(item)

        yield item

    @staticmethod
    def parse_hours(normal_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for day in normal_hours:
            if day.get("isClosed"):
                oh.set_closed(day["day"])
                continue
            for interval in day.get("intervals", []):
                start = f"{interval['start'] // 100:02d}:{interval['start'] % 100:02d}"
                end = f"{interval['end'] // 100:02d}:{interval['end'] % 100:02d}"
                oh.add_range(day["day"], start, end)
        return oh
