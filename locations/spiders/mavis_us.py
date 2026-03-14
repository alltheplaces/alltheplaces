from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.ntb_us import NtbUSSpider
from locations.structured_data_spider import StructuredDataSpider

MAVIS_TIRES = {"name": "Mavis Tires & Brakes", "brand": "Mavis", "brand_wikidata": "Q65058420"}
MAVIS_DISCOUNT = {"name": "Mavis Discount Tire", "brand": "Mavis", "brand_wikidata": "Q65058420"}
TIRE_KINGDOM = {"brand": "Tire Kingdom", "brand_wikidata": "Q17090159"}
TUFFY = {"brand": "Tuffy", "brand_wikidata": "Q17125314"}
JACK_WILLIAMS = {"name": "Jack Williams Tire & Auto", "brand": "Jack Williams Tire & Auto"}


class MavisUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mavis_us"
    sitemap_urls = ["https://www.mavis.com/sitemaps/locations.xml"]
    sitemap_rules = [("/locations/", "parse_sd")]

    brands = {
        "Mavis Tires": (MAVIS_TIRES, Categories.SHOP_TYRES),
        "Mavis Tires and Brakes": (MAVIS_TIRES, Categories.SHOP_TYRES),
        "Melvin's Tires": (MAVIS_TIRES, Categories.SHOP_TYRES),
        "Mavis Discount Tire": (MAVIS_DISCOUNT, Categories.SHOP_TYRES),
        "NTB Tire & Service Centers": (NtbUSSpider.item_attributes, Categories.SHOP_CAR_REPAIR),
        "Tire Kingdom Service Centers": (TIRE_KINGDOM, Categories.SHOP_TYRES),
        "Tuffy Tire & Auto": (TUFFY, Categories.SHOP_TYRES),
        "Jack Williams Tire & Auto": (JACK_WILLIAMS, Categories.SHOP_CAR_REPAIR),
    }

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = item["name"].replace("amp;", "").replace("&apos;", "'")
        if brand := self.brands.get(item["name"]):
            brand, cat = brand
            item.update(brand)
            apply_category(cat, item)
        else:
            apply_category(Categories.SHOP_TYRES, item)
        item["addr_full"] = item.pop("street_address")
        yield item
