from typing import Any
import json

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
#from scrapy.http import HtmlResponse
from scrapy.spiders import Spider
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from urllib.parse import urljoin
from scrapy.http import Response

class RohanGBSpider(Spider):
    name = "rohan_gb"
    item_attributes = {"brand": "Rohan", "brand_wikidata": "Q17025822"}
    start_urls = ["https://www.rohan.co.uk/shopfinder/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        content = response.xpath('//script[text()[contains(., "pageContext")]]/text()').get().replace('const pageContext = JSON.parse("','').replace('");','').replace('const jsStores = pageContext[\'jsStores\'];','').replace('\\"','"')

        data = json.loads(content)
        for location in data["jsStores"]:
            item = DictParser.parse(location["node"]["address"])
            item.pop("email") #not store specific
            item["name"] = "Rohan"
            item["branch"] = location["node"]["label"]
            item["ref"] = location["node"]["code"]
            item["street_address"] = merge_address_lines([location["node"]["address"]["address1"], location["node"]["address"]["address2"]])
            apply_category(Categories.SHOP_CLOTHES, item)
            slug=location["node"]["label"].lower().replace(" ","-")
            item["website"] = urljoin("https://www.rohan.co.uk/our-shops/", slug)

            opening_hours = OpeningHours()
            for day in DAYS_FULL:
                if location["node"]["operatingHours"][day.lower()]["open"] is True:
                    opening_hours.add_range(day, location["node"]["operatingHours"][day.lower()]["opening"], location["node"]["operatingHours"][day.lower()]["closing"])
            item["opening_hours"] = opening_hours.as_opening_hours()

            yield item
