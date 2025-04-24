from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# Storelocator on https://www.coastalcountry.com/about/store-locations
# Individual pages have structured data


class CoastalCountrySpider(SitemapSpider, StructuredDataSpider):
    name = "coastal_country"
    item_attributes = {"brand": "Coastal"}
    allowed_domains = ["www.coastalcountry.com"]
    sitemap_urls = ["https://www.coastalcountry.com/sitemap.xml"]
    sitemap_rules = [(r"/store-locations/[\w-]+$", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_COUNTRY_STORE, item)
        yield item
