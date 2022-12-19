import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROSWER_DEFAULT


class OyshoGbSpider(scrapy.Spider):
    name = "oysho_gb"
    item_attributes = {
        "brand": "Oysho",
        "brand_wikidata": "Q3327046",
    }
    allowed_domains = ["oysho.com"]
    user_agent = BROSWER_DEFAULT

    def start_requests(self):
        url = "https://www.oysho.com/itxrest/2/bam/store/64009606/physical-store?languageId=-1&appId=1&latitude={}&longitude={}&countryCode=FR&radioMax=5000"
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", "UK"):
            yield scrapy.Request(url=url.format(lat, lon))

    def parse(self, response):
        for data in response.json().get("closerStores"):
            item = DictParser.parse(data)

            item["phone"] = data.get("phones")[0]
            item["street_address"] = data.get("addressLines")[0]

            oh = OpeningHours()
            for openHour in data.get("openingHours", {}).get("schedule"):
                for day in openHour.get("weekdays"):
                    oh.add_range(
                        day=DAYS[day - 1],
                        open_time=openHour.get("timeStripList")[0].get("initHour"),
                        close_time=openHour.get("timeStripList")[0].get("endHour"),
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
