from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StarbucksAESpider(SitemapSpider, StructuredDataSpider):
    name = "starbucks_ae"
    item_attributes = {"brand": "ستاربكس", "brand_wikidata": "Q37158"}
    sitemap_urls = ["https://locations.starbucks.ae/robots.txt"]
    sitemap_rules = [(r"ae/directory/[^/]+/[^/]+$", "parse")]
    wanted_types = ["Restaurant"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["branch"] = item.pop("name").removeprefix("Starbucks ")

        item["website"] = item["extras"]["website:ar"] = response.urljoin(
            response.xpath('//a[@class="Header-langOption"][text()="Arabic"]/@href').get()
        )
        item["extras"]["website:en"] = response.url

        yield item
