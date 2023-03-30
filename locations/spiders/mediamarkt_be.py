import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_FR, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class MediaMarktBESpider(CrawlSpider, StructuredDataSpider):
    name = "media_markt_be"
    item_attributes = {"brand": "MediaMarkt", "brand_wikidata": "Q2381223"}
    start_urls = ["https://www.mediamarkt.be/fr/marketselection.html"]
    rules = [Rule(LinkExtractor(restrict_css=".all-markets-list"), callback="parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        name = response.xpath('//*[@id="my-market-content"]/h1/text()').get()
        if name:
            item["name"] = name
        opening_hours = self.parse_hours(response)
        if opening_hours:
            item["opening_hours"] = opening_hours

        yield item

    def parse_hours(self, response):
        opening_hours = OpeningHours()

        store = response.xpath('//*[@itemtype="https://schema.org/LocalBusiness"]')
        if store:
            all_hours = store.xpath('//*[@itemprop="openingHours"]/@content')
            regex = re.compile(r"(lu|ma|me|je|ve|sa|su)\s+(\d{2}:\d{2})\s*-(\d{2}:\d{2})")
            for hours in all_hours:
                hours_str = hours.get().strip()
                match = re.search(regex, hours_str)
                if match:
                    day_of_week = match.group(1).capitalize()
                    open_time = match.group(2)
                    close_time = match.group(3)

                    if close_time == "00:00":
                        close_time = "23:59"

                    opening_hours.add_range(day=DAYS_FR[day_of_week], open_time=open_time, close_time=close_time)

        return opening_hours.as_opening_hours()
