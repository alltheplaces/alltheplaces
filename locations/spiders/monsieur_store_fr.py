from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class MonsieurStoreFRSpider(SitemapSpider):
    name = "monsieur_store_fr"
    item_attributes = {"brand": "Monsieur Store", "brand_wikidata": "Q113686692"}
    sitemap_urls = ["https://monsieurstore.com/sitemap_index.xml"]
    sitemap_follow = ["store-sitemap.xml"]
    sitemap_rules = [(r"https://monsieurstore.com/magasin/[a-z-0-9]+/$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["branch"] = (
            response.xpath('//*[@class="store-header__store-name"]//text()')
            .get()
            .strip()
            .removeprefix("Monsieur Store ")
            .strip("– ")
        )
        item["addr_full"] = ",".join(response.xpath('//*[@class="store-header__address"]//text()').getall())
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[contains(@href,"tel:")]//@href').get().replace("tel:", "")

        oh = OpeningHours()
        for day_time in response.xpath('//*[@class="store-header__schedule"]//li'):
            day = sanitise_day(day_time.xpath('.//*[@class="store-header__day"]/text()').get().strip(), DAYS_FR)
            for time in (
                day_time.xpath('.//*[@class="store-header__time"]').xpath("normalize-space()").get().replace("h", ":")
            ).split("/"):
                if time == "magasin fermé":
                    oh.set_closed(day)
                else:
                    open_time, close_time = time.split("-")
                    oh.add_range(day=day, open_time=open_time.strip(), close_time=close_time.strip())
        item["opening_hours"] = oh

        apply_category(Categories.SHOP_WINDOW_BLIND, item)

        yield item
