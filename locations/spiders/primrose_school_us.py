from json import loads

from scrapy import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PrimroseSchoolUSSpider(Spider):
    name = "primrose_school_us"
    item_attributes = {
        "brand": "Primrose School",
        "brand_wikidata": "Q7243677",
        "extras": Categories.KINDERGARTEN.value,
    }
    allowed_domains = ["www.primroseschools.com"]
    start_urls = ["https://www.primroseschools.com/find-a-school"]

    def parse(self, response):
        next_data = loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        for location in next_data["props"]["pageProps"]["schoolsOverview"]:
            if location["preopening"]:
                continue  # Location not yet open.

            item = DictParser.parse(location)
            if item["name"].startswith("Primrose School of "):
                item["branch"] = item["name"].removeprefix("Primrose School of ")
            item["website"] = "https://www.primroseschools.com" + location["uri"]

            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["hours"].replace("M-F", "Monday - Friday"))

            yield item
