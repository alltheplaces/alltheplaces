from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.hours import DAYS_CN, OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class DominosPizzaTWSpider(Spider):
    name = "dominos_pizza_tw"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    start_urls = ["https://www.dominos.com.tw/Ajax/GetStoreMapMakers"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            yield Request(
                f"https://www.dominos.com.tw/Stores/GetStoreDialog?storeid={location['id']}",
                cb_kwargs={"id": location["id"], "lat": location["latitude"], "lng": location["longitude"]},
                callback=self.parse_store,
            )

    def parse_store(self, response: Response, id: str, lat: float, lng: float) -> Any:
        item = Feature()
        item["ref"] = id
        item["lat"] = lat
        item["lon"] = lng
        item["name"] = response.xpath('//p[@class="stroe-name"]/text()').get()
        item["addr_full"] = response.xpath('//div[@class="d-flex"]/div/span/text()').get()
        item["phone"] = response.xpath('//div[@class="d-flex"]/div/a/span/text()').get()
        self.parse_hours(item, response.xpath('//div[@class="collapse store-opening-time"]'))
        yield item

    def parse_hours(self, item, hours):
        try:
            oh = OpeningHours()
            for day, hour in zip(
                hours.xpath(".//span[boolean(@class)]/text()").getall(),
                hours.xpath(".//span[not(boolean(@class))]/text()").getall(),
            ):
                oh.add_range(DAYS_CN[day], *hour.replace(" ", "").split("~"), "%H:%M")
            item["opening_hours"] = oh
        except:
            self.crawler.stats.inc_value("failed_parse_hours")
