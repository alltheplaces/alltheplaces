# -*- coding: utf-8 -*-
import json

import scrapy

from locations.items import GeojsonPointItem


class WorldcatSpider(scrapy.Spider):
    name = "worldcat"
    allowed_domains = ["worldcat.org"]
    download_delay = 0.5

    def get_page(self, offset):
        return scrapy.Request(
            f"https://worldcat.org/webservices/registry/find?oclcAccountName=+&institutionAlias=&instType=&country=&city=&subdivision=&postalCode=&regID=&oclcSymbol=&ISIL=&marcOrgCode=&blCode=&searchTermSet=1&getData=getData&offset={offset}",
            meta={"offset": offset},
        )

    def start_requests(self):
        yield self.get_page(1)

    def parse(self, response):
        data = response.json()
        if data == []:
            return
        for row in data:
            inst_id = row["inst_id"]
            yield scrapy.Request(
                f"https://worldcat.org/webservices/registry/Institutions/{inst_id}",
                callback=self.parse_library,
            )

        yield self.get_page(1 + response.meta["offset"])

    def parse_library(self, response):
        script = response.xpath('//script/text()[contains(., "var JSON_Obj")]').get()
        data = json.decoder.JSONDecoder().raw_decode(
            script, script.index("{", script.index("var JSON_Obj"))
        )[0]

        if "addresses" not in data:
            # No physical description, possibly related to another institution but that
            # doesn't concern us here.
            return

        geo_address = next(
            (
                addr
                for addr in data["addresses"]
                if {"latitude", "longitude"} <= addr.keys()
            ),
            {},
        )

        if not geo_address:
            # No coordinates given in any of the addresses, omit it
            return

        # We have coordinates, all other data should be optional

        street_address = next(
            (addr for addr in data["addresses"] if {"city"} <= addr.keys()), {}
        )

        properties = {
            "ref": response.url,
            "lat": geo_address["latitude"],
            "lon": geo_address["longitude"],
            "name": data["name"],
            "phone": data.get("phoneNumber"),
            "extras": {"fax": data.get("faxNumber")},
            "website": data.get("instURL", [{}])[0].get("instURL"),
            "street_address": street_address.get("street1"),
            "city": street_address.get("city"),
            "state": street_address.get("subdivisionDescription"),
            "postcode": street_address.get("postalCode"),
            "country": street_address.get("countryDescription"),
        }
        yield GeojsonPointItem(**properties)
