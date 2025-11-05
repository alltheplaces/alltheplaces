import re

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider


class DominosPizzaINSpider(SitemapSpider, StructuredDataSpider):
    name = "dominos_pizza_in"
    item_attributes = {"brand": "Domino's", "brand_wikidata": "Q839466"}
    sitemap_urls = ["https://www.dominos.co.in/store-locations/sitemap_store.xml"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Dominos Pizza ")
        item["addr_full"] = item.pop("street_address")
        if not clean_address(item["addr_full"]):
            yield Request(
                url=response.url.replace("store-locations", "store-location"),
                callback=self.parse_location,
                cb_kwargs=dict(item=item),
            )
        else:
            yield item

    def parse_location(self, response: Response, item: Feature):
        address = response.xpath('//*[contains(@class, "store-page-address")]/text()').get("")
        item["addr_full"] = re.sub(r"(.+?\d{5,}).*", r"\1", address)  # Remove phone to clean address
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/@href').get()
        yield item
