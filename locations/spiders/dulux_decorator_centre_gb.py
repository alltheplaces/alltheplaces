from scrapy import Selector, Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DuluxDecoratorCentreGBSpider(Spider):
    name = "dulux_decorator_centre_gb"
    item_attributes = {
        "brand": "Dulux Decorator Centre",
        "brand_wikidata": "Q115593557",
        "extras": Categories.SHOP_PAINT.value,
    }
    allowed_domains = ["www.duluxdecoratorcentre.co.uk"]
    start_urls = ["https://www.duluxdecoratorcentre.co.uk/store/getstores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
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
            hours_string = " ".join(store_details.xpath('//div[@class="store-days"]//text()').getall())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
