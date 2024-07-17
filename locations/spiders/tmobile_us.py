from typing import Iterator
from urllib.parse import urlencode, urljoin

import scrapy
from scrapy.http import Request, Response

from locations.dict_parser import DictParser
from locations.geo import point_locations
from locations.hours import OpeningHours
from locations.items import Feature

BASE_URL = "https://www.t-mobile.com/stores/api/get-nearby-business/?"


class TMobileUSSpider(scrapy.Spider):
    name = "tmobile_us"
    item_attributes = {
        "brand": "T-Mobile",
        "brand_wikidata": "Q3511885",
    }
    allowed_domains = ["www.t-mobile.com"]
    download_delay = 0.5

    def start_requests(self) -> Iterator[Request]:
        for lat, lon in point_locations(
            "us_centroids_25mile_radius_state.csv",
        ):
            params = {
                "INTNAV": "tNav:StoreLocator",
                "lat": "{}".format(lat),
                "lon": "{}".format(lon),
                "showall": "false",
            }

            yield self.do_request(BASE_URL, params)

    def do_request(self, url, params) -> Request:
        return Request(url + urlencode(params), callback=self.parse, meta=params)

    def parse(self, response: Response, **kwargs) -> Iterator[Feature] | Iterator[Request]:
        data = response.json()

        for poi in data.get("business_list", {}).get("object_list", []):
            item = DictParser.parse(poi)
            item["addr_full"] = " ".join(poi.get("address_text_lines", []))
            item["state"] = poi.get("locale", {}).get("region", {}).get("state")
            item["website"] = item["ref"] = urljoin("https://www.t-mobile.com/", poi["business_link"])
            self.parse_hours(item, poi)
            yield item

        if next_page := data.get("business_list", {}).get("next_page_number"):
            params = response.meta
            params["page"] = next_page
            yield self.do_request(BASE_URL, params)

    def parse_hours(self, item: Feature, poi: dict):
        hours = poi.get("all_opening_hours", {}).get("schemaHrs", [])
        if not hours:
            return
        try:
            oh = OpeningHours()
            for hour in hours:
                day, time = hour.split(" ")
                time_open, time_close = time.split("-")
                oh.add_range(day, time_open, time_close)
            item["opening_hours"] = oh.as_opening_hours()
        except Exception as e:
            self.logger.warning(f"Failed to parse hours {hours}: {e}")
            self.crawler.stats.inc_value(f"atp/{self.name}/hours/failed")
