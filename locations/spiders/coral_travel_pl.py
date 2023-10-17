import json
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class CoralTravelPLSpider(Spider):
    name = "coral_travel_pl"
    start_urls = ["https://www.coraltravel.pl/rwd_map_container/index/"]
    item_attributes = {"brand": "Coral Travel", "brand_wikidata": "Q58011479"}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = response.xpath("//script/text()[contains(., 'initMap')]").get()
        content = script.split("var markers = ")[1].split("];")[0].replace("'", '"').strip().removesuffix(",") + "]"
        content = content.replace('["", ,, "autorized"],', "")
        data = json.loads(content)
        for office in data:
            name, lat, lon, office_type = office
            # TODO: more data in infoWindowContent (HTML in JavaScript)
            yield Feature(
                {
                    "ref": None,
                    "lat": lat,
                    "lon": lon,
                }
            )
