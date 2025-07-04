from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import DAYS_CZ, OpeningHours, sanitise_day
from locations.items import Feature
from locations.structured_data_spider import extract_email, extract_phone


class TetaCZSpider(SitemapSpider):
    name = "teta_cz"
    item_attributes = {"brand": "Teta", "brand_wikidata": "Q20860823"}
    sitemap_urls = ["https://www.tetadrogerie.cz/sitemap_index.xml"]
    sitemap_rules = [(r"/prodejny/\d+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["addr_full"] = response.xpath("//h1/text()").get().strip()
        item["website"] = item["ref"] = response.url

        extract_google_position(item, response)
        extract_email(item, response)
        extract_phone(item, response.xpath('//div[@class="c-store-detail"]'))

        oh = OpeningHours()
        for rule in response.xpath('//*[@class="c-hours c-store-detail__main-opening-times"]//li'):
            day = sanitise_day(rule.xpath(".//text()").get(), DAYS_CZ)
            time = rule.xpath(r"./span/text()").get()

            if (time == "Zavřeno") or (day is None):
                continue

            for period in time.split(","):
                open_time, close_time = period.split("-")
                oh.add_range(day, open_time.strip(), close_time.strip())

        item["opening_hours"] = oh

        apply_category(Categories.SHOP_CHEMIST, item)

        yield item
