from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class KgFashionSuperstoreUSSpider(CrawlSpider, StructuredDataSpider):
    name = "kg_fashion_superstore_us"
    item_attributes = {"brand": "K&G Fashion Superstore", "name": "K&G Fashion Superstore"}
    allowed_domains = ["www.kgstores.com"]
    start_urls = ["https://www.kgstores.com/kg/store/directory"]
    rules = [Rule(LinkExtractor(allow=r"/kg/store/get/\d+$"), callback="parse_sd")]
    wanted_types = ["MensClothingStore"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}
    requires_proxy = True
    # Every store page links to the same generic brand logo and the same
    # brand-wide Facebook page, neither of which is location-specific.
    drop_attributes = {"image", "facebook"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        # The site's own markup always reports addressCountry as "CA", which is
        # incorrect for this US-only chain.
        item["country"] = "US"

        # The site combines brand and city into a single name field, e.g.
        # "K&G Fashion Superstore ORLANDO, FL - Orlando". Use the neatly
        # title-cased city at the end of that string as the branch name, and
        # let item_attributes backfill the plain brand name.
        if item.get("name") and " - " in item["name"]:
            item["branch"] = item["name"].rsplit(" - ", 1)[-1].strip()
        item["name"] = None

        apply_category(Categories.SHOP_CLOTHES, item)

        yield item
