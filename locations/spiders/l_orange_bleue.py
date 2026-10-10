import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_ES, DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class LOrangeBleueSpider(SitemapSpider, StructuredDataSpider):
    name = "l_orange_bleue"
    item_attributes = {"brand": "L'Orange Bleue", "brand_wikidata": "Q3204640"}
    sitemap_urls = [
        "https://www.lorangebleue.fr/clubs-list-sitemap1.xml",
        "https://www.lorangebleue.es/clubs-list-sitemap1.xml",
    ]
    sitemap_rules = [(r"/(clubs|gimnasios)/[^/]+/$", "parse_sd")]
    wanted_types = ["ExerciseGym"]
    drop_attributes = {"image"}

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if response.xpath('//div[@class="club-offer-soon"]'):
            return  # Planned club, not open yet

        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["branch"] = item.pop("name")
        item["website"] = response.url

        # Clubs list staffed hours and, where members have extended access, a second schedule for that access
        schedule = response.xpath('//div[contains(@class, "club-horaires-full")]//ul[@class="club-horaires"]')
        if not schedule:
            schedule = response.xpath('//div[contains(@class, "club-horaires-home")]//ul[@class="club-horaires"]')
        item["opening_hours"] = self.parse_hours(schedule.xpath("./li"))

        apply_category(Categories.GYM, item)
        yield item

    def parse_hours(self, rules) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = sanitise_day(rule.xpath('./span[@class="day"]/text()').get("").strip(), DAYS_FR | DAYS_ES)
            if not day:
                continue
            hours = rule.xpath('./span[@class="hours"]/text()').get("")
            times = re.findall(r"(\d{1,2})(?:[:h](\d{2}))?h?", hours)
            if not times:
                oh.set_closed(day)
                continue
            times = ["{:02d}:{}".format(int(h), m or "00") for h, m in times]
            for open_time, close_time in zip(times[::2], times[1::2]):
                oh.add_range(day, open_time, close_time)
        return oh
