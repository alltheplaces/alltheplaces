import reverse_geocoder

from locations.country_utils import CountryUtils
from locations.items import Feature


def get_lat_lon(item: Feature) -> (float, float):
    if geometry := item.get("geometry"):
        if isinstance(geometry, dict):
            if geometry.get("type") == "Point":
                if coords := geometry.get("coordinates"):
                    return coords[1], coords[0]
    else:
        try:
            return float(item.get("lat")), float(item.get("lon"))
        except TypeError:
            pass
    return None


class CountryCodeCleanUpPipeline:
    def __init__(self):
        self.country_utils = CountryUtils()

    def process_item(self, item, spider):
        if country := item.get("country"):
            if clean_country := self.country_utils.to_iso_alpha2_country_code(country):
                item["country"] = clean_country
                return item

        if getattr(spider, "skip_auto_cc", False):
            return item

        if not getattr(spider, "skip_auto_cc_spider_name", False):
            # No country set, see if it can be cleanly deduced from the spider name
            if country := self.country_utils.country_code_from_spider_name(spider.name):
                spider.crawler.stats.inc_value("atp/field/country/from_spider_name")
                item["country"] = country
                return item

        if not getattr(spider, "skip_auto_cc_domain", False):
            # Still no country set, see if it can be cleanly deduced from a website URL if present
            if country := self.country_utils.country_code_from_url(item.get("website")):
                spider.crawler.stats.inc_value("atp/field/country/from_website_url")
                item["country"] = country
                return item

        if not getattr(spider, "skip_auto_cc_geocoder", False):
            # Still no country set, try an offline reverse geocoder.
            if location := get_lat_lon(item):
                if results := reverse_geocoder.search([(location[0], location[1])]):
                    spider.crawler.stats.inc_value("atp/field/country/from_reverse_geocoding")
                    item["country"] = results[0]["cc"]

                    if not item.get("state"):
                        item["state"] = results[0].get("admin1")

                    return item

        return item
