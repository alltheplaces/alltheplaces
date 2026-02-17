import reverse_geocoder
from scrapy.crawler import Crawler

from locations.country_utils import CountryUtils
from locations.items import Feature, get_lat_lon


class CountryCodeCleanUpPipeline:
    crawler: Crawler

    def __init__(self, crawler: Crawler):
        self.crawler = crawler
        self.country_utils = CountryUtils()

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature):
        if country := item.get("country"):
            if clean_country := self.country_utils.to_iso_alpha2_country_code(country):
                item["country"] = clean_country
                return item

        if getattr(self.crawler.spider, "skip_auto_cc", False):
            return item

        if not getattr(self.crawler.spider, "skip_auto_cc_spider_name", False):
            # No country set, see if it can be cleanly deduced from the spider name

            spider_name = getattr(self.crawler.spider, "name", False)
            if not isinstance(spider_name, str):
                # No spider name set, cannot determine country code(s) from the spider name.
                return item

            if country := self.country_utils.country_code_from_spider_name(
                spider_name
            ):
                if self.crawler.stats:
                    self.crawler.stats.inc_value(
                        "atp/field/country/from_spider_name"
                    )
                item["country"] = country
                return item

        if not getattr(self.crawler.spider, "skip_auto_cc_domain", False):
            # Still no country set, see if it can be cleanly deduced from a website URL if present

            website_url = item.get("website")
            if not isinstance(website_url, str):
                # No website attribute set for the item, cannot determine country code from website URL.
                return item

            if country := self.country_utils.country_code_from_url(website_url):
                if self.crawler.stats:
                    self.crawler.stats.inc_value(
                        "atp/field/country/from_website_url"
                    )
                item["country"] = country
                return item

        if not getattr(self.crawler.spider, "skip_auto_cc_geocoder", False):
            # Still no country set, try an offline reverse geocoder.
            if location := get_lat_lon(item):
                if result := reverse_geocoder.get((location[0], location[1]), mode=1, verbose=False):
                    if self.crawler.stats:
                        self.crawler.stats.inc_value(
                            "atp/field/country/from_reverse_geocoding"
                        )
                    item["country"] = result["cc"]

                    if not item.get("state"):
                        item["state"] = result.get("admin1")

                    return item

        return item
