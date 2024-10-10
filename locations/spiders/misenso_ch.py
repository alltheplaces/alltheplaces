from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature


class MisensoCHSpider(SitemapSpider):
    name = "misenso_ch"
    item_attributes = {"brand": "Misenso", "brand_wikidata": "Q116151325"}
    sitemap_urls = ["https://www.misenso.ch/de/wp-sitemap.xml"]
    sitemap_rules = [(r"/filialen/[a-zA-Z0-9]+", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["name"] = response.xpath("//h1/text()").get()
        item["addr_full"] = response.xpath("//p").xpath("normalize-space()").get()
        item["ref"] = item["website"] = response.url
        item["phone"] = response.xpath('//*[@class="rtc"]//*[contains(@href,"tel:")]/text()').get()
        item["email"] = response.xpath('//*[contains(@href,"mailto:")]/text()').get()
        apply_category(Categories.SHOP_OPTICIAN, item)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath(
            '//*[@class = "type--module name--text moix--1 moix-wowr--1 moix-mona--text--0 container number_of_cols--two"]//li'
        ):
            day_time = day_time.xpath("normalize-space()").get()
            item["opening_hours"].add_ranges_from_string(day_time, days=DAYS_DE)
        yield item
