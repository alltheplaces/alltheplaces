from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TheGoodGuysAUSpider(SitemapSpider, StructuredDataSpider):
    name = "the_good_guys_au"
    item_attributes = {"brand": "The Good Guys", "brand_wikidata": "Q7737217"}
    sitemap_urls = ["https://www.thegoodguys.com.au/sitemap.xml"]
    sitemap_rules = [("/stores/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("The Good Guys ")
        yield item
