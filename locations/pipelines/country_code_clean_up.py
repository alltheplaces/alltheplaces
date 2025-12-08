import reverse_geocoder

from locations.country_utils import CountryUtils
from locations.items import get_lat_lon


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
                if result := reverse_geocoder.get((location[0], location[1]), mode=1, verbose=False):
                    spider.crawler.stats.inc_value("atp/field/country/from_reverse_geocoding")
                    item["country"] = result["cc"]

                    if not item.get("state"):
                        item["state"] = result.get("admin1")

                    return item

        return item
