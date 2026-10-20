from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class StorageSenseUSSpider(SitemapSpider, StructuredDataSpider):
    name = "storage_sense_us"
    item_attributes = {"brand": "Storage Sense", "brand_wikidata": "Q126620207"}
    sitemap_urls = ["https://www.storagesense.com/candee_location-sitemap.xml"]
    sitemap_rules = [(r"(?i)/location/usa/", "parse_sd")]
    drop_attributes = {"email", "image"}

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", "").removeprefix("Storage Sense - ").removesuffix(" - Self Service")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
