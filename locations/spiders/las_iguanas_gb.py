from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class LasIguanasGBSpider(FrankieAndBennysGBSpider):
    name = "las_iguanas_gb"
    item_attributes = {"brand": "Las Iguanas", "brand_wikidata": "Q19875012"}
    sitemap_urls = ["https://www.iguanas.co.uk/sitemap.xml"]

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = (
            response.xpath('//h1/div[contains(@class,"display")]/text()').get()
            or response.xpath("//h1/span/text()").get()
        )
        item["addr_full"] = (
            response.xpath('//*[@class="contact-info"]//*[@class="my-4"]//p').xpath("normalize-space()").get()
        )
        yield item
