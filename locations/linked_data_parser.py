import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class LinkedDataParser(object):
    @staticmethod
    def iter_linked_data(response):
        lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
        for ld in lds:
            try:
                ld_obj = json.loads(ld, strict=False)
            except json.decoder.JSONDecodeError:
                continue

            if isinstance(ld_obj, dict):
                if "@graph" in ld_obj:
                    yield from ld_obj["@graph"]
                else:
                    yield ld_obj
            elif isinstance(ld_obj, list):
                yield from ld_obj
            else:
                raise TypeError(ld_obj)

    @staticmethod
    def find_linked_data(response, wanted_type) -> {}:
        for ld_obj in LinkedDataParser.iter_linked_data(response):
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
            if isinstance(addr, list):
                addr = addr[0]
            if isinstance(addr, str):
                item["addr_full"] = addr
            else:
                # We do not check for "@type" being "PostalAddress", some sites fail
                # to specify this and since it is unlikely to be anything else we do not
                # perform the check.
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
                item["phone"] = addr.get("telephone")

        item["phone"] = ld.get("telephone").strip()
        item["website"] = ld.get("url")

        try:
            oh = OpeningHours()
            oh.from_linked_data(ld)
            item["opening_hours"] = oh.as_opening_hours()
        except:
            pass

        if ld.get("image"):
            if isinstance(ld["image"], str):
                item["image"] = ld["image"]
            elif isinstance(ld["image"], list):
                item["image"] = ld["image"][0]
            elif ld["image"].get("@type") == "ImageObject":
                item["image"] = ld["image"].get("contentUrl")

        item["ref"] = ld.get("branchCode")

        if item["ref"] is None:
            item["ref"] = ld.get("@id")

        return item

    @staticmethod
    def parse(response, wanted_type) -> GeojsonPointItem:
        ld_item = LinkedDataParser.find_linked_data(response, wanted_type)

        if ld_item:
            item = LinkedDataParser.parse_ld(ld_item)

            if item["website"] is None:
                item["website"] = response.url
            elif item["website"] == "":
                item["website"] = response.url
            elif item["website"][0] == "/":
                item["website"] = response.url
            elif item["website"].startswith("www"):
                item["website"] = "https://" + item["website"]

            return item
