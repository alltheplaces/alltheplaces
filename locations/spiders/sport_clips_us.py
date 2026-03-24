from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.open_graph_spider import OpenGraphSpider


class SportClipsUSSpider(CrawlSpider, OpenGraphSpider):
    name = "sport_clips_us"
    item_attributes = {"brand": "Sport Clips", "brand_wikidata": "Q7579310"}
    allowed_domains = ["sportclips.com"]
    start_urls = ["https://sportclips.com/states"]
    rules = [
        Rule(LinkExtractor(allow=[r"/states/[\w-]+$"]), follow=True),
        Rule(LinkExtractor(allow=[r"/states/[\w-]+/[\w-]+$"]), follow=True),
        Rule(LinkExtractor(allow=[r"/us-[a-z]{2}-[\w-]+-[a-z]{2}\d+"]), callback="parse_og"),
    ]

    def post_process_item(self, item, response, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Haircuts for Men | Sport Clips Haircuts Of ")
        yield item
