from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AllsaintsSpider(CrawlSpider, StructuredDataSpider):
    name = "allsaints"
    item_attributes = {"brand": "AllSaints", "brand_wikidata": "Q4728473"}
    start_urls = [
        "https://www.allsaints.com/stores/?sw_skipheader=true&sw_skipfooter=true",
    ]
    rules = [Rule(LinkExtractor(allow=r"https://www.allsaints.com/stores/[\w-]+/[\w-]+/[^/]+$"), callback="parse")]

    wanted_types = ["Store"]
    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DEFAULT_REQUEST_HEADERS": {
            "Host": "www.allsaints.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "upgrade-insecure-requests": "1",
            "Referer": "https://www.allsaints.com/",
            "Connection": "keep-alive",
        },
    }
    drop_attributes = {"email", "contact:facebook", "contact:twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").replace("AllSaints ", "")
        apply_category(Categories.SHOP_CLOTHES, item)
        yield item
