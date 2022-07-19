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
            if ld["geo"].get("@type") in (
                "GeoCoordinates",
                "http://schema.org/GeoCoordinates",
                "https://schema.org/GeoCoordinates",
            ):
                item["lat"] = ld["geo"].get("latitude")
                item["lon"] = ld["geo"].get("longitude")

        item["name"] = ld.get("name")

        if ld.get("address"):
            addr = ld["address"]
            if isinstance(addr, str):
                item["addr_full"] = addr
            elif addr.get("@type") == "PostalAddress":
                item["street_address"] = addr.get("streetAddress") or addr.get(
                    "streetaddress"
                )
                item["city"] = addr.get("addressLocality") or addr.get(
                    "addresslocality"
                )
                item["state"] = addr.get("addressRegion") or addr.get("addressregion")
                item["postcode"] = addr.get("postalCode") or addr.get("postalcode")
                item["country"] = addr.get("addressCountry") or addr.get(
                    "addresscountry"
                )

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
