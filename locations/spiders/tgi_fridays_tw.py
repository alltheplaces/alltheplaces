import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.spiders.tgi_fridays_us import TgiFridaysUSSpider


class TgiFridaysTWSpider(Spider):
    name = "tgi_fridays_tw"
    item_attributes = TgiFridaysUSSpider.item_attributes
    start_urls = ["https://www.tgifridays.com.tw/en/locations"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="locations"]//*[@class="locations-item"]'):
            item = Feature()
            item["branch"] = location.xpath('.//*[@class="locations-item-title"]/text()').get()
            item["addr_full"] = location.xpath('.//*[@class="locations-item-body"]//p/text()[1]').get()
            item["phone"] = location.xpath('.//*[@class="locations-item-body"]//p/text()[2]').get()
            if m := re.search(
                r"query=(-?\d+\.\d+)%2C(-?\d+\.\d+)",
                location.xpath('.//*[@class = "locations-item-link"]/ul//a/@href').get(),
            ):
                item["lat"], item["lon"] = m.groups()
            else:
                extract_google_position(item, location)
            yield item
