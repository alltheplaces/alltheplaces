import re
import json

import scrapy
from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROSWER_DEFAULT


class GreyhoundSpider(SitemapSpider):
    name = "greyhound"
    item_attributes = {"brand": "Greyhound", "brand_wikidata": "Q755309"}
    allowed_domains = ["greyhound.com", "openair-california.airtrfx.com"]
    sitemap_urls = ["https://www.greyhound.com/en-us/sitemap43.xml"]
    sitemap_rules = [(r"/bus-station-[0-9]+", "parse")]
    user_agent = BROSWER_DEFAULT

    def parse(self, response):
        url = "https://openair-california.airtrfx.com/hangar-service/v2/ghl/airports/search"
        payload = {
            "outputFields": ["name", "extraInfo", "city", "state", "iataCode"],
            "sortingDetails": [{"field": "popularity", "order": "DESC"}],
            "filterFields": [{"name": "active", "values": ["true"]}, {"name": "iataCode"}],
            "setting": {"airportSource": "TRFX", "routeSource": "TRFX"},
            "from": 0,
            "size": 40,
            "language": "en",
        }
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://www.greyhound.com",
            "User-Agent": BROSWER_DEFAULT,
            "em-api-key": "HeQpRjsFI5xlAaSx2onkjc1HTK0ukqA1IrVvd5fvaMhNtzLTxInTpeYB1MK93pah",
        }
        station_id = re.findall("[0-9]+", response.url)[0]
        payload.get("filterFields")[1].update({"values": [station_id]})

        yield scrapy.Request(
            url=url, method="POST", body=json.dumps(payload), headers=headers, callback=self.parse_station
        )

    def parse_station(self, response):
        if not response.json():
            return
        data = response.json()[0]
        item = DictParser.parse(data.get("extraInfo", {}).get("address"))
        item["state"] = data.get("state", {}).get("identifierCode")
        item["name"] = data.get("name")
        item["phone"] = data.get("extraInfo", {}).get("metaData", {}).get("phoneNumbers", {}).get("phoneNumber")
        item["ref"] = data.get("iataCode")
        item["website"] = f'https://www.greyhound.com/en-us/bus-station-{item["ref"]}'
        item["street_address"] = item.pop("street")
        item["city"] = data.get("extraInfo", {}).get("address", {}).get("cityName")
        oh = OpeningHours()
        for day, value in (
            data.get("extraInfo", {}).get("metaData", {}).get("hours", {}).get("hoursBusStation", {}).items()
        ):
            if value:
                oh.add_range(
                    day=DAYS[int(day) - 1],
                    open_time=value[0].get("open").replace(" ", ""),
                    close_time=value[0].get("close").replace(" ", ""),
                    time_format="%I:%M%p",
                )
        item["opening_hours"] = oh.as_opening_hours()

        yield item
