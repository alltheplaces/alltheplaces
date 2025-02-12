import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours, day_range, sanitise_day
from locations.structured_data_spider import StructuredDataSpider


class AvisSpider(CrawlSpider, StructuredDataSpider):
    name = "avis"
    item_attributes = {"brand": "Avis", "brand_wikidata": "Q791136"}
    download_delay = 0.5
    allowed_domains = ["avis.com"]
    start_urls = [
        "https://www.avis.com/en/locations/avisworldwide",
        "https://www.avis.com/en/locations/me",  # Country ME not available on worldwide page
    ]
    rules = [
        Rule(LinkExtractor(allow=r"/en/locations/\w{2}$", restrict_xpaths='//*[contains(@class,"world-wide-list")]')),
        Rule(LinkExtractor(allow=r"/en/locations/\w{2}/[-\w]+$")),
        Rule(LinkExtractor(allow=r"/en/locations/\w{2}/[-\w]+/[-\w]+$"), callback="parse_sd", follow=True),
        Rule(LinkExtractor(allow=r"/en/locations/\w{2}/[-\w]+/[-\w]+/[-\w]+$"), callback="parse_sd"),
    ]
    search_for_image = False
    search_for_facebook = False
    search_for_twitter = False

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath('//meta[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//meta[@itemprop="longitude"]/@content').get()

        item["branch"] = item.pop("name").removeprefix("Avis ")

        if hours := response.xpath('//meta[@itemprop="openingHours"]/@content').get():
            item["opening_hours"] = OpeningHours()
            for start_day, end_day, start_time, end_time in re.findall(
                r"(\w{3})(?:\s-\s(\w{3}))?\s(\d+:\d\d\s[APM]+)\s-\s(\d+:\d\d\s[APM]+)",
                hours,
            ):
                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)
                if not end_day:
                    end_day = start_day
                if start_day:
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day), start_time, end_time, time_format="%I:%M %p"
                    )

        yield item
