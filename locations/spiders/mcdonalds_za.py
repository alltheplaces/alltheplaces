from typing import Any, Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsZASpider(PlaywrightSpider):
    name = "mcdonalds_za"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.co.za/templates/_layout/ajax_calls/get_all_locations.php?lat=0&long=0"]
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT, "ROBOTSTXT_OBEY": False} | DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//div[@class="store_listing_con"]'):
            item = Feature()
            item["website"] = location.xpath(".//a/@href").get("")
            item["ref"] = item["website"].split("/location/")[-1].strip()

            if item["website"] == "https://www.mcdonalds.co.za/location/mcdonalds-head-office":
                continue

            item["branch"] = location.xpath(".//h5/text()").get("").removeprefix("McDonald's ")
            item["addr_full"] = location.xpath(".//p/text()").get()
            item["phone"] = (
                location.xpath('.//span[contains(., "Contact Number:")]/text()')
                .get()
                .replace("Contact Number:", "")
                .strip()
            )
            item["email"] = location.xpath('.//span[contains(., "Email:")]/text()').get().replace("Email:", "").strip()

            apply_category(Categories.FAST_FOOD, item)

            yield Request(
                url=f'https://www.mcdonalds.co.za/templates/_layout/ajax_calls/get_location_details.php?id={item["ref"]}',
                cb_kwargs=dict(item=item),
                callback=self.parse_opening_hours,
            )

    def parse_opening_hours(self, response: Response, item: Feature) -> Iterable[Feature]:
        item["opening_hours"] = OpeningHours()
        if response.xpath('//img[contains(@src, "McDonalds-open-247")]').get(""):
            item["opening_hours"] = "24/7"
        else:
            for rule in response.xpath('//*[contains(text(), "Opening Hours")]/following-sibling::span'):
                day = rule.xpath("./strong/text()").get("")
                hours = rule.xpath("./text()").get("").replace("24 hours", "00:00-23:59")
                item["opening_hours"].add_ranges_from_string(f"{day} {hours}")
        yield item
