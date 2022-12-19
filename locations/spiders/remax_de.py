import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class RemaxDeSpider(scrapy.Spider):
    name = "remax_de"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    allowed_domains = ["remax.com/"]

    def start_requests(self):
        url = "https://wp.ooremax.com/wp-json/eapi/v1/agencies?per_page=24&page={}"
        for i in range(11):
            yield scrapy.Request(url=url.format(i), callback=self.parse)

    def parse(self, response):
        for data in response.json():
            item = DictParser.parse(data.get("acf"))
            item["ref"] = data.get("id")
            openHours = (
                data.get("yoast_head_json", {}).get("schema", {}).get("@graph", {})[3].get("openingHoursSpecification")
            )
            oh = OpeningHours()
            for days in openHours:
                for day in days.get("dayOfWeek"):
                    oh.add_range(
                        day=day,
                        open_time=days.get("opens"),
                        close_time=days.get("closes"),
                    )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
