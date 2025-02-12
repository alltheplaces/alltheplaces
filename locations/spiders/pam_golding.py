import re

from scrapy import Spider
from scrapy.http import JsonRequest
from scrapy.linkextractors import LinkExtractor

from locations.hours import OpeningHours
from locations.items import Feature


class PamGoldingSpider(Spider):
    name = "pam_golding"
    item_attributes = {
        "brand": "Pam Golding Properties",
        "brand_wikidata": "Q65051429",
    }
    start_urls = [
        "https://www.pamgolding.co.za/contact-us/offices",
        "https://www.pamgolding.co.za/contact-us/international-offices",
    ]

    def parse(self, response):
        links = LinkExtractor(
            allow=r"^https:\/\/www\.pamgolding\.co\.za\/contact-us\/office-details/.+/\d+$"
        ).extract_links(response)
        for link in links:
            ref = re.sub(r"^https:\/\/www\.pamgolding\.co\.za\/contact-us\/office-details/.+/(\d+)$", r"\1", link.url)
            json_url = f"https://www.pamgolding.co.za/customapi/ContactUs/GetOfficeById/{ref}"
            yield JsonRequest(url=json_url, callback=self.parse_item, meta={"ref": ref, "website": link.url})

    def parse_item(self, response):
        location = response.json()
        item = Feature()

        item["ref"] = response.meta["ref"]
        item["website"] = response.meta["website"]
        item["lat"] = location.get("decLatitude")
        item["lon"] = location.get("decLongitude")

        item["branch"] = location.get("nvcName")
        item["email"] = location.get("nvcEmailAddress")
        item["phone"] = location.get("nvcTelephoneNumber")
        item["extras"]["fax"] = location.get("nvcFaxNumber")

        address = location.get("dtlAddress")
        item["addr_full"] = address.get("nvcSingleLineDisplayAddress")
        item["housenumber"] = address.get("nvcStreetNumber")
        item["street"] = address.get("nvcStreetName")
        item["postcode"] = address.get("nvcPostalCode")
        item["city"] = address.get("nvcCity")
        item["state"] = address.get("nvcProvince")
        item["country"] = address.get("nvcCountry")

        item["opening_hours"] = OpeningHours()
        for day in location["dtlOfficeOperatingTimes"]:
            if day["bitIsActive"]:
                item["opening_hours"].add_ranges_from_string(
                    day["refOperatingTimeType"]["nvcOperatingTImeType"]
                    + " "
                    + day["tmeOpeningTime"]
                    + " - "
                    + day["tmeClosingTime"]
                )
            else:
                try:
                    item["opening_hours"].set_closed(day["refOperatingTimeType"]["nvcOperatingTImeType"])
                except ValueError:
                    pass

        yield item
