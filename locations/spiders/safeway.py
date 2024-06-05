from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SafewaySpider(SitemapSpider, StructuredDataSpider):
    name = "safeway"
    item_attributes = {
        "brand": "Safeway",
        "brand_wikidata": "Q1508234",
        "country": "US",
        "nsi_id": "N/A",
    }
    allowed_domains = ["safeway.com"]
    sitemap_urls = [
        "https://local.safeway.com/sitemap.xml",
        "https://local.pharmacy.safeway.com/sitemap.xml",
        "https://local.fuel.safeway.com/sitemap.xml",
    ]
    sitemap_rules = [(r"^https://local\.(?:fuel\.|pharmacy\.)?safeway\.com/safeway/\w\w/[-\w]+/[-\w]+\.html$", "parse")]
    wanted_types = ["GroceryStore", "GasStation", "Pharmacy"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["image"] = None
        if ld_data["@type"] == "GroceryStore":
            apply_category(Categories.SHOP_SUPERMARKET, item)
        elif ld_data["@type"] == "GasStation":
            apply_category(Categories.FUEL_STATION, item)
        elif ld_data["@type"] == "Pharmacy":
            apply_category(Categories.PHARMACY, item)

        yield item
