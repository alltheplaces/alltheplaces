import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class StoryFRSpider(SitemapSpider):
    name = "story_fr"
    item_attributes = {"brand": "Story", "name": "Story"}
    sitemap_urls = ["https://www.story.fr/magasins-sitemap.xml"]

    def parse(self, response):
        item = Feature()
        item["ref"] = response.xpath('//a[contains(@href, "?magasin=")]/@href').get().split("=")[-1]
        item["website"] = response.url
        item["branch"] = (
            response.xpath('//p[@class="shop__name"]/text()').get().removesuffix(" Story").removesuffix(" STORY")
        )
        # The first address lines can hold the franchisee's name, so keep only the street and the postcode line
        item["addr_full"] = merge_address_lines(
            response.xpath('//address[@class="shop__address"]/text()').getall()[-2:]
        )
        item["phone"] = response.xpath('//ul[@class="shop__contacts"]/li[1]/text()').getall()[-1]
        item["email"] = response.xpath('//ul[@class="shop__contacts"]//a[starts-with(@href, "mailto:")]/text()').get()
        item["lat"] = response.xpath('//div[@id="shop-map"]/@data-lat').get()
        item["lon"] = response.xpath('//div[@id="shop-map"]/@data-lng').get()
        item["opening_hours"] = OpeningHours()
        for row in response.xpath('//div[@class="shop__hours__table"]//tr'):
            day = sanitise_day(row.xpath("./td[1]/text()").get(), DAYS_FR)
            # Times look like "10h/12h - 14h/19h", "10h30 - 19h" or "14h/19"
            times = [
                f"{h}:{m or '00'}" for h, m in re.findall(r"(\d{1,2})h?(\d{2})?", row.xpath("./td[2]/text()").get(""))
            ]
            if not times:
                item["opening_hours"].set_closed(day)
            for open_time, close_time in zip(times[::2], times[1::2]):
                item["opening_hours"].add_range(day, open_time, close_time)
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
