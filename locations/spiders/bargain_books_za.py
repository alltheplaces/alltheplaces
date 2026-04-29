from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class BargainBooksZASpider(Spider):
    name = "bargain_books_za"
    item_attributes = {"brand": "Bargain Books", "brand_wikidata": "Q116741024"}
    start_urls = ["https://www.bargainbooks.co.za/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@id="bb-grid"]//*[@class="bb-card"]'):
            item = Feature()
            item["branch"] = item["ref"] = location.xpath(".//@data-name").get()
            item["state"] = location.xpath(".//@data-province").get()
            item["addr_full"] = location.xpath(".//@data-address").get()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            item["email"] = location.xpath('.//*[contains(@href,"mailto:")]/text()').get()
            oh = OpeningHours()
            for day_time in location.xpath('.//*[@class="bb-hours"]//tr'):
                day = day_time.xpath('.//*[@class="bb-day"]/text()').get()
                time = day_time.xpath('.//*[@class="bb-time "]//text()').get()

                if not day or day == "Public" or not time:
                    continue
                if time.strip().lower() == "closed":
                    oh.set_closed(day)
                else:
                    open_time, close_time = time.strip().replace(".", ":").replace(" ", "-").split("-")
                    oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
            item["opening_hours"] = oh
            yield item
