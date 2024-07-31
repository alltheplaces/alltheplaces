from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class BAndMSpider(SitemapSpider, StructuredDataSpider):
    name = "b_and_m"
    item_attributes = {"brand": "B&M", "brand_wikidata": "Q4836931", "country": "GB"}
    allowed_domains = ["www.bmstores.co.uk"]
    sitemap_urls = ["https://www.bmstores.co.uk/hpcstores/storessitemap"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["LocalBusiness"]

    def inspect_item(self, item, response):
        apply_category(Categories.SHOP_VARIETY_STORE, item)

        if "phone" in item:
            if item["phone"].replace(" ", "").startswith("+443"):
                item.pop("phone", None)
        yield item
