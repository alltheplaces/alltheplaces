import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class BottegaVenetaSpider(PlaywrightSpider):
    name = "bottega_veneta"
    item_attributes = {"brand": "Bottega Veneta", "brand_wikidata": "Q894874"}
    allowed_domains = ["bottegaveneta.com"]
    start_urls = ["https://www.bottegaveneta.com/de-de/storelocator"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response):
        countries = response.xpath('//select[@id="country"]/option/@value').extract()
        for country in countries:
            url = f"https://www.bottegaveneta.com/on/demandware.store/Sites-BV-R-WEUR-Site/de_DE/Stores-FindStoresData?countryCode={country}"
            yield scrapy.Request(url=url, callback=self.store_parse)

    def store_parse(self, response):
        for store in json.loads(response.xpath("//pre//text()").get())["storesData"]["stores"]:
            item = DictParser.parse(store)
            item["website"] = store.get("detailsUrl")
            item["branch"] = item.pop("name")
            oh = OpeningHours()
            for day, hour in store.get("openingHours").items():
                if hour.get("openFromTo") == "NO DATA":
                    continue
                oh.add_range(day, hour.get("openFromTo").split(" - ")[0], hour.get("openFromTo").split(" - ")[1])
            item["opening_hours"] = oh
            yield item
