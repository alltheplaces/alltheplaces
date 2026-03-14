from typing import Any

import chompjs
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BinnysUSSpider(SitemapSpider):
    name = "binnys_us"
    item_attributes = {"brand": "Binny's Beverage Depot", "brand_wikidata": "Q30687714"}
    allowed_domains = ["binnys.com"]
    sitemap_urls = ["https://www.binnys.com/robots.txt"]
    sitemap_rules = [(r"/store-locator/([^/]+)/", "parse")]
    requires_proxy = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        script = response.xpath('//script/text()[contains(.,"var serverSideViewModel")]').get()
        data = chompjs.parse_js_object(script)
        item = DictParser.parse(data)
        item["branch"] = item.pop("name")
        item["website"] = response.url

        try:
            item["opening_hours"] = self.parse_opening_hours(data["storeSchedule"])
        except:
            pass

        yield item

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            oh.add_range(rule["dayOfTheWeek"], rule["openingHours"], rule["closingHours"], "%I:%M %p")
        return oh
