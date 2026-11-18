from time import strptime
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.google_url import extract_google_position
from locations.hours import OpeningHours, day_range
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class LeesFamousRecipeSpider(SitemapSpider):
    name = "lees_famous_recipe"
    item_attributes = {"brand": "Lee's Famous Recipe Chicken", "brand_wikidata": "Q6512810"}
    allowed_domains = ["leesfamousrecipe.com"]
    sitemap_urls = ["https://leesfamousrecipe.com/sitemap.xml"]
    sitemap_rules = [(r"/locations/.+/.+$", "parse")]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["phone"] = response.xpath(
            '//div[@class="location-store-details"]//a[starts-with(@href, "tel:")]/text()'
        ).get()
        item["addr_full"] = merge_address_lines(
            response.xpath(
                '//div[@class="location-store-details"]//div[@class="location-address-info"]/a//text()'
            ).getall()
        )

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//div[contains(@class, "operation-hours")]//li'):
            days = rule.xpath('./span[@class="days"]/text()').get("").split(" - ")
            open_time, close_time = rule.xpath('./span[@class="hours"]/text()').get("").split(" - ")
            if (close := strptime(close_time, "%I:%M %p")) <= strptime(open_time, "%I:%M %p") and close.tm_hour:
                continue
            for day in day_range(days[0], days[-1]):
                item["opening_hours"].add_range(day, open_time, close_time, time_format="%I:%M %p")

        extract_google_position(item, response)
        apply_category(Categories.FAST_FOOD, item)

        yield item
