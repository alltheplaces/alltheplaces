import json
import re
from typing import Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser

OVERSEAS = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class FranceLiterieFRSpider(SitemapSpider):
    name = "france_literie_fr"
    item_attributes = {"brand": "France Literie", "brand_wikidata": "Q100249535"}
    sitemap_urls = ["https://www.france-literie.fr/shop-sitemap.xml"]
    sitemap_rules = [(r"/magasins/[^/]+/$", "parse")]

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        # The Yoast graph is a single object, not a list, so it is read here
        # instead of through StructuredDataSpider.
        for script in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            ld = json.loads(script)
            graph = ld.get("@graph", ld)
            if isinstance(graph, dict) and graph.get("@type") == "LocalBusiness":
                break
        else:
            return

        hours = graph.pop("openingHours", None)
        item = LinkedDataParser.parse_ld(graph)
        item["ref"] = item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("France Literie ").split(" – ")[0]
        item["name"] = "France Literie"
        item["opening_hours"] = self.parse_hours(hours or [])
        # Overseas stores are listed with addressCountry FR
        if country := OVERSEAS.get((item.get("postcode") or "")[:3]):
            item["country"] = country

        apply_category(Categories.SHOP_BED, item)

        yield item

    @staticmethod
    def parse_hours(lines: list[str]) -> OpeningHours | None:
        oh = OpeningHours()
        for line in lines:
            day_name, _, rest = line.strip().partition(" ")
            day = DAYS_FR.get(day_name.title())
            if day is None:
                return None
            if not rest.strip():
                continue
            if "ferm" in rest.lower():
                oh.set_closed(day)
                continue
            times = re.findall(r"(\d{1,2})h(\d{2})?\s*(?:à|-|–)\s*(\d{1,2})h(\d{2})?", rest.lower())
            if not times:
                return None
            for h1, m1, h2, m2 in times:
                oh.add_range(day, f"{h1}:{m1 or '00'}", f"{h2}:{m2 or '00'}")
        return oh
