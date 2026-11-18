import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_FR, DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AutodistributionFRSpider(SitemapSpider, StructuredDataSpider):
    name = "autodistribution_fr"
    item_attributes = {
        "brand": "Autodistribution",
        "brand_wikidata": "Q139825482",
    }
    sitemap_urls = ["https://www.autodistribution.fr/sitemap.xml"]
    sitemap_rules = [(r"autodistribution\.fr/magasins-pieces-auto/[^/]+$", "parse_sd")]
    wanted_types = ["AutomotiveBusiness"]
    search_for_email = False
    search_for_phone = False

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Feature]:
        text = response.text.replace('\\"', '"')
        if match := re.search(r'"id":(\d+),"latitude":(-?[\d.]+),"longitude":(-?[\d.]+)', text):
            item["ref"], item["lat"], item["lon"] = match.groups()

        item.pop("name", None)

        if schedule := response.xpath('//svg[contains(@class, "remixicon")]/following-sibling::p/text()').get():
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                schedule.replace("et", " ").split("Atelier")[0], DAYS_FR, delimiters=DELIMITERS_FR, closed=CLOSED_FR
            )

        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
