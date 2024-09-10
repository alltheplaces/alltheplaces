from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.structured_data_spider import StructuredDataSpider


class SportClipsUSSpider(CrawlSpider, StructuredDataSpider):
    name = "sport_clips_us"
    item_attributes = {"brand": "Sport Clips", "brand_wikidata": "Q7579310"}
    allowed_domains = ["sportclips.com"]
    start_urls = ["https://sportclips.com/states"]
    rules = [Rule(LinkExtractor(allow=[r"/states/[\w-]+$"]), callback="parse_sd")]
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Sport Clips Haircuts of ")

        el = response.xpath(f"//h4[starts-with(text(), {ld_data['name']!r})]/..")
        item["website"] = item["ref"] = el.xpath(".//a[text()='View Website']/@href").get()
        assert item["ref"] is not None
        extract_google_position(item, el)

        yield item
