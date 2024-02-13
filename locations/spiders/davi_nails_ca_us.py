import re

from scrapy import Request

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DaViNailsCAUSSpider(WPStoreLocatorSpider):
    name = "davi_nails_ca_us"
    item_attributes = {
        "brand_wikidata": "Q108726836",
        "brand": "DaVi Nails",
        "extras": Categories.SHOP_BEAUTY.value,
    }
    allowed_domains = [
        "davinails.com",
    ]
    searchable_points_files = ["us_centroids_100mile_radius.csv"]
    search_radius = 10000
    max_results = 10000

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["city"] = item["city"].strip(",")
        item["name"] = re.sub(" inside WM \#\d+", "", item["name"])
        yield item
