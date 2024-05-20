from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class MycarTyreAndAutoAUSpider(SitemapSpider, StructuredDataSpider):
    name = "mycar_tyre_and_auto_au"
    item_attributes = {
        "brand": "mycar Tyre & Auto",
        "brand_wikidata": "Q106224674",
        "extras": Categories.SHOP_CAR_REPAIR.value,
    }
    allowed_domains = ["www.mycar.com.au"]
    sitemap_urls = ["https://www.mycar.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.mycar\.com\.au\/stores\/\w+\/(?:(?<!closed-)[\w\-](?!-closed))+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("facebook", None)  # Brand-specific not location-specific.
        yield item
