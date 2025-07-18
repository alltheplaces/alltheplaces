import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class EurospinSpider(SitemapSpider, StructuredDataSpider):
    name = "eurospin"
    item_attributes = {"brand": "EuroSpin", "brand_wikidata": "Q1374674"}
    sitemap_urls = [
        "https://www.eurospin.it/store-sitemap.xml",
        "https://www.eurospin.si/store-sitemap.xml",
        "https://www.eurospin.hr/store-sitemap.xml",
    ]
    sitemap_rules = [("/punti-vendita/|/prodajna-mesta/|/nase-poslovnice/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["street_address"] = re.sub("(?sim)<.+?>", " ", str(item["street_address"]))
        item["branch"] = item.pop("name")
        item.pop("image")
        item.pop("phone")
        item.pop("email")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
