import html
import re
from typing import Any, AsyncIterator

from chompjs import parse_js_object
from scrapy import FormRequest, Selector
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import extract_email


class HobbytownUSSpider(PlaywrightSpider):
    name = "hobbytown_us"
    item_attributes = {"brand": "HobbyTown", "brand_wikidata": "Q5874921"}
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    async def start(self) -> AsyncIterator[Any]:
        yield FormRequest(
            "https://www.hobbytown.com/ajax/store-locations/store-list",
            formdata={"zip": "90210", "pageType": "StoreLocator", "searchRadius": "3000", "productID": "0"},
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in parse_js_object(
            re.search(
                r"locations: (\[\[.+?]],)", response.xpath("//script[contains(text(), 'locations')]/text()").get()
            ).group(1)
        ):
            item = Feature()
            item["lat"] = location[0]
            item["lon"] = location[1]
            item["ref"] = location[3]
            item["website"] = response.urljoin(
                response.xpath('//*[@data-store-id="{}"]//a[@title="Store Profile"]/@href'.format(item["ref"])).get()
            )

            sel = Selector(text=html.unescape(location[2]))
            item["branch"] = sel.xpath("//strong/text()").get().removeprefix("HobbyTown ")
            addr = sel.xpath("//body/text()").getall()
            item["addr_full"] = merge_address_lines(addr[:2])
            if len(addr) == 3:
                item["phone"] = addr[2]

            extract_email(item, sel)
            apply_category(Categories.SHOP_CRAFT, item)

            yield item
