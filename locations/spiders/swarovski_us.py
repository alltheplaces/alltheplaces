import re

import scrapy

from locations.geo import point_locations
from locations.linked_data_parser import LinkedDataParser
from locations.user_agents import BROWSER_DEFAULT


class SwarovskiUSSpider(scrapy.Spider):
    name = "swarovski_us"
    item_attributes = {"brand": "Swarovski", "brand_wikidata": "Q611115"}
    allowed_domains = ["swarovski.com"]
    headers = {"User-Agent": BROWSER_DEFAULT}

    def start_requests(self):
        point_files = "us_centroids_100mile_radius_state.csv"
        for lat, lon in point_locations(point_files):
            url = f"https://www.swarovski.com/en-LU/store-finder/stores/?geoPoint.latitude={lat}&geoPoint.longitude={lon}&provider=GOOGLE&allBaseStores=true&radius=120&clientTimeZoneOffset=-60"
            yield scrapy.Request(url=url, headers=self.headers)

    def parse(self, response):
        if response.xpath('//div[contains(text(), "stores")]/text()').get():
            stores = response.xpath(
                '//div[@id="swa-store-locator__tab-list"]/div[contains(@class,"swa-store-view__store")]'
            )
            for store in stores:
                coords = {"lat": store.xpath("./@data-latitude").get(), "lon": store.xpath("./@data-longitude").get()}
                url = store.xpath('.//a[contains(@href, "store")]/@href').get()
                yield scrapy.Request(
                    url=f"https://www.{self.allowed_domains[0]}{url}",
                    headers=self.headers,
                    callback=self.parse_store,
                    cb_kwargs={"coords": coords},
                )

    def parse_store(self, response, coords):
        type_store = response.xpath('//span[@class="swa-headlines__subheadline swa-label-sans--medium"]/text()').get()
        if not type_store:
            item = LinkedDataParser.parse(response, "Store")
            item["ref"] = re.findall("[0-9]+", response.url)[0]
            item["lat"] = coords.get("lat")
            item["lon"] = coords.get("lon")
            item["addr_full"] = item.pop("street_address").replace("<br>", "")

            yield item
