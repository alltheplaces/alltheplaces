import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BottegaVenetaSpider(scrapy.Spider):
    name = "bottega_veneta"
    item_attributes = {
        "brand": "Bottega Veneta",
        "brand_wikidata": "Q894874",
    }
    allowed_domains = ["bottegaveneta.com"]
    start_urls = ["https://www.bottegaveneta.com/de-de/storelocator"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        countries = response.xpath('//select[@id="country"]/option/@value').extract()
        for country in countries:
            url = f"https://www.bottegaveneta.com/on/demandware.store/Sites-BV-R-WEUR-Site/de_DE/Stores-FindStoresData?countryCode={country}"
            yield scrapy.Request(url=url, callback=self.store_parse)

    def store_parse(self, response):
        for store in response.json()["storesData"]["stores"]:
            item = DictParser.parse(store)
            item["website"] = store.get("detailsUrl")
            oh = OpeningHours()
            for day, hour in store.get("openingHours").items():
                if hour.get("openFromTo") == "NO DATA":
                    continue
                oh.add_range(
                    day=day,
                    open_time=hour.get("openFromTo").split(" - ")[0],
                    close_time=hour.get("openFromTo").split(" - ")[1],
                )
            item["opening_hours"] = oh.as_opening_hours()
            yield item
