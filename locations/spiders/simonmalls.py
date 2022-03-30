# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem


class SimonMallsSpider(scrapy.Spider):
    download_delay = 0.2
    name = "simonmalls"
    item_attributes = {"brand": "Simon Malls"}
    allowed_domains = ["simon.com"]
    start_urls = ("https://api.simon.com/v1.2/centers/all/index",)

    def parse(self, response):
        base_url = "https://www.simon.com/mall/"

        # build store urls
        jsonresponse = response.json()
        for stores in jsonresponse:
            store = json.dumps(stores)
            store_data = json.loads(store)
            store_name = store_data["urlFriendlyName"]
            if store_data["address"]["country"] != "UNITED STATES":
                pass
            elif store_data["urlFriendlyName"] == "one-phipps-plaza":
                # skip does not have a store page
                pass
            else:
                store_url = base_url + store_name
                yield scrapy.Request(
                    store_url,
                    callback=self.parse_store,
                    meta={
                        "country": store_data["address"]["country"],
                        "phone": store_data["mallPhone"],
                        "location_type": store_data["propertyType"],
                    },
                )

    def parse_store(self, response):
        extracted_script = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "FullAddress")]/text()'
        ).extract_first()
        if extracted_script is None:
            pass
        else:
            store_data = json.loads(
                re.search(r"var mallObj =(.*)", extracted_script).group(1)
            )

            properties = {
                "name": store_data["DisplayName"].replace("\u00ae", " ").strip(" "),
                "ref": store_data["Id"],
                "addr_full": store_data["FullAddress"],
                "city": store_data["City"],
                "state": store_data["StateCode"],
                "postcode": store_data["ZipCode"],
                "country": response.meta["country"],
                "phone": response.meta["phone"],
                "website": response.url,
                "lat": float(store_data["Latitude"]),
                "lon": float(store_data["Longitude"]),
                "extras": {"location_type": response.meta["location_type"]},
            }
            yield GeojsonPointItem(**properties)
