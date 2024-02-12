from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class NeurothSpider(Spider):
    name = "neuroth"
    item_attributes = {"brand": "Neuroth", "brand_wikidata": "Q15836645"}

    def start_requests(self) -> Iterable[Request]:
        for country in ["at", "ba", "ch", "de", "hr", "si", "rs"]:
            yield JsonRequest("https://{}.neuroth.com/wp-json/neuroth/v1/appointments/stores".format(country))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = Feature()
            item["ref"] = location["code"]
            item["website"] = location["permalink"]
            item["addr_full"] = location["contact"]["formattedAddress"]
            item["street_address"] = location["contact"]["address"]
            item["postcode"] = location["contact"]["zip"]
            item["city"] = location["contact"]["city"]
            item["country"] = location["contact"]["country"]
            item["phone"] = location["contact"]["phone"]
            item["email"] = location["contact"]["email"]
            item["extras"]["fax"] = location["contact"]["fax"]
            item["lat"] = location["coordinates"]["latitude"]
            item["lon"] = location["coordinates"]["longitude"]
            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]["openingHoursEntries"]:
                item["opening_hours"].add_range(DAYS[rule["weekday"] - 1], rule["opens"], rule["closes"], "%H:%M:%S")

            yield item
