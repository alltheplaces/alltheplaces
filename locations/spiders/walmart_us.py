from __future__ import annotations

import json
from typing import Any

from scrapy.http import Request, Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

ZYTE_API_PARAMS = {"httpResponseBody": True, "geolocation": "US"}


class WalmartUSSpider(SitemapSpider):
    name = "walmart_us"
    item_attributes = {"brand": "Walmart", "brand_wikidata": "Q483551"}
    allowed_domains = ["www.walmart.com"]
    sitemap_urls = [
        "https://www.walmart.com/sitemap_store_main_supercenter.xml.gz",
        "https://www.walmart.com/sitemap_store_main_neighborhood.xml.gz",
        "https://www.walmart.com/sitemap_store_main_discount.xml.gz",
        "https://www.walmart.com/sitemap_store_main_other.xml.gz",
    ]
    sitemap_rules = [(r"/store/\d+-", "parse")]
    custom_settings = {
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 5,
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 210,
    }

    async def start(self) -> AsyncIterator[Any]:
        for url in self.sitemap_urls:
            yield Request(url, self._parse_sitemap, meta={"zyte_api": dict(ZYTE_API_PARAMS)})

    def _parse_sitemap(self, response: Response) -> Iterable[Request]:
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = dict(ZYTE_API_PARAMS)
            yield request

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if not script_data:
            self.logger.warning(f"Could not find __NEXT_DATA__ in {response.url}")
            return

        try:
            next_data = json.loads(script_data)
        except json.JSONDecodeError:
            self.logger.warning(f"Could not parse __NEXT_DATA__ JSON from {response.url}")
            return

        # Navigate to node detail
        node = (
            next_data.get("props", {})
            .get("pageProps", {})
            .get("initialData", {})
            .get("initialDataNodeDetail", {})
            .get("data", {})
            .get("nodeDetail", {})
        )

        if not node:
            self.logger.warning(f"Could not extract nodeDetail from {response.url}")
            return

        address = node.get("address", {})

        item = Feature(
            ref=node.get("id"),
            lat=node.get("geoPoint", {}).get("latitude"),
            lon=node.get("geoPoint", {}).get("longitude"),
            street_address=address.get("addressLineOne"),
            city=address.get("city"),
            state=address.get("state"),
            postcode=address.get("postalCode"),
            country=address.get("country", "US"),
            phone=node.get("phone"),
            website=response.url,
        )

        # Set branch name (location-specific name like "Willmar Supercenter")
        item["branch"] = node.get("displayName", "").split(",")[0].strip()

        # Parse store type and apply category
        store_type = node.get("name", "")
        if store_type == "Walmart Supercenter":
            item["name"] = "Walmart Supercenter"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif "Neighborhood Market" in store_type:
            item["name"] = "Walmart Neighborhood Market"
            item["brand"] = "Walmart Neighborhood Market"
            item["brand_wikidata"] = "Q7963529"
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            item["name"] = "Walmart"
            apply_category(Categories.SHOP_DEPARTMENT_STORE, item)

        # Parse opening hours
        hours = node.get("operationalHours", [])
        if hours:
            item["opening_hours"] = self.parse_hours(hours)

        yield item

    def parse_hours(self, hours: list) -> OpeningHours | None:
        if not hours:
            return None

        try:
            oh = OpeningHours()
            for rule in hours:
                day = rule.get("day")
                if rule.get("closed") is True:
                    oh.set_closed(day)
                else:
                    oh.add_range(day, rule.get("start"), rule.get("end"))
            return oh
        except Exception as e:
            self.logger.error(f"Failed to parse hours: {hours}, {e}")
            return None
