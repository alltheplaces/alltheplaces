from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class CaptainDUSSpider(SitemapSpider):
    name = "captain_d_us"
    item_attributes = {"brand": "Captain D's", "brand_wikidata": "Q5036616"}
    sitemap_urls = ["https://locations.captainds.com/sitemap_index.xml"]
    sitemap_rules = [(r"https://locations.captainds.com/ll/[^/]+/[^/]+/[^/]+/[a-z-0-9]+/$", "parse")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    wanted_types = ["LocalBusiness"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = chompjs.parse_js_object(response.xpath('//*[@type="application/ld+json"][2]/text()').get().strip())
        item = DictParser.parse(raw_data)
        item["ref"] = item["website"] = response.url
        oh = OpeningHours()
        for day_time in response.xpath('//*[@itemprop="openingHours"]/@content').getall():
            print(day_time)
            oh.add_ranges_from_string(day_time)
        item["opening_hours"] = oh
        yield item
