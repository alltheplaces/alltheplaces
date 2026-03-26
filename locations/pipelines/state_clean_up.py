import reverse_geocoder
from geonamescache import GeonamesCache
from scrapy.crawler import Crawler

from locations.items import Feature, get_lat_lon

US_TERRITORIES = {
    "AS": {"code": "AS", "name": "American Samoa"},
    "FM": {"code": "FM", "name": "Micronesia"},
    "GU": {"code": "GU", "name": "Guam"},
    "MH": {"code": "MH", "name": "Marshall Islands"},
    "MP": {"code": "MP", "name": "Northern Mariana Islands"},
    "PW": {"code": "PW", "name": "Palau"},
    "PR": {"code": "PR", "name": "Puerto Rico"},
    "VI": {"code": "VI", "name": "U.S. Virgin Islands"},
}

STATES = {
    "CA": {
        "AB": {"code": "AB", "name": "Alberta"},
        "BC": {"code": "BC", "name": "British Columbia"},
        "MB": {"code": "MB", "name": "Manitoba"},
        "NB": {"code": "NB", "name": "New Brunswick"},
        "NT": {"code": "NT", "name": "Northwest Territories"},
        "NL": {"code": "NL", "name": "Newfoundland and Labrador"},
        "NS": {"code": "NS", "name": "Nova Scotia"},
        "NU": {"code": "YT", "name": "Nunavut"},
        "ON": {"code": "ON", "name": "Ontario"},
        "PE": {"code": "PE", "name": "Prince Edward Island"},
        "QC": {"code": "QC", "name": "Quebec"},
        "SK": {"code": "SK", "name": "Saskatchewan"},
        "YT": {"code": "YT", "name": "Yukon"},
    },
    "US": GeonamesCache().get_us_states() | US_TERRITORIES,
}

STATE_OVERRIDES = {"Washington, D.C.": "DC"}


class StateCodeCleanUpPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    @staticmethod
    def clean_state(state: str, country: str) -> str | None:
        if country not in STATES.keys():
            raise ValueError(f'Only {", ".join(STATES.keys())} supported')
            return None

        state = STATE_OVERRIDES.get(state, state)

        if s := STATES[country].get(state):
            return str(s["code"])
        else:
            for possible_state in STATES[country].values():
                if possible_state["name"] == state:
                    return str(possible_state["code"])

    def process_item(self, item: Feature) -> Feature:
        country = item.get("country")
        if not country:
            return item

        if country not in STATES.keys():
            return item

        state = StateCodeCleanUpPipeline.clean_state(str(item.get("state")), str(country))

        if not state:  # geocode state
            if location := get_lat_lon(item):
                if result := reverse_geocoder.get((location[0], location[1]), mode=1, verbose=False):
                    if self.crawler.stats:
                        self.crawler.stats.inc_value("atp/field/state/from_reverse_geocoding")
                    state = result["admin1"]

        item["state"] = StateCodeCleanUpPipeline.clean_state(str(state), str(country))

        return item
