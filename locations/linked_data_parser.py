import json

import chompjs
import json5

from locations.hours import OpeningHours
from locations.items import Feature, add_social_media


class LinkedDataParser:
    @staticmethod
    def iter_linked_data(response, json_parser="json"):
        lds = response.xpath('//script[@type="application/ld+json"]//text()').getall()
        for ld in lds:
            try:
                if json_parser == "json5":
                    ld_obj = json5.loads(ld)
                elif json_parser == "chompjs":
                    ld_obj = chompjs.parse_js_object(ld)
                else:
                    ld_obj = json.loads(ld, strict=False)
            except (json.decoder.JSONDecodeError, ValueError):
                continue

            if isinstance(ld_obj, dict):
                if "@graph" in ld_obj:
                    yield from filter(None, ld_obj["@graph"])
                else:
                    yield ld_obj
            elif isinstance(ld_obj, list):
                yield from filter(None, ld_obj)
            else:
                raise TypeError(ld_obj)

    @staticmethod
    def find_linked_data(response, wanted_type, json_parser="json") -> {}:
        if isinstance(wanted_type, list):
            wanted_types = [LinkedDataParser.clean_type(t) for t in wanted_type]
        else:
            wanted_types = [LinkedDataParser.clean_type(wanted_type)]

        for ld_obj in LinkedDataParser.iter_linked_data(response, json_parser=json_parser):
            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            if all(wanted in types for wanted in wanted_types):
                return ld_obj

    @staticmethod
    def parse_ld(ld, time_format: str = "%H:%M") -> Feature:  # noqa: C901
        item = Feature()

        if (geo := ld.get("geo")) or "location" in ld and (geo := ld["location"].get("geo")):
            if isinstance(geo, list):
                geo = geo[0]

            if LinkedDataParser.check_type(geo.get("@type"), "GeoCoordinates"):
                item["lat"] = LinkedDataParser.clean_float(LinkedDataParser.get_clean(geo, "latitude"))
                item["lon"] = LinkedDataParser.clean_float(LinkedDataParser.get_clean(geo, "longitude"))

        item["name"] = LinkedDataParser.get_clean(ld, "name")
        if isinstance(item["name"], list):
            item["name"] = item["name"][0]

        if addr := LinkedDataParser.get_clean(ld, "address"):
            if isinstance(addr, list):
                addr = addr[0]

            if isinstance(addr, str):
                item["addr_full"] = addr
            elif isinstance(addr, dict):
                if LinkedDataParser.check_type(addr.get("@type"), "PostalAddress"):
                    if street_address := LinkedDataParser.get_case_insensitive(addr, "streetAddress"):
                        if isinstance(street_address, list):
                            street_address = ", ".join(street_address)

                        item["street_address"] = street_address
                    item["city"] = LinkedDataParser.get_case_insensitive(addr, "addressLocality")
                    item["state"] = LinkedDataParser.get_case_insensitive(addr, "addressRegion")
                    item["postcode"] = LinkedDataParser.get_case_insensitive(addr, "postalCode")
                    country = LinkedDataParser.get_case_insensitive(addr, "addressCountry")

                    if isinstance(country, str):
                        item["country"] = country
                    elif isinstance(country, dict):
                        if LinkedDataParser.check_type(country.get("@type"), "Country"):
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

        if isinstance(item["email"], str):
            item["email"] = item["email"].replace("mailto:", "")

        item["website"] = ld.get("url")

        try:
            oh = OpeningHours()
            oh.from_linked_data(ld, time_format=time_format)
            item["opening_hours"] = oh
        except:
            pass

        if image := ld.get("image"):
            if isinstance(image, list):
                image = image[0]

            if isinstance(image, str):
                item["image"] = image
            elif isinstance(image, dict):
                if LinkedDataParser.check_type(image.get("@type"), "ImageObject"):
                    item["image"] = image.get("contentUrl")

        item["ref"] = ld.get("branchCode")
        if item["ref"] is None or item["ref"] == "":
            item["ref"] = ld.get("@id")

        if item["ref"] == "":
            item["ref"] = None

        types = ld.get("@type", [])
        if not isinstance(types, list):
            types = [types]
        types = [LinkedDataParser.clean_type(t) for t in types]
        for t in types:
            LinkedDataParser.parse_enhanced(t, ld, item)

        LinkedDataParser.parse_same_as(ld, item)

        return item

    @staticmethod
    def parse(response, wanted_type, json_parser="json") -> Feature:
        ld_item = LinkedDataParser.find_linked_data(response, wanted_type, json_parser=json_parser)
        if ld_item:
            item = LinkedDataParser.parse_ld(ld_item)

            if isinstance(item["website"], list):
                item["website"] = item["website"][0]

            if not item["website"]:
                item["website"] = response.url
            elif item["website"].startswith("www"):
                item["website"] = "https://" + item["website"]

            return item

    @staticmethod
    def get_clean(obj, key):
        if value := obj.get(key):
            if isinstance(value, str):
                if value == "null":
                    return None
                return value.strip(" ,")
            return value

    @staticmethod
    def get_case_insensitive(obj, key):
        # Prioritise the case correct key
        if value := LinkedDataParser.get_clean(obj, key):
            return value

        for real_key in obj:
            if real_key.lower() == key.lower():
                return LinkedDataParser.get_clean(obj, real_key)

    @staticmethod
    def check_type(type: str, wanted_type: str, default: bool = True) -> bool:
        if default and type is None:
            return True

        return LinkedDataParser.clean_type(type) == wanted_type.lower()

    @staticmethod
    def clean_type(type: str) -> str:
        return type.lower().replace("http://", "").replace("https://", "").replace("schema.org/", "")

    @staticmethod
    def clean_float(value: str | float) -> float:
        if isinstance(value, float):
            return value
        if isinstance(value, str):
            try:
                return float(value.replace(",", "."))
            except:
                pass
        # Pass the bad data forward and let the validation pipeline complain
        return value

    @staticmethod
    def parse_enhanced(t: str, ld: dict, item: Feature):
        if t == "hotel":
            LinkedDataParser.parse_enhanced_hotel(ld, item)

    @staticmethod
    def parse_enhanced_hotel(ld: dict, item: Feature):
        if stars := LinkedDataParser.get_clean(ld, "starRating"):
            if isinstance(stars, str):
                item["extras"]["stars"] = stars
            elif isinstance(stars, dict):
                item["extras"]["stars"] = stars.get("ratingValue")

    @staticmethod
    def parse_same_as(ld: dict, item: Feature):
        if same_as := LinkedDataParser.get_clean(ld, "sameAs"):
            if isinstance(same_as, str):
                same_as = [same_as]
            for link in same_as:
                if "facebook.com" in link:
                    add_social_media(item, "facebook", link)
                elif "tripadvisor.com" in link:
                    add_social_media(item, "tripadvisor", link)
