from typing import Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TommyBahamaSpider(SitemapSpider, StructuredDataSpider):
    name = "tommy_bahama"
    item_attributes = {"brand": "Tommy Bahama", "brand_wikidata": "Q3531299"}
    sitemap_urls = ["https://www.tommybahama.com/en/sitemap.xml"]
    sitemap_rules = [("/en/store/", "parse_sd")]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    wanted_types = ["ClothingStore"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        item["ref"] = item["website"] = response.url

        branch = item.pop("name")
        if branch.startswith("Tommy Bahama Home Store"):
            item["name"] = "Tommy Bahama Home Store"
            item["branch"] = branch.removeprefix("Tommy Bahama Home Store").strip(" -")
        elif branch.endswith(" (Outlet)"):
            item["name"] = "Tommy Bahama Outlet"
            item["branch"] = branch.removesuffix("(Outlet)")
        else:
            item["name"] = "Tommy Bahama"
            item["branch"] = branch

        try:
            item["opening_hours"] = self.parse_hours(response)
        except:
            pass

        apply_category(Categories.SHOP_CLOTHES, item)
        yield item

    def parse_hours(self, response: TextResponse) -> OpeningHours:
        oh = OpeningHours()
        for day, time in zip(
            response.xpath(
                '//div[@id="store-hours-container"]//div[@class="store-hours-columns"]/div[1]/div/text()'
            ).getall(),
            response.xpath(
                '//div[@id="store-hours-container"]//div[@class="store-hours-columns"]/div[2]/div/text()'
            ).getall(),
        ):
            if time == "CLOSED":
                oh.set_closed(day)
                continue
            else:
                start_time, end_time = time.replace("–", "-").split("-")
                oh.add_range(day, start_time.strip(), end_time.strip(), time_format="%I:%M %p")
        return oh
