import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours, sanitise_day


class ServiceApotheekNLSpider(SitemapSpider):
    name = "service_apotheek_nl"
    item_attributes = {"brand": "Service Apotheek", "brand_wikidata": "Q124129179"}
    sitemap_urls = ["https://www.serviceapotheek.nl/sitemap.xml"]
    sitemap_rules = [(r"nl/[^/]+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if not (contact := re.search(r'"contact":(\{"email":.*?\}\]\})', response.text.replace('\\"', '"'))):
            return
        location = json.loads(contact.group(1))["addresses"][0]
        item = DictParser.parse(location)
        item["ref"] = item["website"] = response.url
        item["housenumber"] = location["number"]
        item["branch"] = item.pop("name").removeprefix("Service Apotheek ")
        item["opening_hours"] = self.parse_opening_hours(response)
        apply_category(Categories.PHARMACY, item)
        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()
        for rule in response.xpath('//h3[text()="Openingstijden"]/parent::div/following-sibling::div[1]/div'):
            day = sanitise_day(rule.xpath("./span[1]/text()").get(), DAYS_NL)
            times = re.findall(r"\d\d:\d\d", "".join(rule.xpath("./span[2]//text()").getall()))
            if not times:
                oh.set_closed(day)
            for open_time, close_time in zip(times[::2], times[1::2]):
                oh.add_range(day, open_time, close_time)
        return oh
