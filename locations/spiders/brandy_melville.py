import json

from geonamescache import GeonamesCache
from scrapy import Spider

from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature


class BrandyMelvilleSpider(Spider):
    name = "brandy_melville"
    item_attributes = {"brand": "Brandy Melville", "brand_wikidata": "Q25387414"}
    start_urls = ["https://locations.brandymelville.com/"]

    def parse(self, response):
        script = response.xpath("//script[contains(text(), 'locations =')]/text()").get()
        script = script[script.find("locations =") :].removeprefix("locations =").strip()
        script = script[: script.find("};") + 1]

        geonames = GeonamesCache()
        countries = geonames.get_countries_by_names()
        states = geonames.get_us_states_by_names()

        for region, subregions in json.loads(script)["data"].items():
            for subregion, locations in subregions.items():
                for location in locations:
                    item = Feature()

                    item["city"] = location[0]
                    if item["city"] in location[1]:
                        item["addr_full"] = location[1]
                    else:
                        item["street_address"] = location[1]
                    item["phone"] = item["ref"] = location[2]
                    item["lat"], item["lon"] = url_to_coords(location[3])

                    oh = OpeningHours()
                    oh.add_ranges_from_string(location[4])
                    item["opening_hours"] = oh

                    if region in countries:
                        item["country"] = countries[region]["iso"]
                    elif subregion in countries:
                        item["country"] = countries[subregion]["iso"]
                    if subregion in states:
                        item["state"] = states[subregion]["code"]

                    yield item
