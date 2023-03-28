import reverse_geocoder
from geonamescache import GeonamesCache

from locations.pipelines.country_code_clean_up import get_lat_lon
from locations.spiders.xfinity import US_TERRITORIES

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
    @staticmethod
    def clean_state(state: str, country: str) -> str:
        if country not in STATES.keys():
            raise ValueError(f'Only {", ".join(STATES.keys())} supported')

        state = STATE_OVERRIDES.get(state, state)

        if s := STATES[country].get(state):
            return s["code"]
        else:
            for possible_state in STATES[country].values():
                if possible_state["name"] == state:
                    return possible_state["code"]

    def process_item(self, item, spider):
        country = item.get("country")
        if not country:
            return item

        if country not in STATES.keys():
            return item

        state = StateCodeCleanUpPipeline.clean_state(item.get("state"), country)

        if not state:  # geocode state
            if location := get_lat_lon(item):
                if results := reverse_geocoder.search([(location[0], location[1])]):
                    spider.crawler.stats.inc_value("atp/field/state/from_reverse_geocoding")
                    state = results[0]["admin1"]

        item["state"] = StateCodeCleanUpPipeline.clean_state(state, country)

        return item
