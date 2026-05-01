from typing import Iterable

import chompjs
from scrapy import Request
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class TommyBahamaSpider(StructuredDataSpider):
    name = "tommy_bahama"
    item_attributes = {"brand": "Tommy Bahama", "brand_wikidata": "Q3531299"}
    start_urls = ["https://www.tommybahama.com/store-finder"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}
    wanted_types = ["ClothingStore"]
    search_for_twitter = False
    search_for_facebook = False
    search_for_email = False

    def parse(self, response: TextResponse, **kwargs):
        # The sitemap does not include the restaurants, so use this JS list instead
        script = response.xpath("//script[contains(text(), 'window.allStoresData = ')]/text()").get()
        all_stores_data = chompjs.parse_js_object(script)
        for store in all_stores_data:
            yield Request(
                response.urljoin(store["url"]),
                callback=self.parse_island if store.get("restaurantUrl", False) else self.parse_sd,
            )

    def parse_island(self, response: TextResponse):
        item = Feature()
        item["website"] = item["ref"] = response.url
        item["lat"] = response.xpath("//@location-latitude").get()
        item["lon"] = response.xpath("//@location-longitude").get()
        item["branch"] = response.xpath("//@location-name").get()
        item["street_address"] = response.xpath("//@location-address").get()
        item["addr_full"] = merge_address_lines(
            [item["street_address"], response.xpath("//@location-city-state-zip").get()]
        )

        oh = OpeningHours()
        for row in response.css(".hours tr"):
            oh.add_ranges_from_string(" ".join(row.xpath("*/text()").getall()))
        item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)
        yield item

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

        item["opening_hours"] = self.parse_hours(response)

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
