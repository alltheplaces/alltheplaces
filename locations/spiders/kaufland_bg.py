from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class KauflandBGSpider(Spider):
    name = "kaufland_bg"
    item_attributes = {"brand": "Kaufland", "brand_wikidata": "Q685967"}
    start_urls = ["https://www.kaufland.bg/.klstorefinder.json"]

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

            item["website"] = f'https://www.kaufland.bg/moyat-kaufland/uslugi/filiali/{location["friendlyUrl"]}.html'

            yield item
