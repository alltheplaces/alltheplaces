import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class KauflandSpider(scrapy.Spider):
    name = "kaufland"
    item_attributes = {"brand": "Kaufland", "brand_wikidata": "Q685967"}
    website_formats = {
        "https://filiale.kaufland.de/.klstorefinder.json": "https://filiale.kaufland.de/service/filiale/frankfurt-oder-spitzkrug-multi-center-{}.html",
        "https://www.kaufland.bg/.klstorefinder.json": "https://www.kaufland.bg/moyat-kaufland/uslugi/filiali/{}.html",
    }
    start_urls = website_formats.keys()

    def parse(self, response, **kwargs):
        for location in response.json():
            item = GeojsonPointItem()

            item["ref"] = location["n"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["name"] = location["cn"]
            item["phone"] = location["p"].replace("/", "")
            item["postcode"] = location["pc"]
            item["street_address"] = location["sn"]

            oh = OpeningHours()
            for rule in location["wod"]:
                day, start_time, end_time = rule.split("|")
                oh.add_range(day, start_time, end_time)
            item["opening_hours"] = oh.as_opening_hours()

            item["website"] = self.website_formats.get(response.url).format(location["friendlyUrl"])

            yield item
