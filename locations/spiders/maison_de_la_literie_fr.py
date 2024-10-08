from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser


class MaisonDeLaLiterieFRSpider(Spider):
    name = "maison_de_la_literie_fr"
    item_attributes = {"brand": "Maison de la Literie", "brand_wikidata": "Q80955776"}
    start_urls = ["https://www.maisondelaliterie.fr/magasins?ajax=1&p=1&n=500&all=1"]
    time_format = "%Hh%M"

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["stores"]:
            item = DictParser.parse(location)
            # Unfortunately, the opening hours are expressed in a variety of
            # formats:
            # "10h - 19h"
            # "10h-12h et 14h-19h"
            # ""
            # For now, commenting out but leaving as example for any later contributors
            # oh = OpeningHours()

            # for specific_day in location["business_hours"]:
            #     for hours in specific_day["hours"]:
            #         oh.add_range(
            #             day=DAYS_FR[specific_day["day"]],
            #             open_time=hours.split("-")[0],
            #             close_time=hours.split("-")[1],
            #             time_format=self.time_format,
            #         )

            # item["opening_hours"] = oh

            item["website"] = location["meta"]["canonical"]

            yield item
