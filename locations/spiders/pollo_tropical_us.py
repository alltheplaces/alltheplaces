from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class PolloTropicalUSSpider(SitemapSpider, StructuredDataSpider):
    name = "pollo_tropical_us"
    item_attributes = {"brand": "Pollo Tropical", "brand_wikidata": "Q3395356"}
    sitemap_urls = ["https://locations.pollotropical.com/robots.txt"]
    sitemap_rules = [(r"https://locations\.pollotropical\.com/\w\w/[^/]+/[^/]+$", "parse")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"] = response.xpath('//meta[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//meta[@itemprop="longitude"]/@content').get()
        item["extras"]["website:menu"] = response.xpath(
            '//a[@class="Link Core-cta--online"][contains(@href, "https://order.pollotropical.com")]/@href'
        ).get()

        yield item
