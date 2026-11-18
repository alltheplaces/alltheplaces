from typing import Any, Iterable
from urllib.parse import unquote

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.react_server_components import parse_rsc

# Country booking lines shared by many salons in Poland and South Korea
SHARED_PHONES = {"223915000", "+8227207573"}


class JeanLouisDavidSpider(SitemapSpider):
    name = "jean_louis_david"
    item_attributes = {"brand": "Jean Louis David", "brand_wikidata": "Q64445174"}
    sitemap_urls = ["https://www.jeanlouisdavid.com/sitemaps/sitemap-hairdressers.xml"]
    sitemap_rules = [(r"/salons/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        rsc = "".join(chunk[1] for chunk in map(chompjs.parse_js_object, scripts) if len(chunk) > 1)
        slug = unquote(response.url.rstrip("/").rsplit("/", 1)[1])
        # Each page also embeds nearby salons, so pick the one matching the URL.
        salon = next((s for s in self.iter_hairdressers(dict(parse_rsc(rsc.encode()))) if s.get("slug") == slug), None)
        if salon is None:
            self.logger.error(f"Salon data not found on {response.url}")
            return

        common = salon["common"]
        item = Feature()
        item["ref"] = str(salon["id"])
        item["branch"] = " ".join(common["brand"].split())
        if location := salon["pictureAndMap"]["map"]:
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
        item["addr_full"] = merge_address_lines(
            [line for line in (common["addressLine1"], common["addressLine2"]) if line != "None"]
        )
        item["city"] = common["city"]
        if common.get("tel") not in SHARED_PHONES:
            item["phone"] = common.get("tel")
        item["website"] = response.url

        # Days are numbered from 1 (Monday); the site shows days missing from the list as closed.
        item["opening_hours"] = OpeningHours()
        open_days = set()
        for rule in salon["toBeComputed"]["openUntil"]["hours"]:
            if not rule["closed"]:
                item["opening_hours"].add_range(DAYS[rule["day"] - 1], rule["opening"], rule["closing"])
                open_days.add(DAYS[rule["day"] - 1])
        item["opening_hours"].set_closed([day for day in DAYS if day not in open_days])

        apply_category(Categories.SHOP_HAIRDRESSER, item)
        yield item

    def iter_hairdressers(self, node: Any) -> Iterable[dict]:
        if isinstance(node, dict):
            if isinstance(node.get("hairdresser"), dict):
                yield node["hairdresser"]
            for value in node.values():
                yield from self.iter_hairdressers(value)
        elif isinstance(node, list):
            for value in node:
                yield from self.iter_hairdressers(value)
