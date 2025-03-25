from typing import Any

import chompjs
import scrapy
from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class MitsubishiMASpider(scrapy.Spider):
    name = "mitsubishi_ma"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["http://www.mitsubishi-motors.ma/succursale"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="item-list"]//li'):
            item = Feature()
            item["branch"] = location.xpath(".//h3/text()").get()
            item["street_address"] = location.xpath('.//*[@class="adrs"]//p/text()[1]').get().strip()
            item["city"] = location.xpath('.//*[@class="adrs"]//p/text()[2]').get().strip()
            item["phone"] = location.xpath('.//*[contains(@href,"tel:")]/text()').get()
            extract_google_position(item, location)
            apply_category(Categories.SHOP_CAR, item)
            yield item
