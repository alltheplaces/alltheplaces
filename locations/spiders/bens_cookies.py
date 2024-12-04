from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature


class BensCookiesSpider(SitemapSpider):
    name = "bens_cookies"
    item_attributes = {"brand": "Ben's Cookies", "brand_wikidata": "Q4885143"}
    sitemap_urls = ["https://www.benscookies.com/robots.txt"]
    sitemap_follow = ["location"]
    sitemap_rules = [("/stores/", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()

        try:
            item["opening_hours"] = self.parse_opening_hours(response)
        except:
            self.logger.warning("Error parsing opening hours: {}".format(response.url))

        yield item

    def parse_opening_hours(self, response: Response) -> OpeningHours:
        oh = OpeningHours()

        for rule in response.xpath('//ul[contains(@class, "hours")]/li'):
            day = sanitise_day(rule.xpath("./span[1]/text()").get())
            if not day:
                continue
            times = rule.xpath("./span[2]/text()").get()
            if times.upper() == "CLOSED":
                oh.set_closed(day)
            else:
                oh.add_range(rule.xpath("./span[1]/text()").get(), *times.replace("–", "-").split(" - "))

        return oh
