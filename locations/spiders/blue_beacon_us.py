import json
import re
from typing import Any

from scrapy import Selector
from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class BlueBeaconUSSpider(Spider):
    name = "blue_beacon_us"
    item_attributes = {"brand": "Blue Beacon", "brand_wikidata": "Q127435120"}
    start_urls = ["https://bluebeacon.com/locations/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for feature in json.loads(
            re.search(
                r"SABAI\.GoogleMaps\.map\(\n\s+'#sabai-content \.sabai-directory-map',\n\s+(\[{.+}]),", response.text
            ).group(1)
        ):
            item = DictParser.parse(feature)
            html_listing = Selector(text=feature["content"])
            item["branch"] = html_listing.xpath('//div[@class="sabai-directory-title"]/a/@title').get()
            item["website"] = html_listing.xpath('//div[@class="sabai-directory-title"]/a/@href').get()
            item["ref"] = item["website"]
            item["addr_full"] = clean_address(
                html_listing.xpath('//div[@class="sabai-directory-location"]//text()').getall()
            )
            apply_category(Categories.CAR_WASH, item)
            apply_yes_no(Extras.TRUCK_WASH, item, True)
            yield item
