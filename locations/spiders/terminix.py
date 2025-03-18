from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TerminixSpider(SitemapSpider, StructuredDataSpider):
    name = "terminix"
    item_attributes = {
        "brand": "Terminix",
        "brand_wikidata": "Q7702831",
    }
    sitemap_urls = ["https://www.terminix.com/sitemap.xml"]
    sitemap_rules = [
        (r"/exterminators/\w+/[\w\-]+-(\d+)/$", "parse_sd"),
    ]
    requires_proxy = True

    def pre_process_data(self, ld_data, **kwargs):
        ld_data.pop("image", None)

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Remove brand social links
        item.pop("facebook", None)

        apply_category(Categories.SHOP_PEST_CONTROL, item)
        yield item
