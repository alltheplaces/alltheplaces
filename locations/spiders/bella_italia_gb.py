from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.spiders.frankie_and_bennys_gb import FrankieAndBennysGBSpider


class BellaItaliaGBSpider(FrankieAndBennysGBSpider):
    name = "bella_italia_gb"
    item_attributes = {"brand": "Bella Italia", "brand_wikidata": "Q4883362"}
    sitemap_urls = ["https://www.bellaitalia.co.uk/sitemap.xml"]

    def parse_item(self, item: Feature, response: Response, **kwargs) -> Iterable[Feature]:
        item["branch"] = (
            response.xpath('//h1/div[contains(@class,"display")]/text()').get()
            or response.xpath("//h1/span/text()").get()
        )
        item["addr_full"] = response.xpath('//*[@class="contact-info"]//p').xpath("normalize-space()").get()
        yield item
