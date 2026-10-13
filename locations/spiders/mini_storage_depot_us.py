from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MiniStorageDepotUSSpider(SitemapSpider, StructuredDataSpider):
    name = "mini_storage_depot_us"
    item_attributes = {"brand": "Mini Storage Depot", "brand_wikidata": "Q112833014"}
    sitemap_urls = ["https://www.ministoragedepot.com/sitemap_index.xml"]
    sitemap_rules = [(r"/storage-locations/[a-z]{2}/[^/]+/", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Mini Storage Depot - ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
