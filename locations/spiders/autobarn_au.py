import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class AutobarnAUSpider(scrapy.Spider):
    name = "autobarn_au"
    item_attributes = {"brand": "Autobarn", "brand_wikidata": "Q105831666"}
    allowed_domains = ["autobarn.com.au"]
    start_urls = ["https://autobarn.com.au/ab/store-finder?q=Australia&ajax=true&page=0"]

    def parse(self, response):
        stores = response.json()["data"]
        for store in stores:
            item = DictParser.parse(store)
            item["ref"] = item.pop("name")
            item["name"] = store["displayName"]
            item["city"] = item["city"].title()
            item["website"] = "https://autobarn.com.au/ab" + item["website"].split("?", 1)[0]
            if "openings" in store:
                oh = OpeningHours()
                for day_name, day_hours in store["openings"].items():
                    day_hours = day_hours.upper()
                    if day_hours == "CLOSED":
                        continue
                    day_name = day_name.replace(".", "")
                    oh.add_range(DAYS_EN[day_name], day_hours.split(" - ")[0], day_hours.split(" - ")[1], "%I:%M %p")
                item["opening_hours"] = oh.as_opening_hours()
            yield item

        if "crawl_complete" in response.meta and response.meta["crawl_complete"] is True:
            return
        total_stores = int(response.json()["total"])
        number_of_pages, trailing_count = divmod(total_stores, 5)
        if trailing_count > 0:
            number_of_pages = number_of_pages + 1
        for page_number in range(1, number_of_pages, 1):
            yield scrapy.Request(
                url=f"https://autobarn.com.au/ab/store-finder?q=Australia&ajax=true&page={page_number}",
                callback=self.parse,
                meta={"crawl_complete": True},
            )
