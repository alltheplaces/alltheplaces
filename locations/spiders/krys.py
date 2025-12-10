from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_FR, OpeningHours, sanitise_day

PAGE_SIZE = 500


class KrysSpider(Spider):
    name = "krys"
    item_attributes = {"brand": "Krys", "brand_wikidata": "Q3119538"}
    start_urls = ["https://www.krys.com/recherche-magasin"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def make_request(self, offset) -> JsonRequest:
        return JsonRequest(
            url="https://www.krys.com/ajax.V1.php/fr_FR/Rbs/Storelocator/Store/",
            headers={"X-HTTP-Method-Override": "GET"},
            data={
                "websiteId": 100196,
                "sectionId": 100196,
                "pageId": 101077,
                "data": {
                    "currentStoreId": 0,
                    "distanceUnit": "kilometers",
                    "distance": "20000kilometers",
                    "coordinates": {"latitude": 0, "longitude": 0},
                },
                "dataSets": "coordinates,address,card,services,hours",
                "URLFormats": "canonical",
                "visualFormats": "original",
                "pagination": f"{offset},{PAGE_SIZE}",
                "referer": "https://www.krys.com/recherche-magasin",
            },
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(0)

    def parse(self, response, **kwargs):
        pagination = response.json()["pagination"]
        if pagination["offset"] + pagination["limit"] < pagination["count"]:
            yield self.make_request(pagination["offset"] + PAGE_SIZE)

        for location in response.json()["items"]:
            if location["longClosed"]:
                continue

            location.update(location.pop("common"))
            location.update(location.pop("address"))
            location.update(location.pop("fields"))
            location.update(location.pop("card"))
            item = DictParser.parse(location)
            item["branch"] = (
                item.pop("name").replace("Krys", "").replace("Audition", "").lstrip("- ").rstrip(" -").lstrip().rstrip()
            )
            item["website"] = location["URL"]["canonical"]
            item["image"] = ";".join([i["original"] for i in location["visuals"]])
            item["street_address"] = ", ".join(filter(None, [location["street"], location["street_extend"]]))
            item["addr_full"] = ", ".join(location["lines"])

            item["opening_hours"] = OpeningHours()
            for rule in location["hours"]["openingHours"]:
                if day := sanitise_day(rule["title"][:2], DAYS_FR):
                    times = [
                        rule.get(period) for period in ["amBegin", "amEnd", "pmBegin", "pmEnd"] if rule.get(period)
                    ]
                    if len(times) % 2 == 0:
                        for start, end in zip(times[::2], times[1::2]):
                            item["opening_hours"].add_range(day, start, end)
            yield item
