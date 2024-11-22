import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response
from scrapy.selector import Selector

from locations.hours import CLOSED_IT, DAYS_IT, DELIMITERS_IT, OpeningHours
from locations.items import Feature


class CometITSpider(Spider):
    name = "comet_it"
    item_attributes = {"brand": "Comet", "brand_wikidata": "Q3777340"}
    start_urls = ["https://www.comet.it/negozi"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r"data: {\"stores\":(\[.+\]),\"storesCount\"", response.text).group(1)):
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["latitudine"]
            item["lon"] = location["longitudine"]
            item["website"] = location["url"]
            item["street_address"] = location["indirizzoConLocalita"]
            item["city"] = location["citta"]
            item["postcode"] = location["cap"]
            item["phone"] = location["telefono"].replace("/", "")
            item["email"] = location["email"]
            item["branch"] = location["nome"].removeprefix("Comet ")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(
                Selector(text=location["orariestesi"]).xpath("string(//*)").get(),
                days=DAYS_IT,
                closed=CLOSED_IT,
                delimiters=DELIMITERS_IT,
            )

            yield item
