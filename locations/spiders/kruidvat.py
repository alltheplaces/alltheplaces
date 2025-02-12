from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class KruidvatSpider(scrapy.Spider):
    name = "kruidvat"
    item_attributes = {"brand": "Kruidvat", "brand_wikidata": "Q2226366"}
    start_urls = [
        "https://www.kruidvat.be/api/v2/kvb/stores?lang=nl_BE&radius=100000&pageSize=10000&fields=FULL",
        "https://www.kruidvat.nl/api/v2/kvn/stores?lang=nl&radius=100000&pageSize=10000&fields=FULL",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.xpath("//stores"):
            item = Feature()
            item["ref"] = store.xpath("code/text()").get()

            if item["ref"] == "8000":
                continue

            item["state"] = store.xpath(".//province/text()").get()
            item["postcode"] = store.xpath(".//postalCode/text()").get()
            item["street"] = store.xpath(".//line1/text()").get()
            item["lat"] = store.xpath(".//latitude/text()").get()
            item["lon"] = store.xpath(".//longitude/text()").get()
            item["addr_full"] = store.xpath(".//formattedAddress/text()").get()

            item["opening_hours"] = OpeningHours()
            for rule in store.xpath(".//weekDayOpeningList"):
                if rule.xpath("./closed/text()").get() == "true":
                    continue
                item["opening_hours"].add_range(
                    rule.xpath("shortenedWeekDay/text()").get(),
                    rule.xpath("openingTime/formattedHour/text()").get(),
                    rule.xpath("closingTime/formattedHour/text()").get(),
                )

            item["website"] = response.urljoin(store.xpath("url/text()").get())

            apply_category(Categories.SHOP_CHEMIST, item)

            yield item
