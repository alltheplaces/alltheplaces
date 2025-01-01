import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class StudenacHRSpider(CrawlSpider):
    item_attributes = {"brand": "Studenac", "brand_wikidata": "Q65156084"}
    name = "studenac_hr"
    allowed_domains = ["studenac.hr"]
    # store finder contains about 90 extra stores compared to the sitemap
    start_urls = ["https://www.studenac.hr/trgovine"]
    rules = [Rule(LinkExtractor(allow=r"trgovine/\d{1,5}/t"), callback="parse", follow=False)]

    def parse(self, response: Response):
        item = Feature()
        item["ref"] = re.findall(r"trgovine/\d+/t(\d+)-", response.url)[0]
        item["website"] = response.url
        item["lat"] = response.xpath("//div[@class='marker']/@data-lat").get()
        item["lon"] = response.xpath("//div[@class='marker']/@data-lng").get()
        item["street_address"] = response.xpath("//div[@class='marketsingle__header']//h2/text()").get()

        hours = response.xpath("//div[@class='marketsingle__workhours']//ul/li")
        oh = OpeningHours()
        for day, range in zip(DAYS, hours):
            range = range.xpath("strong/text()").get(default="")
            if "zatvoreno" in range.lower():
                oh.set_closed(day)
            if ":" not in range.lower():
                continue  # no hours
            open_time, close_time = range.split("-")
            oh.add_range(day, open_time, close_time)
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
