from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class FairmontSpider(SitemapSpider, StructuredDataSpider):
    name = "fairmont"
    FAIRMONT = {"brand": "Fairmont", "brand_wikidata": "Q1393345"}
    sitemap_urls = ["https://www.fairmont.com/en.sitemap.xml"]
    sitemap_rules = [("/hotels/[^/]+/[^/]+html$", "parse_sd")]

    def post_process_item(self, item, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.HOTEL, item)
        yield item
