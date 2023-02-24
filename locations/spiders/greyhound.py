import json
import re

import scrapy
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class GreyhoundSpider(SitemapSpider):
    name = "greyhound"
    item_attributes = {"brand": "Greyhound", "brand_wikidata": "Q755309"}
    allowed_domains = ["greyhound.com", "openair-california.airtrfx.com"]
    sitemap_urls = ["https://www.greyhound.com/robots.txt"]
    sitemap_rules = [(r"/bus-station-[0-9]+", "parse")]
    user_agent = BROWSER_DEFAULT

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
            "User-Agent": BROWSER_DEFAULT,
            "em-api-key": "HeQpRjsFI5xlAaSx2onkjc1HTK0ukqA1IrVvd5fvaMhNtzLTxInTpeYB1MK93pah",
        }
        try:
            ref = re.findall("[0-9]+", response.url)[0]
            station_id = re.findall(r"user_input_origin_airport_code\":\"([a-z0-9\-]*)\"", response.text)[0]
        except IndexError:
            return

        payload.get("filterFields")[1].update({"values": [station_id]})

        yield scrapy.Request(
            url=url,
            method="POST",
            body=(json.dumps(payload)),
            headers=headers,
            callback=self.parse_station,
            cb_kwargs={"ref": ref},
        )

    def parse_station(self, response, ref):
        if not response.json():
            return
        data = response.json()[0]

        item = DictParser.parse(data.get("extraInfo", {}).get("address"))
        item["state"] = data.get("state", {}).get("identifierCode")
        item["name"] = data.get("name")
        item["phone"] = data.get("extraInfo", {}).get("metaData", {}).get("phoneNumbers", {}).get("phoneNumber")
        item["ref"] = ref
        item["website"] = f"https://www.greyhound.com/en-us/bus-station-{ref}"
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
        item["extras"] = {"iataCode": data.get("iataCode")}

        apply_category(Categories.BUS_STATION, item)

        yield item
