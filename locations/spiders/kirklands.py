from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class KirklandsSpider(CrawlSpider, StructuredDataSpider):
    name = "kirklands"
    item_attributes = {
        "brand": "Kirkland's",
        "brand_wikidata": "Q6415714",
    }
    start_urls = ["https://www.kirklands.com/custserv/locate_store.cmd"]
    rules = [Rule(LinkExtractor(allow=["/store.jsp?"]), callback="parse")]
    wanted_types = ["Store"]

    def parse(self, response):
        response.css(".NearbyStores").remove()
        response.css('a[href=""][itemprop="telephone"]').remove()
        yield from self.parse_sd(response)

    def post_process_item(self, item, response, ld_data, **kwargs):
        oh = OpeningHours()
        for row in response.css("#inStoreDiv .hours tr"):
            day, interval = row.css("td ::text").extract()
            open_time, close_time = interval.split(" - ")
            oh.add_range(day[:2], open_time, close_time, "%I %p")
        item["opening_hours"] = oh.as_opening_hours()
        yield item
