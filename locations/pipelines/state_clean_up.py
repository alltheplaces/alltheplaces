import reverse_geocoder
from geonamescache import GeonamesCache
from scrapy.exceptions import DropItem

from locations.items import get_lat_lon
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
                if result := reverse_geocoder.get((location[0], location[1]), mode=1, verbose=False):
                    spider.crawler.stats.inc_value("atp/field/state/from_reverse_geocoding")
                    state = result["admin1"]

        item["state"] = StateCodeCleanUpPipeline.clean_state(state, country)

        # If the spider wants a callback then make it. If there are any errors
        # in the mechanism then catch them, log them and abort the output.
        try:
            if StateCodeCleanUpPipeline in getattr(spider, "pipeline_after_callbacks", []):
                item = spider.pipeline_after_callback(item, StateCodeCleanUpPipeline)
        except Exception as e:
            spider.crawler.stats.inc_value("atp/pipeline/error/StateCodeCleanUpPipeline")
            spider.logger.error(f"Error in pipeline callback: {str(e)}")
            item = None

        if item is None:
            raise DropItem

        return item
