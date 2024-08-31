from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class VirginActiveBWNAZASpider(Spider):
    name = "virgin_active_bw_na_za"
    item_attributes = {"brand": "Virgin Active", "brand_wikidata": "Q4013942", "extras": Categories.GYM.value}
    start_urls = ["https://cms.virginactive.co.za/wp-json/api/map_club_list"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse_location_list)

    def parse_location_list(self, response):
        for location in response.json()["club_list"]:
            yield JsonRequest(
                url=f"https://cms.virginactive.co.za/wp-json/wp/v2/clubs/?_embed&slug={location['slug']}",
                callback=self.parse_location,
            )

    def parse_location(self, response):
        location = response.json()[0]["acf"]
        properties = {
            "ref": location["gym_id"],
            "lat": location["gym_lat"],
            "lon": location["gym_long"],
            "branch": response.json()[0]["title"]["rendered"],
            "addr_full": location["gym_address"],
            "phone": location["gym_telephone"],
            "state": location["prv_name"],
            "image": location["gym_image"],
            "website": response.json()[0]["link"],
        }
        item = Feature(**properties)
        item["opening_hours"] = OpeningHours()
        for day in location["operating_hours"]:
            if day["goh_day"] in ["0", ""]:  # Public holidays = 0
                continue
            else:
                item["opening_hours"].add_range(
                    DAYS_FULL[int(day["goh_day"]) - 1],
                    day["goh_start"],
                    day["goh_end"],
                    time_format="%H:%M:%S",
                )
        yield item
