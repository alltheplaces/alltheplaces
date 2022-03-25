import json
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class PetSuitesSpider(scrapy.Spider):
    name = "pet_suites"
    allowed_domains = ["yext.com"]
    start_urls = (
        "https://liveapi.yext.com/v2/accounts/me/entities?filter=%7B%20%22meta.folderId%22%3A%7B%22%24in%22%3A[249017]%7D%7D&limit=50&api_key=2bc9758495549d8bd15fe1c10fdcd617&v=20161012",
    )

    def process_hours(self, hours):
        output = OpeningHours()
        for day, data in hours.items():
            day_fmted = day[0].upper() + day[1].lower()
            hours_data = data.get("openIntervals")
            if not hours_data:
                continue
            hours_data = hours_data[0]
            output.add_range(day_fmted, hours_data["start"], hours_data["end"])

        return output.as_opening_hours()

    def parse(self, response):
        data = json.loads(response.text).get("response")
        for entity in data["entities"]:
            yield GeojsonPointItem(
                lat=entity["geocodedCoordinate"]["latitude"],
                lon=entity["geocodedCoordinate"]["longitude"],
                name=entity["name"],
                addr_full=entity["address"]["line1"],
                city=entity["address"]["city"],
                state=entity["address"]["region"],
                postcode=entity["address"]["postalCode"],
                country=entity["address"]["countryCode"],
                phone=entity["mainPhone"],
                website=entity["websiteUrl"]["url"],
                opening_hours=self.process_hours(entity["hours"]),
                ref=entity["c_googleMyBusinessCID"],
            )
