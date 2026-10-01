from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class StoragePostUSSpider(CrawlSpider, StructuredDataSpider):
    name = "storage_post_us"
    item_attributes = {"brand": "Storage Post"}
    allowed_domains = ["www.storagepost.com"]
    start_urls = ["https://www.storagepost.com/locations"]
    rules = [
        Rule(LinkExtractor(allow=r"/locations/[^/]+(/[^/]+)?$", deny=r"/blog|/\d{5}$")),
        Rule(LinkExtractor(allow=r"/locations/[^/]+/[^/]+/[^/]+$", deny=r"/blog|/\d{5}$"), callback="parse_sd"),
    ]
    wanted_types = ["SelfStorage"]
    time_format = "%I:%M %p"
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("lat") and item.get("lon") and float(item["lat"]) < 0 < float(item["lon"]):
            item["lat"], item["lon"] = item["lon"], item["lat"]
        item["branch"] = (item.pop("name", None) or "").removeprefix("Storage Post - ") or None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
