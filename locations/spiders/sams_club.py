import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import FIREFOX_LATEST


class SamsClubSpider(SitemapSpider):
    name = "sams_club"
    item_attributes = {"brand": "Sam's Club", "brand_wikidata": "Q1972120"}
    sitemap_urls = ["https://www.samsclub.com/sitemap_locators.xml"]
    custom_settings = {"USER_AGENT": FIREFOX_LATEST}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.xpath("//h1/text()").get():
            item = Feature()
            item["name"] = response.xpath("//h1/text()").get()
            item["street_address"] = response.xpath('//*[@data-testid="store-address"]/text()').get()
            item["addr_full"] = response.xpath('//*[@data-testid="store-address"]').xpath("normalize-space()").get()
            item["phone"] = response.xpath('//*[contains(@href,"tel:")]/text()').get()
            item["ref"] = item["website"] = response.url
            item["lat"], item["lon"] = re.search(
                r"\"latitude\":(-?\d+\.\d+),.*longitude\":(-?\d+\.\d+)}", response.text
            ).groups()
            item["opening_hours"] = OpeningHours()
            for day_time in response.xpath('//*[@class="tl mt2"][1]//*[@class="flex justify-between mb1"]'):
                day_time_string = day_time.xpath("normalize-space()").get()
                item["opening_hours"].add_ranges_from_string(day_time_string)
            apply_category(Categories.SHOP_WHOLESALE, item)
            yield item
