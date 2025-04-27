import json
from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class RomanOriginalsGBSpider(Spider):
    name = "roman_originals_gb"
    item_attributes = {"brand": "Roman Originals", "brand_wikidata": "Q94579553"}
    start_urls = ["https://www.roman.co.uk/store-locator"]

    def find_between(self, text, first, last):
        start = text.index(first) + len(first)
        end = text.index(last, start)
        return text[start:end]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = self.find_between(response.text, '"@graph":', "}</script>")
        json_data = json.loads(data)
        for stores in json_data:
            if stores["@type"] == "Store":
                for store in stores["department"]:
                    item = DictParser.parse(store)
                    item["ref"] = store["name"]
                    item["branch"] = item["ref"]
                    item["street_address"] = merge_address_lines(
                        [store["address"]["streetAddress"], store["address"]["addressLocality"]]
                    )
                    item["website"] = urljoin("https://www.roman.co.uk", store["url"])
                    item["lat"] = store["location"]["geo"]["latitude"]
                    item["lon"] = store["location"]["geo"]["longitude"]
                    
                    #                    item["opening_hours"] = OpeningHours()
                    # Opening hours are wrong
                    #                    for day in store["openingHoursSpecification"][0]["dayOfWeek"]:
                    #                        item["opening_hours"].add_range(day, store["openingHoursSpecification"][0]["opens"], store["openingHoursSpecification"][0]["closes"])

                    yield item
