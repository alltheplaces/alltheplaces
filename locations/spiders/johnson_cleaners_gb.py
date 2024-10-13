from typing import Any, Iterable
from urllib.parse import urljoin

from scrapy import FormRequest, Request, Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.asda_gb import AsdaGBSpider
from locations.spiders.sainsburys import SainsburysSpider
from locations.spiders.tesco_gb import TescoGBSpider, set_located_in
from locations.spiders.waitrose import WaitroseSpider


class JohnsonCleanersGBSpider(Spider):
    name = "johnson_cleaners_gb"
    item_attributes = {"brand": "Johnson Cleaners", "brand_wikidata": "Q6268527"}

    located_in_map = {
        "0": None,
        "asda": AsdaGBSpider.item_attributes,
        "sainsburys": SainsburysSpider.SAINSBURYS,
        "tesco": TescoGBSpider.TESCO_EXTRA,
        "waitrose": WaitroseSpider.WAITROSE,
    }

    def make_request(self, lat: float, lon: float) -> FormRequest:
        return FormRequest(
            url="https://www.johnsoncleaners.com/storefinder/locator/get/{}/{}/1".format(lat, lon),
            formdata={"search2": "+", "type": "5,1", "address": "", "start": "2000"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

    def start_requests(self) -> Iterable[Request]:
        for lat, lon in [
            (57.4804152, -4.6801978),
            (55.4788659, -2.3730688),
            (54.6865469, -6.2182837),
            (52.2278129, -0.5053931),
            (50.6668862, -4.1089087),
        ]:
            yield self.make_request(lat, lon)

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = urljoin("https://www.johnsoncleaners.com/branch/", location["url"])
            item["street_address"] = location["street1"]

            if supermarket := location.get("supermarket"):
                if supermarket in self.located_in_map:
                    if self.located_in_map[supermarket]:
                        set_located_in(self.located_in_map[supermarket], item)
                else:
                    self.crawler.stats.inc_value("{}/unknown_supermarket/{}".format(self.name, supermarket))

            item["opening_hours"] = OpeningHours()
            for day in range(1, 7):
                rule = location["opening_{}".format(day)]
                if rule == "Closed":
                    item["opening_hours"].set_closed(DAYS[day - 1])
                else:
                    item["opening_hours"].add_range(DAYS[day - 1], *rule.split(" - "))

            yield item
