from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PlayaBowlsUSSpider(Spider):
    name = "playa_bowls_us"
    item_attributes = {"brand": "Playa Bowls", "brand_wikidata": "Q114618507"}
    allowed_domains = ["www.playabowls.com"]
    start_urls = ["https://services.playabowls.com/api/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = location["link"]
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["timing"].replace("Open Everyday ", "Mo-Su"))
            yield item
