from scrapy import Spider

from locations.hours import DAYS_CZ, OpeningHours, sanitise_day
from locations.items import Feature


class RossmannCZSpider(Spider):
    name = "rossmann_cz"
    item_attributes = {"brand": "Rossmann", "brand_wikidata": "Q316004"}
    start_urls = ["https://www.rossmann.cz/prodejny"]
    custom_settings = {"COOKIES_ENABLED": False}

    def parse(self, response, **kwargs):
        for store in response.xpath('//div[@class="page-store--store-list"]/a'):
            item = Feature()
            item["ref"] = store.xpath("./@href").get()
            item["website"] = "https://www.rossmann.cz" + item["ref"]
            item["lat"] = store.xpath("./@data-latitude").get()
            item["lon"] = store.xpath("./@data-longitude").get()
            item["city"] = store.xpath("./@data-ga-city").get()
            item["addr_full"] = store.xpath("./@data-ga-address").get()
            item["name"] = store.xpath('.//div[@class="page-store--store-title"]/text()').get()

            oh = OpeningHours()
            for rule in store.xpath('.//div[@class="page-store--opening-hours"]/div[@class="page-store--opening-day"]'):
                day = rule.xpath("./strong/text()").get().replace(":", "").strip()
                day = sanitise_day(day, DAYS_CZ)

                if day is None:
                    continue

                hours = "".join(rule.xpath("./text()").getall()).strip()

                if "-" not in hours:
                    continue

                open_time, close_time = hours.split(" - ")
                oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh

            yield item
