from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class BuckleUSSpider(SitemapSpider, StructuredDataSpider):
    name = "buckle_us"
    item_attributes = {"brand": "Buckle", "brand_wikidata": "Q4983306"}
    allowed_domains = ["local.buckle.com"]
    sitemap_urls = ["https://local.buckle.com/robots.txt"]
    sitemap_rules = [(r"\/clothing-\d+\.html$", "parse")]
    wanted_types = ["Clothing Store"]

    def post_process_item(self, item, response, ld_data):
        item["name"] = item["name"].replace("`", "’")
        item.pop("image", None)
        yield item
