import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class OfficeSpider(SitemapSpider):
    name = "office"
    item_attributes = {"brand": "Office", "brand_wikidata": "Q7079121"}
    allowed_domains = ["office.co.uk"]
    sitemap_urls = ["https://www.office.co.uk/robots.txt"]
    sitemap_follow = ["store"]
    sitemap_rules = [(r"/view/content/storelocator\?storename", "parse")]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["branch"] = response.xpath('//span[@class="bold"]/text()').get().removeprefix("Office ")
        item["phone"] = response.xpath('//div[contains(span/text(), "Tel")]/text()').get()
        item["addr_full"] = merge_address_lines(
            response.xpath('//ul[contains(@class, "storelocator_addressdetails_address")]/li/text()').getall()[1:]
        )

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//span[@class="storelocator_open_times_day"]/text()').getall():
            if m := re.search(r"(\w+): (\d{1,2}:\d\d) - (\d\d:\d\d)", rule):
                item["opening_hours"].add_range(*m.groups())

        if coords := re.search(r"<coordinates>(.*?)</coordinates>", response.text):
            item["lon"], item["lat"] = coords.group(1).split(",")

        yield item
