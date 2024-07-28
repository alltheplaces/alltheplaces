import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class StudenacHRSpider(CrawlSpider):
    item_attributes = {"brand": "Studenac", "brand_wikidata": "Q65156084"}
    name = "studenac_hr"
    allowed_domains = ["studenac.hr"]
    # store finder contains about 90 extra stores compared to the sitemap
    start_urls = ["https://www.studenac.hr/popis-trgovina"]
    rules = [Rule(LinkExtractor(allow=r"trgovine/\d{1,5}/t"), callback="parse", follow=False)]

    def parse(self, response: Response):
        # email address on store websites is generic
        item = Feature()
        item["ref"] = re.findall(r"trgovine/\d+/t(\d+)-", response.url)[0]
        item["website"] = response.url
        marker = response.css("div.marker")[0]
        item["lat"], item["lon"] = marker.attrib["data-lat"], marker.attrib["data-lng"]
        info = response.css("div.info")[0]
        item["city"], item["street_address"], *_ = [i.strip() for i in info.css("h2::text").getall() if i.strip()]
        opening_hours = OpeningHours()
        ranges = response.css("ul.info__list p::text").getall()
        for day, range in zip(DAYS, ranges):
            if "zatvoreno" in range:
                continue  # closed
            if ":" not in range:
                continue  # no hours
            open_time, close_time = range.split("-")
            opening_hours.add_range(day, open_time.strip(), close_time.strip())
        item["opening_hours"] = opening_hours
        yield item
