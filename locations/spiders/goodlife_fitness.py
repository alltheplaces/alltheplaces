from datetime import datetime
from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class GoodlifeFitnessSpider(SitemapSpider, StructuredDataSpider):
    name = "goodlife_fitness"
    item_attributes = {"brand": "GoodLife Fitness", "brand_wikidata": "Q3110654"}
    allowed_domains = ["goodlifefitness.com"]
    sitemap_urls = ["https://www.goodlifefitness.com/sitemap.xml"]
    sitemap_rules = [(r"/clubs/club.", "parse")]
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs: Any) -> Iterable[Any]:
        club_id = response.xpath("//*[contains(@class, 'js-directions-map')]/@data-club-id").get()
        if not club_id:
            return
        item["branch"] = item.pop("name")
        item["lat"] = response.xpath("//@data-club-lat").get()
        item["lon"] = response.xpath("//@data-club-lng").get()
        apply_category(Categories.GYM, item)

        api_path = response.xpath("//*[@id='header-path']/@data-api-path").get()
        yield Request(
            url=f"https://www.goodlifefitness.com{api_path}.GetClubsWithDetails.{club_id}.false.true.0.json",
            callback=self.parse_club_details,
            cb_kwargs={"item": item},
        )

    def parse_club_details(self, response: Response, item: Feature, **kwargs: Any) -> Any:
        club = response.json()["map"]["response"][0]
        item["phone"] = club["Phone"]
        item["email"] = club["Email"]

        item["opening_hours"] = OpeningHours()
        for rule in club["RegularOperatingHours"]:
            start = datetime.fromisoformat(rule["StartTime"])
            end = datetime.fromisoformat(rule["EndTime"])
            day = DAYS[start.weekday()]
            if start == end:
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_range(day, start.strftime("%H:%M"), end.strftime("%H:%M"))
        yield item
