from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.items import Feature


class AwaySpider(Spider):
    name = "away"
    item_attributes = {"brand": "Away", "brand_wikidata": "Q48743138"}
    start_urls = ["https://www.awaytravel.com/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath('//*[contains(@class,"flex md:justify-end w-full gap-md md:gap-lg")]'):
            item = Feature()
            item["addr_full"] = store.xpath(".//address/span/text()").get()
            item["branch"] = store.xpath('.//*[@class="flex flex-col gap-sm"]/p/a[1]/text()').get()
            item["phone"] = store.xpath('.//*[@class="flex flex-col gap-sm"]/p/a[2]/text()').get()
            item["ref"] = item["website"] = urljoin(
                "https://www.awaytravel.com", store.xpath('.//*[@class="flex flex-col gap-sm"]/p/a/@href').get()
            )
            item["lat"] = response.xpath(f"""//*[contains(@value,"{(item["branch"])}")]/@data-latitude""").get()
            item["lon"] = response.xpath(f"""//*[contains(@value,"{item["branch"]}")]/@data-longitude""").get()
            yield item
