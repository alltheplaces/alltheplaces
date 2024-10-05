import json
import logging
import re
import traceback

import chompjs
import json5

from locations.hours import DAYS_EN, OpeningHours, day_range, sanitise_day
from locations.items import Feature, add_social_media

logger = logging.getLogger(__name__)


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
    def parse_ld(ld, time_format: str = "%H:%M", days: {} = DAYS_EN) -> Feature:  # noqa: C901
        item = Feature()

        if (
            (geo := LinkedDataParser.get_case_insensitive(ld, "geo"))
            or "location" in [key.lower() for key in ld]
            and (geo := LinkedDataParser.get_case_insensitive(ld["location"], "geo"))
        ):
            if isinstance(geo, list):
                geo = geo[0]

            if LinkedDataParser.check_type(geo.get("@type"), "GeoCoordinates"):
                item["lat"] = LinkedDataParser.clean_float(LinkedDataParser.get_case_insensitive(geo, "latitude"))
                item["lon"] = LinkedDataParser.clean_float(LinkedDataParser.get_case_insensitive(geo, "longitude"))

        item["name"] = LinkedDataParser.get_case_insensitive(ld, "name")
        if isinstance(item["name"], list):
            item["name"] = item["name"][0]

        if addr := LinkedDataParser.get_case_insensitive(ld, "address"):
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
                            item["country"] = LinkedDataParser.get_case_insensitive(country, "name")

                    # Common mistake to put "telephone" in "address"
                    item["phone"] = LinkedDataParser.get_case_insensitive(addr, "telephone")

        if item.get("phone") is None:
            item["phone"] = LinkedDataParser.get_case_insensitive(ld, "telephone")

        if isinstance(item["phone"], list):
            item["phone"] = item["phone"][0]

        if isinstance(item["phone"], str):
            item["phone"] = item["phone"].replace("tel:", "")

        item["email"] = LinkedDataParser.get_case_insensitive(ld, "email")

        if isinstance(item["email"], str):
            item["email"] = item["email"].replace("mailto:", "")

        item["website"] = LinkedDataParser.get_case_insensitive(ld, "url")

        try:
            item["opening_hours"] = LinkedDataParser.parse_opening_hours(ld, time_format=time_format, days=days)
        except ValueError as e:
            # Explicitly handle a ValueError, which is likely time_format related
            logger.warning(f"Unable to parse opening hours - check time_format? Error was: {str(e)}")
        except Exception as e:
            logger.warning(f"Unhandled error, unable to parse opening hours. Error was: {type(e)} {str(e)}")
            logger.debug(traceback.format_exc())

        if image := LinkedDataParser.get_case_insensitive(ld, "image"):
            if isinstance(image, list):
                image = image[0]

            if isinstance(image, str):
                item["image"] = image
            elif isinstance(image, dict):
                if LinkedDataParser.check_type(image.get("@type"), "ImageObject"):
                    item["image"] = LinkedDataParser.get_case_insensitive(image, "contentUrl")

        item["ref"] = LinkedDataParser.get_case_insensitive(ld, "branchCode")
        if item["ref"] is None or item["ref"] == "":
            item["ref"] = LinkedDataParser.get_case_insensitive(ld, "@id")

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

    # Parses an openingHoursSpecification dict
    # e.g.:
    # {
    #  "@type": "OpeningHoursSpecification",
    #  "closes":  "17:00:00",
    #  "dayOfWeek": "https://schema.org/Sunday",
    #  "opens":  "09:00:00"
    # }
    # See https://schema.org/OpeningHoursSpecification for further examples.
    #
    # This defaults to DAYS_EN, which is the standard (see https://schema.org/DayOfWeek)
    # As some publishers publish localised days, we allow this to be overridden.
    @staticmethod
    def _parse_opening_hours_specification(oh: OpeningHours, rule: dict, time_format: str, days: {} = DAYS_EN):
        if (
            not type(LinkedDataParser.get_case_insensitive(rule, "dayOfWeek")) in [list, str]
            or not type(LinkedDataParser.get_case_insensitive(rule, "opens")) == str
            or not type(LinkedDataParser.get_case_insensitive(rule, "closes")) == str
        ):
            return oh

        parsed_days = LinkedDataParser.get_case_insensitive(rule, "dayOfWeek")
        if not isinstance(parsed_days, list):
            parsed_days = [parsed_days]

        for day in parsed_days:
            # Handle plain text days, or URI references to a DayOfWeek enumeration, ie https://schema.org/Friday
            parsed_day = sanitise_day(day.strip(), days)
            oh.add_range(
                day=days[parsed_day],
                open_time=LinkedDataParser.get_case_insensitive(rule, "opens").strip(),
                close_time=LinkedDataParser.get_case_insensitive(rule, "closes").strip(),
                time_format=time_format,
            )
        return oh

    # Parse an individual https://schema.org/openingHours property value such as
    # "Mo,Tu,We,Th 09:00-12:00"
    # "Mo-Fr 10:00-19:00"
    @staticmethod
    def _parse_opening_hours(oh: OpeningHours, rule: str, time_format: str, permitted_days: {} = DAYS_EN):
        days, time_ranges = rule.split(" ", 1)

        for time_range in time_ranges.split(","):
            if time_ranges.lower() in ["closed", "off"]:
                start_time = end_time = "closed"
            else:
                start_time, end_time = time_range.split("-")

            start_time = start_time.strip()
            end_time = end_time.strip()

            if "-" in days:
                start_day, end_day = days.split("-")

                start_day = sanitise_day(start_day, permitted_days)
                end_day = sanitise_day(end_day, permitted_days)

                for day in day_range(start_day, end_day):
                    oh.add_range(day, start_time, end_time, time_format)
            else:
                for day in days.split(","):
                    if d := sanitise_day(day, permitted_days):
                        oh.add_range(d, start_time, end_time, time_format)
        return oh

    @staticmethod
    def parse_opening_hours(linked_data, time_format: str = "%H:%M", days: {} = DAYS_EN) -> OpeningHours:
        oh = OpeningHours()
        if spec := LinkedDataParser.get_case_insensitive(linked_data, "openingHoursSpecification"):
            if isinstance(spec, list):
                for rule in spec:
                    if not isinstance(rule, dict):
                        continue
                    oh = LinkedDataParser._parse_opening_hours_specification(oh, rule, time_format, days)
            elif isinstance(spec, dict):
                oh = LinkedDataParser._parse_opening_hours_specification(oh, spec, time_format, days)
            else:
                logger.info("Unknown openingHoursSpecification structure, ignoring")
                logger.debug(LinkedDataParser.get_case_insensitive(linked_data, "openingHoursSpecification"))

        elif rules := LinkedDataParser.get_case_insensitive(linked_data, "openingHours"):
            if not isinstance(rules, list):
                rules = re.findall(
                    r"""((
                        \w{2,3}                 # Day
                        |\w{2,3}\s?\-\s?\w{2,3} # Day - Day
                        |(\w{2,3},)+\w{2,3}     # Day,Day
                    )\s(
                        (\d\d:\d\d)\s?\-\s?(\d\d:\d\d) # time - range
                        |(?i:closed) # ignoring case
                    ))""",
                    rules,
                    re.X,
                )
                rules = [r[0] for r in rules]

            for rule in rules:
                if not rule:
                    continue

                oh = LinkedDataParser._parse_opening_hours(oh, rule, time_format, days)

        return oh

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
        if stars := LinkedDataParser.get_case_insensitive(ld, "starRating"):
            if isinstance(stars, str):
                item["extras"]["stars"] = stars
            elif isinstance(stars, dict):
                item["extras"]["stars"] = LinkedDataParser.get_case_insensitive(stars, "ratingValue")

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
