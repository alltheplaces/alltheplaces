import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class GoodLifeFitnessSpider(SitemapSpider):
    name = "goodlifefitness"
    item_attributes = {"brand": "GoodLife Fitness", "brand_wikidata": "Q3110654"}
    allowed_domains = ["goodlifefitness.com"]
    sitemap_urls = ["https://www.goodlifefitness.com/sitemap.xml"]
    sitemap_rules = [(r"/clubs/club.", "parse")]

    def parse(self, response):
        template = "https://www.goodlifefitness.com/content/experience-fragments/goodlife/header/master/jcr:content/root/responsivegrid/header.GetClubsWithDetails.{}.false.true.20221127.json"
        url_id = re.findall("[0-9]+", response.url)[0]
        yield scrapy.Request(url=template.format(url_id), callback=self.parse_club)

    def parse_club(self, response):
        data = response.json().get("map", {}).get("response")[0]
        item = DictParser.parse(data)
        item["name"] = data.get("ClubName")
        item["website"] = data.get("pagePath")
        item["ref"] = data.get("ClubNumber")
        oh = OpeningHours()
        for day in data.get("OperatingHours"):
            oh.add_range(
                day=DAYS[day.get("Day")],
                open_time=day.get("StartTime").strip("Z")[-8:][:5],
                close_time=day.get("EndTime").strip("Z")[-8:][:5],
            )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
