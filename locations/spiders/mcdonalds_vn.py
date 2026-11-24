from typing import Any

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.user_agents import BROWSER_DEFAULT


class McdonaldsVNSpider(PlaywrightSpider):
    name = "mcdonalds_vn"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.vn/restaurants.html"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[contains(@class,"tbox-address-store")]'):
            item = Feature()
            item["ref"] = location.xpath("@id").get()
            item["branch"] = (
                location.xpath('./p[@class="tname-store"]/text()')
                .get("")
                .removeprefix("McDonald's ")
                .removeprefix("McDonald’s ")
            )
            item["addr_full"] = location.xpath('./p[@class="ttitle"][contains(., "Address:")]/span/text()').get()
            item["phone"] = location.xpath('/p[@class="ttitle"][contains(., "Phone:")]/span/text()').get()
            item["lat"], item["lon"] = url_to_coords(location.xpath('.//a[@class="location-web"]/@href').get())

            apply_category(Categories.FAST_FOOD, item)

            yield item
