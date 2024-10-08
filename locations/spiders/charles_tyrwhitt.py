import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class CharlesTyrwhittSpider(scrapy.Spider):
    name = "charles_tyrwhitt"
    item_attributes = {
        "brand": "Charles Tyrwhitt",
        "brand_wikidata": "Q924963",
    }
    allowed_domains = ["www.charlestyrwhitt.com"]
    start_urls = ["https://www.charlestyrwhitt.com/uk/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        mapdata = response.xpath('//div[@id="map-data"]//text()').get()
        data = json.loads(mapdata)
        for location in data:
            item = DictParser.parse(location)
            apply_category(Categories.SHOP_CLOTHES, item)
            item["branch"] = item["name"]
            item["name"] = "Charles Tyrwhitt"
            location["address1"] = location["address1"].replace("Charles Tyrwhitt", "")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            oh = OpeningHours()
            for line in (location["storeHours"] or "").split("<br />"):
                oh.add_ranges_from_string(line)
            item["opening_hours"] = oh
            item["website"] = f'https://www.charlestyrwhitt.com{location["detailsURL"]}'

            yield item
