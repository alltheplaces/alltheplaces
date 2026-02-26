from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class NisalocalGBSpider(CrawlSpider, StructuredDataSpider):
    name = "nisalocal_gb"
    item_attributes = {"brand": "Nisa", "brand_wikidata": "Q16999069"}
    allowed_domains = ["nisalocally.co.uk"]
    start_urls = ["https://www.nisalocally.co.uk/stores/index.html"]
    rules = [Rule(LinkExtractor(allow=".*/stores/.*"), callback="parse_sd", follow=True)]
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("Test "):
            return
        elif "Nisa Extra" in item["name"]:
            apply_category(Categories.SHOP_SUPERMARKET, item)
        else:
            apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
