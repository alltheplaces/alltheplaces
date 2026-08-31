from typing import Any

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class FriBikeshopDKSpider(Spider):
    name = "fri_bikeshop_dk"
    item_attributes = {"brand": "Fri BikeShop", "brand_wikidata": "Q80575447"}
    start_urls = ["https://www.fribikeshop.dk/butikker"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in DictParser.get_nested_key(
            chompjs.parse_js_object(response.xpath("//script[contains(text(), '__CONTENT_CACHE')]/text()").get()),
            "stores",
        ):
            item = DictParser.parse(location["information"])
            item["branch"] = item.pop("name").removeprefix("Fri BikeShop ")
            item["lat"] = location["information"]["address"]["latitude"]
            item["lon"] = location["information"]["address"]["longitude"]
            item["street_address"] = location["information"]["address"]["address"]
            item["ref"] = item["website"] = response.urljoin(location["information"]["weblink"])
            item["image"] = location["information"]["storeFrontImage"]

            item["opening_hours"] = self.parse_opening_hours(location["openingHours"])
            apply_category(Categories.SHOP_BICYCLE, item)

            yield item

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            oh.add_range(day, rules["{}Open".format(day)], rules["{}Close".format(day)])
        return oh
