import json
from typing import Iterable
from urllib.parse import urlencode

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Request, Response

from locations.country_utils import CountryUtils, get_locale
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.subway import SubwaySpider


class SubwayWorldwideSpider(Spider):
    """
    This API should have most of the Subway locations worldwide. The only con is the API is coordinate-based.
    Full list of countries: https://www.subway.com/es-CO/ExploreOurWorld
    """

    item_attributes = SubwaySpider.item_attributes
    country_utils = CountryUtils()

    def start_requests(self) -> Iterable[Request]:
        country = self.country_utils.country_code_from_spider_name(self.name)
        language = get_locale(country) or "en-US"
        for city in city_locations(country, 1000):
            lat, lon = city["latitude"], city["longitude"]
            yield self.make_request(lat, lon, country, 1, language)

    def make_request(self, lat, lon, country_code: str, start_index: int, language: str) -> Request:
        q = {
            "InputText": "",
            "GeoCode": {"Latitude": lat, "Longitude": lon, "CountryCode": country_code, "City": ""},
            "DetectedLocation": {"Latitude": 0, "Longitude": 0, "Accuracy": 0},
            "Paging": {"StartIndex": start_index, "PageSize": 50},
            "ConsumerParameters": {
                "metric": True,
                "culture": language,
                "country": country_code,
                "size": "D",
                "template": "",
                "rtl": False,
                "clientId": "17",
                "key": "SUBWAY_PROD",
            },
            "Filters": [],
            "LocationType": 2,
            "behavior": "",
            "FavoriteStores": None,
            "RecentStores": None,
            "Stats": {"abc": "geo,A", "src": "geocode", "act": "enter", "c": "subwayLocator", "pac": "8,2"},
        }
        q = json.dumps(q)
        url = "https://locator-svc.subway.com/v3/GetLocations.ashx?" + urlencode({"q": q})
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
        data = chompjs.parse_js_object(response.text)

        paging_html = Selector(text=data["PagingHtml"])
        pages = paging_html.xpath('//span[@class="locatorResultsPaging"]/text()').get(default="")
        pages = pages.replace("Page", "").replace("of", "/").replace(" ", "")
        current, total = pages.split("/")

        for poi in data.get("ResultData", []):
            address = poi.get("Address", {})
            if address.get("CountryCode", "").upper() != response.meta["country_code"]:
                # API can give POIs for nearby countries, filter them out for less confusion
                # TODO: revisit this at some point?
                continue
            item = DictParser.parse(poi)
            item["ref"] = poi["LocationId"]["StoreNumber"]
            item["street_address"] = clean_address(
                [address.get("Address1"), address.get("Address2"), address.get("Address3")]
            )
            yield item

        if int(current) < int(total):
            yield self.make_request(
                response.meta["lat"],
                response.meta["lon"],
                response.meta["country_code"],
                int(current) + 1,
                response.meta["language"],
            )


class SubwayTHSpider(SubwayWorldwideSpider):
    name = "subway_th"


# TODO: spiders for other countries
