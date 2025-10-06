from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AesopSpider(CrawlSpider, StructuredDataSpider):
    name = "aesop"
    item_attributes = {"brand": "Aesop", "brand_wikidata": "Q4688560"}
    start_urls = ["https://www.aesop.com/stores/all"]
    rules = [Rule(LinkExtractor(allow=r"/stores/"), callback="parse_sd", follow=True)]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("Aesop ", "")
        item["website"] = response.url
        apply_category(Categories.SHOP_COSMETICS, item)
        yield item
