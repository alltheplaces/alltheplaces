import json

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_3_LETTERS_FROM_SUNDAY, OpeningHours


class YogurtlandSpider(Spider):
    name = "yogurtland"
    item_attributes = {"brand": "Yogurtland", "brand_wikidata": "Q8054428"}

    def _make_request(self, page=1):
        return Request(
            f"https://www.yogurtland.com/api/1.1/locations/search.json?page={page}",
            headers={"X-Api-Key": "QeKEiECfiACR"},
        )

    def start_requests(self):
        yield self._make_request()

    def parse(self, response):
        for location in response.json()["locations"]:
            item = DictParser.parse(location["Location"])
            item["branch"] = item.pop("name")
            item["street_address"] = item.pop("addr_full")
            item["website"] = f"https://www.yogurtland.com/locations/view/{location['Location']['id']}"
            item["image"] = location["Image"]["uri"]

            hours = json.loads(location["Location"]["hours_json"])
            oh = OpeningHours()
            for day, times in zip(DAYS_3_LETTERS_FROM_SUNDAY, hours):
                if times["isActive"]:
                    try:
                        oh.add_range(day, times["timeFrom"], times["timeTill"])
                    except ValueError as e:
                        self.logger.exception(e)
                        oh = None
                        break
            item["opening_hours"] = oh

            yield item

        if response.json()["has_more"]:
            yield self._make_request(int(response.json()["page"]) + 1)
