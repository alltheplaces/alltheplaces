import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.geo import point_locations
from locations.linked_data_parser import LinkedDataParser
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class SwarovskiUSSpider(Spider):
    name = "swarovski_us"
    item_attributes = {"brand": "Swarovski", "brand_wikidata": "Q611115"}
    allowed_domains = ["swarovski.com"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"USER_AGENT": BROWSER_DEFAULT}

    async def start(self) -> AsyncIterator[Request]:
        point_files = "us_centroids_100mile_radius_state.csv"
        for lat, lon in point_locations(point_files):
            yield Request(
                url=f"https://www.swarovski.com/en-LU/store-finder/stores/?geoPoint.latitude={lat}&geoPoint.longitude={lon}&provider=GOOGLE&allBaseStores=true&radius=120&clientTimeZoneOffset=-60",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if response.xpath('//div[contains(text(), "stores")]/text()').get():
            for store in response.xpath(
                '//div[@id="swa-store-locator__tab-list"]/div[contains(@class,"swa-store-view__store")]'
            ):
                url = store.xpath('.//a[contains(@href, "store")]/@href').get()
                yield Request(
                    url=f"https://www.{self.allowed_domains[0]}{url}",
                    callback=self.parse_store,
                    cb_kwargs={
                        "lat": store.xpath("./@data-latitude").get(),
                        "lon": store.xpath("./@data-longitude").get(),
                    },
                )

    def parse_store(self, response: Response, lat: str, lon: str) -> Any:
        type_store = response.xpath('//span[@class="swa-headlines__subheadline swa-label-sans--medium"]/text()').get()
        if not type_store:
            item = LinkedDataParser.parse(response, "Store")
            item["ref"] = re.findall("[0-9]+", response.url)[0]
            item["lat"] = lat
            item["lon"] = lon
            item["addr_full"] = item.pop("street_address").replace("<br>", "")

            yield item
