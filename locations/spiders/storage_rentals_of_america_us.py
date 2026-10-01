from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StorageRentalsOfAmericaUSSpider(SitemapSpider, StructuredDataSpider):
    name = "storage_rentals_of_america_us"
    item_attributes = {"brand": "Storage Rentals of America", "brand_wikidata": "Q120733770"}
    sitemap_urls = ["https://www.sroa.com/find-storage/sitemap.xml"]
    sitemap_rules = [(r"/find-storage/[^/]+/[^/]+/(?!storage-types$)[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"email", "image", "opening_hours"}

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "").removeprefix("Storage Rentals of America - ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
