import scrapy
import json
import re

from locations.items import GeojsonPointItem


class ExtraSpaceStorageSpider(scrapy.Spider):
    name = "extra_space_storage"
    item_attributes = {"brand": "Extra Space Storage"}
    allowed_domains = ["www.extraspace.com"]
    start_urls = ("https://www.extraspace.com/sitemap_sites.aspx",)

    def parse(self, response):
        response.selector.remove_namespaces()
        store_urls = response.xpath("//url/loc/text()").extract()
        regex = re.compile(r"https://www.extraspace.com/\S+")
        for path in store_urls:
            if re.search(regex, path):
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
            else:
                pass

    def parse_store(self, response):
        data = self.get_json_data(response)
        if not data:
            # The sitemap may include some URLs that do not provide details of individual stores
            return

        data_address = data["address"]
        data_geo = data["geo"]

        if not data_address or not data_geo:
            return

        properties = {
            # The Site Number does not appear in JSON but it is displayed on the page.
            "ref": response.xpath('//*/span[@id="site-number"]/text()').get(),
            "name": data["name"],
            "addr_full": data_address["streetAddress"],
            "city": data_address["addressLocality"],
            "state": data_address["addressRegion"],
            "postcode": data_address["postalCode"],
            "lon": float(data_geo["longitude"]),
            "lat": float(data_geo["latitude"]),
            "phone": data["telephone"],
            "website": data["url"],
        }

        opening_hours_list = data["openingHours"]
        if isinstance(opening_hours_list, list) and len(opening_hours_list) > 0:
            # Opening hours are already in OpenStreetMap format but each ruleset appears as a separate array
            # element in JSON.
            opening_hours = "; ".join(opening_hours_list)
            properties["opening_hours"] = opening_hours

        yield GeojsonPointItem(**properties)

    def get_json_data(self, response):
        # The pages for each location include JSON data in several <script /> blocks.
        # The metadata for the location is in the block that follows the SelfStorage
        # schema (see http://schema.org/SelfStorage).
        all_ldjson = response.xpath('//*/script[@type="application/ld+json"]/text()')
        for ldjson in all_ldjson:
            data = json.loads(ldjson.get())
            if data["@type"] == "SelfStorage":
                return data

        return
