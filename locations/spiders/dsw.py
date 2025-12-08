from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DswSpider(SitemapSpider, StructuredDataSpider):
    name = "dsw"
    item_attributes = {"brand": "DSW", "brand_wikidata": "Q5206207"}
    allowed_domains = [
        "stores.dsw.com",
        "stores.dsw.ca",
    ]
    sitemap_urls = [
        "https://stores.dsw.com/sitemap.xml",
        "https://stores.dsw.ca/sitemap.xml",
    ]
    sitemap_rules = [(r"\/\w{2}\/[^/]+\/[^/]+(\.html)?$$", "parse_sd")]
    wanted_types = ["LocalBusiness", "ShoeStore"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = item["image"] = None
        item["branch"] = response.xpath('//span[@class="LocationName-geo"]/text()').extract_first()

        yield item
