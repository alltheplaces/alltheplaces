import re
from typing import Any, AsyncIterator, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class FiveStarFoodMartUSSpider(WpGoMapsSpider):
    name = "five_star_food_mart_us"
    item_attributes = {"brand": "FiveStar", "brand_wikidata": "Q127690151", "name": "FiveStar"}
    allowed_domains = ["fivestarfoodmart.com"]

    async def start(self) -> AsyncIterator[Request]:
        # Phone numbers are only published in the HTML store list on the locations page, not in the map markers.
        yield Request("https://fivestarfoodmart.com/locations/", callback=self.parse_phones)

    def parse_phones(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        text = " ".join(response.xpath('//*[@id="primary"]//text()').getall())
        self.phones = dict(re.findall(r"Store #\s*(\d+)[^#]*?(\(?\d{3}\)?[\s.-]*\d{3}[\s.-]*\d{4})", text))
        yield Request("https://fivestarfoodmart.com/wp-json/wpgmza/v1/features/", callback=self.parse)

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = location["title"].split("#")[-1].strip()
        item.pop("name", None)
        item["phone"] = self.phones.get(item["ref"])
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
