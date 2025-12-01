from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class DelArteFRSpider(SitemapSpider):
    name = "del_arte_fr"
    item_attributes = {"brand": "Ristorante Del Arte", "brand_wikidata": "Q89208262"}
    sitemap_urls = ["https://occ.groupeleduff.com/occ/v2/delarte-fr/sitemap.xml"]
    sitemap_rules = [("/store-finder/", "parse")]
    sitemap_follow = ["Store"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = (
            response.xpath("//title/text()")
            .get()
            .removeprefix("Restaurant Italien & Pizzeria ")
            .removesuffix(" I Del Arte")
        )
        item["street_address"] = response.xpath('//*[@class = "cx-store-address mb-2"]//text()').get()
        item["phone"] = response.xpath('//*[@class= "cx-store-phone"]/text()').get()

        apply_category(Categories.RESTAURANT, item)
        extract_google_position(item, response)

        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@class ="cx-schedules-rows"]//div[contains(@class, "row")]'):
            day = sanitise_day(day_time.xpath('.//*[contains(@class,"cx-days")]/text()').get(), DAYS_FR)
            time = day_time.xpath('//*[contains(@class,"cx-hours")]').xpath("normalize-space()").get()
            if "Fermé" in time:
                item["opening_hours"].set_closed(day)
                continue
            for open_close_time in time.split("et"):
                open_time, close_time = open_close_time.split("-")
                item["opening_hours"].add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        yield item
