from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AnnTaylorUSSpider(SitemapSpider, StructuredDataSpider):
    name = "ann_taylor_us"
    item_attributes = {"brand": "Ann Taylor", "brand_wikidata": "Q4766699"}
    drop_attributes = {"facebook"}
    allowed_domains = ["www.anntaylor.com"]
    sitemap_urls = ["https://www.anntaylor.com/sitemap_index.xml"]
    sitemap_rules = [(r"^https:\/\/www\.anntaylor\.com\/store(?:\/factory)?\/[a-z]{2}\/[\w\-]+\/[\w\-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
