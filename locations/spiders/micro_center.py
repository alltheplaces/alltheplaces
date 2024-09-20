from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MicroCenterSpider(CrawlSpider, StructuredDataSpider):
    name = "micro_center"
    item_attributes = {"brand": "Micro Center", "brand_wikidata": "Q6839153"}
    allowed_domains = ["www.microcenter.com"]
    start_urls = ["https://www.microcenter.com/site/stores/default.aspx"]
    rules = [Rule(LinkExtractor("/site/stores/"), "parse")]
    wanted_types = ["ComputerStore"]
    time_format = "%H"

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["ref"] == "https://www.microcenter.com/site/stores/default.aspx":
            return None
        if (item.get("name") or "").startswith("Micro Center - "):
            item["branch"] = item.pop("name").removeprefix("Micro Center - ")
            apply_category(Categories.SHOP_COMPUTER, item)
            yield item
        else:
            pass  # Duplicate Micro data on every page
