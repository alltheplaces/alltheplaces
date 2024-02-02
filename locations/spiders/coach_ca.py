from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CoachCASpider(CrawlSpider, StructuredDataSpider):
    name = "coach_ca"
    item_attributes = {"brand": "Coach", "brand_wikidata": "Q727697"}
    start_urls = ["https://ca.coach.com/stores/index.html"]
    rules = [
        Rule(LinkExtractor(allow=r"/stores/(outlets/)?\w\w$", deny=r"/fr_ca/")),
        Rule(LinkExtractor(allow=r"/stores/(outlets/)?\w\w/[-\w]+$", deny=r"/fr_ca/")),
        Rule(
            LinkExtractor(allow=r"/stores/(outlets/)?\w\w/[-\w]+/.+$", deny=r"/fr_ca/"),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["Store", "OutletStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["extras"]["website:fr"] = response.urljoin(response.xpath('//a[text()="Français"]/@href').get())
        item["extras"]["website:en"] = response.url

        if item["name"].startswith("COACH Outlet"):
            item["name"] = "COACH Outlet"
        else:
            item["name"] = "COACH"

        item["branch"] = ld_data["name"].removeprefix(item["name"]).strip()

        yield item
