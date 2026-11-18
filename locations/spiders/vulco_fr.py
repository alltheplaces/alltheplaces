from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonResponse

from locations.dict_parser import DictParser
from locations.geo import country_iseadgg_centroids
from locations.hours import OpeningHours
from locations.items import Feature


class VulcoFRSpider(Spider):
    name = "vulco_fr"
    item_attributes = {"brand": "Vulco", "brand_wikidata": "Q80184403"}
    api_key = "6UVdMLOJT71jdPeeEDyZYnbCVBbVZrh8IjbOUcbj"

    async def start(self) -> Iterable[Request]:
        # The API accepts a search radius of at most 100 km. The FR centroids include the overseas departments.
        for lat, lon in country_iseadgg_centroids("FR", 94):
            yield Request(
                url="https://api-gaas.goodyear.eu/dealer/v1/find-by-location?distance=100000&pageSize=1000&channel=VULCO&shop=vulco-fr&country=FR&format=RETAIL&latitude={}&longitude={}".format(
                    lat, lon
                ),
                headers={"x-api-key": self.api_key},
            )

    def parse(self, response: JsonResponse, **kwargs: Any) -> Iterable[Feature]:
        for result in response.json()["dealers"]:
            dealer = result["dealer"]
            dealer.update(dealer.pop("address"))
            dealer.update(dealer.pop("geoPoint"))
            item = DictParser.parse(dealer)
            item["ref"] = dealer["agencyId"]
            item["street_address"] = item.pop("street", None)
            item.pop("housenumber", None)
            item["city"] = (dealer.get("city") or "").title() or None

            dealer_name = dealer["name"]
            item["name"] = "Vulco"
            if dealer_name.upper().startswith("VULCO "):
                item["branch"] = dealer_name[6:].strip("- ").title()

            item["website"] = "https://www.vulco.fr/all-dealers/{}/{}-{}.html".format(
                dealer["cityWebsafe"], dealer["nameWebsafe"], dealer["agencyId"]
            )

            item["opening_hours"] = OpeningHours()
            for day in dealer.get("openingHours") or []:
                for period in ("am", "pm"):
                    if times := day.get(period):
                        item["opening_hours"].add_range(day["dayOfWeek"], times["openingTime"], times["closingTime"])

            yield item
