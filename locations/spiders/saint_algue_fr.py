import re
from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class SaintAlgueFRSpider(SitemapSpider):
    name = "saint_algue_fr"
    item_attributes = {"brand": "Saint Algue", "brand_wikidata": "Q62973210"}
    sitemap_urls = ["https://www.saint-algue.com/sitemaps/sitemap-hairdressers.xml"]
    sitemap_rules = [(r"/salons/[-\w]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        location_data = response.xpath('//script[contains(text(),"page-Salon")]/text()').get("").replace('\\"', '"')
        if match := re.search(r"hairdresser\":({.+?}),\"pictureAndMap", location_data):
            location = chompjs.parse_js_object(match.group(1) + "}")
            location.update(location.pop("common", {}))
            location.update(location.get("toBeComputed", {}).pop("distanceFromUser", {}))
            location["address"] = merge_address_lines(
                [location.pop("addressLine1", ""), location.pop("addressLine2", "")]
            )
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").title().removeprefix("Saint Algue - ")
            item["website"] = response.url
            item["opening_hours"] = OpeningHours()
            hours = location.get("toBeComputed", {}).get("openUntil", {}).get("hours") or []
            for rule in hours:
                item["opening_hours"].add_range(DAYS[rule["day"] - 1], rule["opening"], rule["closing"])
            apply_category(Categories.SHOP_HAIRDRESSER, item)
            yield item
