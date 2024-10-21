import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class NafNafFRSpider(Spider):
    name = "naf_naf_fr"
    item_attributes = {"brand_wikidata": "Q3334188"}
    start_urls = ["https://www.nafnaf.com/pages/nos-boutiques"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath('//*[contains(@props, "stores")]/@props').get())["stores"][1]:
            item = Feature()
            item["ref"] = location[1]["id"][1]
            item["branch"] = location[1]["name"][1].removeprefix("NAF NAF ")
            item["street_address"] = location[1]["address"][1]
            item["city"] = location[1]["city"][1]
            item["postcode"] = location[1]["zipcode"][1]
            item["country"] = location[1]["country"][1]
            item["phone"] = location[1]["phone"][1]
            item["email"] = location[1]["email"][1]

            if "location" in location[1]:
                item["lon"] = location[1]["location"][1][0][1]
                item["lat"] = location[1]["location"][1][1][1]

            yield item
