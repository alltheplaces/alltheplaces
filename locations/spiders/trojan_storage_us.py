from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class TrojanStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "trojan_storage_us"
    item_attributes = {"brand": "Trojan Storage", "brand_wikidata": "Q108917137"}
    sitemap_urls = ["https://www.trojanstorage.com/sitemap_index.xml"]
    sitemap_rules = [(r"/self-storage/[a-z]{2}/[^/]+/[^/]+/$", "parse_sd")]
    wanted_types = ["LocalBusiness", "SelfStorage", "Organization"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        item["website"] = response.url
        item["branch"] = item.pop("name").removeprefix("Trojan Storage of ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
