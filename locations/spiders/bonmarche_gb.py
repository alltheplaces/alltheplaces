import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.country_utils import CountryUtils
from locations.geo import city_locations
from locations.items import Feature


class BonmarcheGBSpider(Spider):
    name = "bonmarche_gb"
    item_attributes = {"brand": "Bonmarche", "brand_wikidata": "Q4942146"}
    country_utils = CountryUtils()

    def start_requests(self) -> Iterable[Request]:
        country = "GB"
        language = "en-GB"
        for city in city_locations("GB", 1000):
            lat, lon = city["latitude"], city["longitude"]
            yield self.make_request(lat, lon, country, 1, language)

    def make_request(self, lat, lon, country_code: str, start_index: int, language: str) -> Request:
        url = f"https://www.bonmarche.co.uk/on/demandware.store/Sites-BONMARCHE-GB-Site/en_GB/Stores-FindStores?lat={lat}&lng={lon}&dwfrm_storelocator_findbygeocoord=Search&format=ajax&amountStoresToRender=5&checkout=false"
        return Request(
            url,
            meta={
                "lat": lat,
                "lon": lon,
                "country_code": country_code,
                "start_index": start_index,
                "language": language,
            },
            callback=self.parse,
        )

    def parse(self, response: Response) -> Iterable[Feature]:
        try:
            geodata = response.xpath('//div[@id="map"]//@data-results').get()
            geo = json.loads(geodata)
        except Exception as e:
            self.logger.warning(f"Failed to parse geodata: {geodata}, {e}")
        data = response.xpath('//li[@class="stores-list-item"]')
        for location in data:
            item = Feature()
            item["addr_full"] = location.xpath('//div[@class="store-address"]').get()
            item["phone"] = location.xpath('//a/href[contains(text,"tel:")]').get()
            item["ref"] = location.xpath("//a//@data-storeid").get()
            for store in geo["stores"]:
                if store["id"] == item["ref"]:
                    item["lat"] = store["lat"]
                    item["lon"] = store["lng"]

            yield item
