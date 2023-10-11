import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_PL, OpeningHours, day_range, sanitise_day
from locations.items import Feature


class PolomarketPLSpider(CrawlSpider):
    name = "polomarket_pl"
    item_attributes = {"brand": "Polomarket", "brand_wikidata": "Q11821937"}
    start_urls = ["https://www.polomarket.pl/pl/nasze-sklepy.html"]
    rules = [
        Rule(
            LinkExtractor(restrict_xpaths='//*[@id="region_map_area"]', allow="pl/nasze-sklepy.html"),
            callback="parse_store",
        )
    ]
    no_refs = True

    def parse_store(self, response):
        for store in response.xpath('//*[@class="row region"]'):
            if opening_hours := store.xpath('.//*[contains(text(),"Godziny otwarcia")]/parent::div/text()').get():
                if any(tag in opening_hours.lower() for tag in ["nieczynny", "wkrótce"]):  # opening soon or closed
                    continue
            item = Feature()
            item["city"] = store.xpath('.//*[contains(text(),"Miasto")]/parent::div/text()').get().strip()
            item["street_address"] = store.xpath('.//*[contains(text(),"Ulica")]/parent::div/text()').get().strip()
            item["lat"] = store.xpath(".//@data-lat").get()
            item["lon"] = store.xpath(".//@data-lng").get()
            item["website"] = response.url
            item["opening_hours"] = OpeningHours()
            for start_day, end_day, start_time, end_time in re.findall(
                r"(\w+)[-\s]*(\w+)?\s*(\d+[:.]\d+)\s*-\s*(\d+[:.]\d+)", opening_hours
            ):
                start_day, end_day = [day.replace("sob", "sb") if day else day for day in [start_day, end_day]]
                start_day = sanitise_day(start_day, DAYS_PL)
                end_day = sanitise_day(end_day, DAYS_PL) or start_day
                if start_day:
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day), start_time.replace(".", ":"), end_time.replace(".", ":")
                    )
            yield item
