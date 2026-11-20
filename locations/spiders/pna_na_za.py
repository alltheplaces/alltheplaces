from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class PnaNAZASpider(PlaywrightSpider):
    name = "pna_na_za"
    allowed_domains = ["pnastores.co.za"]
    start_urls = ["https://www.pna.co.za/pna-locations/"]
    item_attributes = {
        "brand": "PNA",
        "brand_wikidata": "Q126911439",
    }
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[@class="goreview-store-grid"]//*[@class="goreview-store-card"]'):
            item = Feature()
            item["branch"] = item["ref"] = (
                store.xpath('.//*[@class="goreview-store-name"]/text()').get().removeprefix("PNA ")
            )
            item["addr_full"] = store.xpath('.//*[@class="goreview-store-address"]/text()').get()
            item["city"] = store.xpath('.//*[@class="goreview-store-city"]/text()').get()
            item["phone"] = store.xpath('.//*[contains(@href,"tel:")]/text()').get()
            item["email"] = store.xpath('.//*[contains(@href,"mailto:")]/text()').get()
            item["state"] = store.xpath(".//@data-province").get()
            item["lat"] = store.xpath(".//@data-lat").get()
            item["lon"] = store.xpath(".//@data-lng").get()
            try:
                oh = OpeningHours()
                for day_time in store.xpath('.//*[@class="goreview-store-times"]//tbody//tr'):
                    day = day_time.xpath("./td[1]/text()").get()
                    open_close_time = day_time.xpath("./td[2]/text()").get()
                    if open_close_time == "Closed":
                        oh.set_closed(day)
                    else:
                        open_time, close_time = open_close_time.split("-")
                        oh.add_range(day, open_time.strip(), close_time.strip())
                item["opening_hours"] = oh
            except:
                pass
            yield item
