import json
import math

import scrapy
from scrapy.downloadermiddlewares.retry import get_retry_request

from locations.categories import Categories, apply_category
from locations.items import Feature


class WorldcatSpider(scrapy.Spider):
    name = "worldcat"
    allowed_domains = ["worldcat.org"]
    download_delay = 0.5
    requires_proxy = True

    def get_page(self, offset):
        return scrapy.Request(
            # This URL returns JSON array
            f"https://worldcat.org/webservices/registry/find?oclcAccountName=+&institutionAlias=&instType=&country=&city=&subdivision=&postalCode=&regID=&oclcSymbol=&ISIL=&marcOrgCode=&blCode=&searchTermSet=1&getData=getData&offset={offset}",
            meta={"offset": offset},
        )

    def start_requests(self):
        yield scrapy.Request(
            # This URL returns HTML search page
            "https://www.worldcat.org/webservices/registry/find?oclcAccountName=+&institutionAlias=&instType=&country=&city=&subdivision=&postalCode=&regID=&oclcSymbol=&ISIL=&marcOrgCode=&blCode=&offset=0&searchTermSet=1",
            callback=self.parse_search_page,
        )

    def parse_search_page(self, response):
        total_records = int(response.xpath("//script/text()").re_first(r"var totalRecords = '(\d+)'"))
        total_pages = math.ceil(total_records / 10)
        for i in range(1, total_pages + 1):
            yield self.get_page(i)

    def parse(self, response):
        data = response.json()
        if data == []:
            # Seems to sometimes return empty array as a transient error,
            # let's call their bluff to see if that's actually the end.
            yield get_retry_request(response.request, spider=self, reason="empty array")
            return
        for row in data:
            inst_id = row["inst_id"]
            yield scrapy.Request(
                f"https://worldcat.org/webservices/registry/Institutions/{inst_id}",
                callback=self.parse_library,
            )

    def parse_library(self, response):
        script = response.xpath('//script/text()[contains(., "var JSON_Obj")]').get()
        data = json.decoder.JSONDecoder().raw_decode(script, script.index("{", script.index("var JSON_Obj")))[0]

        if "addresses" not in data:
            # No physical description, possibly related to another institution but that
            # doesn't concern us here.
            return

        geo_address = next(
            (addr for addr in data["addresses"] if {"latitude", "longitude"} <= addr.keys()),
            {},
        )

        if not geo_address:
            # No coordinates given in any of the addresses, omit it
            return

        # We have coordinates, all other data should be optional

        street_address = next((addr for addr in data["addresses"] if {"city"} <= addr.keys()), {})

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
        item = Feature(**properties)
        apply_category(Categories.LIBRARY, item)
        yield item
