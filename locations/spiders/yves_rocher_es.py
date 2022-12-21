import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROSWER_DEFAULT


class YvesRocherEsSpider(scrapy.Spider):
    name = "yves_rocher_es"
    item_attributes = {
        "brand": "Yves Rocher",
        "brand_wikidata": "Q1477321",
    }
    allowed_domains = ["yves-rocher.es"]
    start_urls = ["https://www.yves-rocher.es/filialen-und-kosmetik-institute/SL"]
    user_agent = BROSWER_DEFAULT

    def parse(self, response):
        urls = response.xpath('//div[@id="all-store-container"]//a/@href')
        for url in urls:
            url = f"https://{self.allowed_domains[0]}{url.get()}"
            yield scrapy.Request(url=url, callback=self.parse_store)

    def parse_store(self, response):
        data = response.xpath('//div[@class="cursor_pointer m_0"]/div[1]/@data-woosmap-component').get()
        data_json = json.loads(data)
        item = DictParser.parse(data_json)
        item["ref"] = data_json.get("storeId")
        item["lat"] = data_json.get("location")[1]
        item["lon"] = data_json.get("location")[0]
        item["website"] = response.url
        item["country"] = "DE"
        oh = OpeningHours()
        days = [
            "openingMonday",
            "openingTuesday",
            "openingWednesday",
            "openingThursday",
            "openingFriday",
            "openingSaturday",
            "openingSunday",
        ]
        if data_json.get("openingMonday"):
            print("\n", data_json.get("openingMonday"), "\n")
        for day in days:
            if data_json.get(day):
                for ilem in data_json.get(day).split("<br>"):
                    hours = ilem.strip().split(" - ")
                    oh.add_range(
                        day=day.replace("opening", ""),
                        open_time=hours[0],
                        close_time=hours[1],
                    )

        item["opening_hours"] = oh.as_opening_hours()

        yield item
