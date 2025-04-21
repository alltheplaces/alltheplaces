from typing import Any

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class EssentielAntwerpSpider(CrawlSpider):
    name = "essentiel_antwerp"
    item_attributes = {"brand": "Essentiel Antwerp", "brand_wikidata": "Q117456339"}
    start_urls = ["https://www.essentiel-antwerp.com/be_en/ourstores"]

    rules = [
        Rule(
            LinkExtractor(
                restrict_xpaths='//*[@class="sps-NpIex BuilderAccordion_accordion_item__pPRwV"]//*[@class="sps-C92Xj"]//a'
            ),
            callback="parse",
        )
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["street_address"] = response.xpath("//p/text()").get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath("//p[2]/text()").get(), response.xpath("//p[3]/text()").get()]
        )
        item["website"] = item["ref"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//text()').get()
        extract_google_position(item, response)
        yield item
