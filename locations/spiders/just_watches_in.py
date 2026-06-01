from typing import Iterable
from urllib.parse import urljoin

import scrapy
from scrapy import Spider
from scrapy.http import TextResponse

from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class JustWatchesINSpider(Spider):
    name = "just_watches_in"
    item_attributes = {"brand": "Just Watches", "brand_wikidata": "Q117822349"}
    start_urls = ["https://stores.justwatches.com/"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.xpath('//*[@class="store_outlet_01__item store-info-box"]'):
            item = Feature()
            item["city"] = location.xpath('.//*[@id="business_city"]/@value').get()
            item["state"] = location.xpath('.//*[@id="state"]/@value').get()
            item["phone"] = location.xpath('.//*[@id="phone"]/@value').get()
            item["email"] = location.xpath('.//*[@id="business_email"]/@value').get()
            item["addr_full"] = location.xpath('.//*[@id="address"]/@value').get()
            item["lat"] = location.xpath('.//*[@class="outlet-latitude"]/@value').get()
            item["lon"] = location.xpath('.//*[@class="outlet-longitude"]/@value').get()
            item["ref"] = item["website"] = location.xpath(".//h2//@href").get()
            yield item
        if page_url := response.xpath('//*[@class="next"]'):
            yield scrapy.Request(url=urljoin(response.url, page_url.xpath(".//@href").get()), callback=self.parse)
