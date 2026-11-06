import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

OVERSEAS_COUNTRIES = {"971": "GP", "972": "MQ", "973": "GF", "974": "RE", "976": "YT"}


class CultureVeloFRSpider(SitemapSpider, StructuredDataSpider):
    name = "culture_velo_fr"
    item_attributes = {"brand": "Culture Vélo", "brand_wikidata": "Q130215001", "name": "Culture Vélo"}
    allowed_domains = ["www.culturevelo.com"]
    sitemap_urls = ["https://www.culturevelo.com/10-services-magasins-sitemap.xml"]
    sitemap_rules = [(r"/-([^/]+)-$", "parse_sd")]
    wanted_types = ["BikeStore"]
    drop_attributes = {"image"}

    def sitemap_filter(self, entries):
        for entry in entries:
            entry["loc"] = entry["loc"].split("/services/")[0]
            yield entry

    def pre_process_data(self, ld_data: dict, **kwargs) -> None:
        ld_data.pop("brand", None)
        ld_data.pop("@id", None)
        rules = []
        for rule in ld_data.get("openingHoursSpecification", []):
            times = re.findall(r"\d{1,2}(?::\d{2})?", f"{rule['opens']} {rule['closes']}")
            times = [t if ":" in t else f"{t}:00" for t in times]
            rules += [
                {"dayOfWeek": rule["dayOfWeek"], "opens": o, "closes": c} for o, c in zip(times[::2], times[1::2])
            ]
        ld_data["openingHoursSpecification"] = rules

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Culture Vélo").strip()
        item["email"] = response.xpath("//script/text()").re_first(r'"mail":"([^"]+)"')
        if country := OVERSEAS_COUNTRIES.get(item["postcode"][:3]):
            item["country"] = country
        apply_category(Categories.SHOP_BICYCLE, item)
        yield item
