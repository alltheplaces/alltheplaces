from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class AesopSpider(CrawlSpider, StructuredDataSpider, CamoufoxSpider):
    name = "aesop"
    item_attributes = {"brand": "Aesop", "brand_wikidata": "Q4688560"}
    allowed_domains = ["shop.aesop.com"]
    start_urls = ["https://shop.aesop.com/stores/all"]
    rules = [Rule(LinkExtractor(allow="/stores/"), callback="parse_sd", follow=True)]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Aesop ", "")
        item["website"] = response.url
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
