from typing import Any, AsyncIterator

from scrapy import Selector, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DuluxDecoratorCentreGBSpider(Spider):
    name = "dulux_decorator_centre_gb"
    item_attributes = {
        "brand": "Dulux Decorator Centre",
        "brand_wikidata": "Q115593557",
    }
    allowed_domains = ["www.duluxdecoratorcentre.co.uk"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(url="https://www.duluxdecoratorcentre.co.uk/store/getstores", cookies={"BVBRANDID": ""})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["Points"]:
            item = DictParser.parse(location)
            store_details = Selector(text=location["FormattedAddress"])
            item["street_address"] = (
                store_details.xpath('//div[contains(@class, "store-street-address")]/text()').get("").strip()
            )
            item["city"] = store_details.xpath('//div[contains(@class, "store-town")]/text()').get("").strip()
            item["state"] = store_details.xpath('//div[contains(@class, "store-country")]/text()').get("").strip()
            item["postcode"] = store_details.xpath('//div[@class="store-info"]/text()').get("").strip()
            item["website"] = "https://www.duluxdecoratorcentre.co.uk/" + item["website"]
            item["branch"] = item.pop("name")
            hours_string = " ".join(store_details.xpath('//div[@class="store-days"]//text()').getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            apply_category(Categories.SHOP_PAINT, item)
            yield item
