from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class MacaroniGrillUSSpider(SitemapSpider, StructuredDataSpider):
    name = "macaroni_grill_us"
    item_attributes = {"brand": "Romano's Macaroni Grill", "brand_wikidata": "Q7362714"}
    allowed_domains = ["macaronigrill.com"]
    sitemap_urls = ["https://www.macaronigrill.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/[-\w]+-[a-z]{2}$", "parse_sd")]
    wanted_types = ["Restaurant"]
    drop_attributes = {"email"}

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "italian"
        yield item
