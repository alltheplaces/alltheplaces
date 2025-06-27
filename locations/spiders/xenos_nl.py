import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_NL, OpeningHours, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class XenosNLSpider(CrawlSpider, StructuredDataSpider):
    name = "xenos_nl"
    item_attributes = {"brand": "Xenos", "brand_wikidata": "Q16547960"}
    start_urls = ["https://www.xenos.nl/winkels"]
    rules = [Rule(LinkExtractor(allow=r"/winkels/[-\w]+", deny=r"/winkels/\w+$"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = response.xpath("//title/text()").get().split(" | ")[0].removeprefix("Xenos ")
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["city"] = response.xpath('//*[@itemprop="addressLocality"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//*[@class="opening__times"]//li'):
            if day := sanitise_day(rule.xpath("./span[1]/text()").get(), DAYS_NL):
                hours = rule.xpath("./span[2]/text()").get("")
                for open_time, close_time in re.findall(r"(\d+:\d+)[-\s]+(\d+:\d+)", hours):
                    item["opening_hours"].add_range(day, open_time, close_time)
        apply_category(Categories.SHOP_HOUSEWARE, item)
        yield item
