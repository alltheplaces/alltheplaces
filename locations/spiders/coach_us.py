from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CoachUSSpider(CrawlSpider, StructuredDataSpider):
    name = "coach_us"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    start_urls = ["https://www.coach.com/stores/index.html"]
    rules = [
        Rule(LinkExtractor(allow=r"/stores/(outlets/)?\w\w$")),
        Rule(LinkExtractor(allow=r"/stores/(outlets/)?\w\w/[-\w]+$")),
        Rule(
            LinkExtractor(allow=r"/stores/(outlets/)?\w\w/[-\w]+/.+$"),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["Store", "OutletStore"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item["name"].startswith("COACH Outlet"):
            item["name"] = "COACH Outlet"
        else:
            item["name"] = "COACH"

        item["branch"] = ld_data["name"].removeprefix(item["name"]).strip()

        yield item
