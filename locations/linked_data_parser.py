import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class LinkedDataParser(object):
    @staticmethod
    def find_linked_data(response, wanted_type) -> {}:
        lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
        for ld in lds:
            ld_obj = json.loads(ld)

            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            if wanted_type in types:
                return ld_obj

    @staticmethod
    def parse_ld(ld) -> GeojsonPointItem:
        item = GeojsonPointItem()

        if ld.get("geo"):
            if ld["geo"].get("@type") == "GeoCoordinates":
                item["lat"] = ld["geo"].get("latitude")
                item["lon"] = ld["geo"].get("longitude")

        item["name"] = ld.get("name")

        if ld.get("address"):
            if isinstance(ld["address"], str):
                item["addr_full"] = ld["address"]
            elif ld["address"].get("@type") == "PostalAddress":
                item["street_address"] = ld["address"].get("streetAddress")
                item["city"] = ld["address"].get("addressLocality") or ld["address"].get("addresslocality")
                item["state"] = ld["address"].get("addressRegion") or ld["address"].get("addressregion")
                item["postcode"] = ld["address"].get("postalCode")
                item["country"] = ld["address"].get("addressCountry")

        item["phone"] = ld.get("telephone")
        item["website"] = ld.get("url")

        oh = OpeningHours()
        oh.from_linked_data(ld)
        item["opening_hours"] = oh.as_opening_hours()

        if ld.get("image"):
            if isinstance(ld["image"], str):
                item["image"] = ld["image"]
            elif ld["image"].get("@type") == "ImageObject":
                item["image"] = ld["image"].get("contentUrl")

        item["ref"] = ld.get("branchCode")

        if item["ref"] is None:
            item["ref"] = ld.get("@id")

        if ld.get("brand"):
            if isinstance(ld["brand"], str):
                item["brand"] = ld["brand"]
            elif (
                ld["brand"].get("@type") == "Brand"
                or ld["brand"].get("@type") == "Organization"
            ):
                item["brand"] = ld["brand"].get("name")

        return item

    @staticmethod
    def parse(response, wanted_type) -> GeojsonPointItem:
        ld_item = LinkedDataParser.find_linked_data(response, wanted_type)

        if ld_item:
            item = LinkedDataParser.parse_ld(ld_item)

            if item["website"] is None:
                item["website"] = response.url

            return item
