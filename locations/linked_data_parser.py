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

        if (
            (geo := ld.get("geo"))
            or "location" in ld
            and (geo := ld["location"].get("geo"))
        ):
            if isinstance(geo, list):
                geo = geo[0]

            if geo.get("@type", "GeoCoordinates") in (
                "GeoCoordinates",
                "http://schema.org/GeoCoordinates",
                "https://schema.org/GeoCoordinates",
            ):
                item["lat"] = geo.get("latitude")
                item["lon"] = geo.get("longitude")

        item["name"] = LinkedDataParser.get_clean(ld, "name")

        if addr := LinkedDataParser.get_clean(ld, "address"):
            if isinstance(addr, list):
                addr = addr[0]

            if isinstance(addr, str):
                item["addr_full"] = addr
            elif isinstance(addr, dict):
                if addr.get("@type", "PostalAddress") == "PostalAddress":
                    item["street_address"] = LinkedDataParser.get_case_insensitive(
                        addr, "streetAddress"
                    )
                    item["city"] = LinkedDataParser.get_case_insensitive(
                        addr, "addressLocality"
                    )
                    item["state"] = LinkedDataParser.get_case_insensitive(
                        addr, "addressRegion"
                    )
                    item["postcode"] = LinkedDataParser.get_case_insensitive(
                        addr, "postalCode"
                    )
                    country = LinkedDataParser.get_case_insensitive(
                        addr, "addressCountry"
                    )

                    if isinstance(country, str):
                        item["country"] = country
                    elif isinstance(country, dict):
                        if country.get("@type", "Country") == "Country":
                            item["country"] = country.get("name")

                    # Common mistake to put "telephone" in "address"
                    item["phone"] = LinkedDataParser.get_clean(addr, "telephone")

        if item.get("phone") is None:
            item["phone"] = LinkedDataParser.get_clean(ld, "telephone")

        if isinstance(item["phone"], list):
            item["phone"] = item["phone"][0]

        if isinstance(item["phone"], str):
            item["phone"] = item["phone"].replace("tel:", "")

        item["email"] = LinkedDataParser.get_clean(ld, "email")

        item["website"] = ld.get("url")

        try:
            oh = OpeningHours()
            oh.from_linked_data(ld)
            item["opening_hours"] = oh.as_opening_hours()
        except:
            pass

        if image := ld.get("image"):
            if isinstance(image, list):
                image = image[0]

            if isinstance(image, str):
                item["image"] = image
            elif isinstance(image, dict):
                if image.get("@type", "ImageObject") == "ImageObject":
                    item["image"] = image.get("contentUrl")

        item["ref"] = ld.get("branchCode")
        if item["ref"] is None or item["ref"] == "":
            item["ref"] = ld.get("@id")

        if item["ref"] == "":
            item["ref"] = None

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

    @staticmethod
    def get_clean(obj, key):
        if value := obj.get(key):
            if isinstance(value, str):
                return value.strip()
            return value

    @staticmethod
    def get_case_insensitive(obj, key):
        # Prioritise the case correct key
        if value := LinkedDataParser.get_clean(obj, key):
            return value

        for real_key in obj:
            if real_key.lower() == key.lower():
                return LinkedDataParser.get_clean(obj, real_key)
