from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class DavidLloydGBSpider(Spider):
    name = "david_lloyd_gb"
    item_attributes = {"brand": "David Lloyd Clubs", "brand_wikidata": "Q5236716"}
    start_urls = ["https://mobile-app-back.davidlloyd.co.uk/clubs/locations"]

    def parse(self, response, **kwargs):
        for ref, coords in response.json()["clubLocations"].items():
            yield JsonRequest(
                url=f"https://mobile-app-back.davidlloyd.co.uk/clubs/{ref}",
                callback=self.parse_location,
                cb_kwargs={"coords": coords},
            )

    def parse_location(self, response, coords, **kwargs):
        location = response.json()
        if location["brand"] != "david-lloyd":
            return
        item = Feature()
        item["lat"] = coords["latitude"]
        item["lon"] = coords["longitude"]
        item["ref"] = location["siteId"]
        item["branch"] = location["clubName"]
        item["email"] = location["receptionEmailAddress"]
        item["phone"] = location["telephone"]
        item["country"] = location["country"]

        item["opening_hours"] = OpeningHours()
        for day, times in location["clubOpeningTimes"]["weeklyOpeningTimes"].items():
            for time in times:
                item["opening_hours"].add_range(day, time["from"], time["to"])

        yield item


#
