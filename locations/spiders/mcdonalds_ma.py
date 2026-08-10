from typing import Any

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsMASpider(PlaywrightSpider):
    name = "mcdonalds_ma"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.ma"]
    start_urls = ["https://www.mcdonalds.ma/nos-restaurants"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="gridRestaurants"]//*[@data-services]'):
            item = Feature()
            item["branch"] = (
                location.xpath('.//*[@class="title"]/text()').get("").strip().removeprefix("Restaurant McDonald's ")
            )
            item["addr_full"] = location.xpath('.//*[@class="adress"]/text()').get("")

            services = [service.strip().lower() for service in location.xpath("./@data-services").get("").split(",")]

            if "mccafe" in services:
                mccafe = item.deepcopy()
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                yield mccafe

            apply_yes_no(Extras.WIFI, item, "wifi" in services)
            apply_yes_no(Extras.OUTDOOR_SEATING, item, "terrasse" in services)
            apply_yes_no(Extras.DELIVERY, item, "mcdelivery" in services)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "mcdrive" in services)

            yield item
