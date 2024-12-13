import math
import re

from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import get_lat_lon, set_lat_lon


def check_field(item, spider: Spider, param, allowed_types, match_regex=None):
    if val := item.get(param):
        if not isinstance(val, allowed_types):
            spider.crawler.stats.inc_value(f"atp/field/{param}/wrong_type")
            spider.logger.error(f"Invalid type {type(val).__name__} on {param}, expected {allowed_types}")
        elif match_regex and not match_regex.match(val):
            spider.crawler.stats.inc_value(f"atp/field/{param}/invalid")
    else:
        spider.crawler.stats.inc_value(f"atp/field/{param}/missing")


class CheckItemPropertiesPipeline:
    # From https://github.com/django/django/blob/master/django/core/validators.py
    url_regex = re.compile(
        r"^(?:http)s?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|"  # ...or ipv4
        r"\[?[A-F0-9]*:[A-F0-9:]+\]?)"  # ...or ipv6
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    country_regex = re.compile(r"(^[A-Z]{2}$)")
    email_regex = re.compile(r"(^[-\w_.+]+@[-\w]+\.[-\w.]+$)")
    twitter_regex = re.compile(r"^@?([-\w_]+)$")
    wikidata_regex = re.compile(
        r"^Q[0-9]+$",
    )
    opening_hours_regex = re.compile(
        r"^(?:(?:Mo|Tu|We|Th|Fr|Sa|Su)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))? (?:,?[0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}|closed|off)+(?:; )?)+$"
    )
    min_lat = -90.0
    max_lat = 90.0
    min_lon = -180.0
    max_lon = 180.0

    def process_item(self, item, spider):  # noqa: C901
        check_field(item, spider, "brand_wikidata", allowed_types=(str,), match_regex=self.wikidata_regex)
        check_field(item, spider, "operator_wikidata", allowed_types=(str,), match_regex=self.wikidata_regex)
        check_field(item, spider, "website", (str,), self.url_regex)
        check_field(item, spider, "image", (str,), self.url_regex)
        check_field(item, spider, "email", (str,), self.email_regex)
        check_field(item, spider, "phone", (str,))
        check_field(item, spider, "street_address", (str,))
        check_field(item, spider, "city", (str,))
        check_field(item, spider, "state", (str,))
        check_field(item, spider, "postcode", (str,))
        check_field(item, spider, "country", (str,), self.country_regex)
        check_field(item, spider, "name", (str,))
        check_field(item, spider, "brand", (str,))
        check_field(item, spider, "operator", (str,))
        check_field(item, spider, "branch", (str,))

        if coords := get_lat_lon(item):
            lat, lon = coords

            if not (self.min_lat < lat < self.max_lat):
                spider.crawler.stats.inc_value("atp/field/lat/invalid")
                lat = None

            if not (self.min_lon < lon < self.max_lon):
                spider.crawler.stats.inc_value("atp/field/lon/invalid")
                lon = None

            if isinstance(lat, float) and isinstance(lon, float):
                if math.fabs(lat) < 3 and math.fabs(lon) < 3:
                    spider.crawler.stats.inc_value("atp/geometry/null_island")
                    lat = None
                    lon = None

            set_lat_lon(item, lat, lon)

        if not (item.get("geometry") or get_lat_lon(item)):
            spider.crawler.stats.inc_value("atp/field/lat/missing")
            spider.crawler.stats.inc_value("atp/field/lon/missing")

        if twitter := item.get("twitter"):
            if not isinstance(twitter, str):
                spider.crawler.stats.inc_value("atp/field/twitter/wrong_type")
            elif not (self.url_regex.match(twitter) and "twitter.com" in twitter) and not self.twitter_regex.match(
                twitter
            ):
                spider.crawler.stats.inc_value("atp/field/twitter/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/twitter/missing")

        opening_hours = item.get("opening_hours")
        if opening_hours is not None:
            if isinstance(opening_hours, OpeningHours):
                if opening_hours:
                    item["opening_hours"] = opening_hours.as_opening_hours()
                else:
                    del item["opening_hours"]
                    spider.crawler.stats.inc_value("atp/field/opening_hours/missing")
            elif not isinstance(opening_hours, str):
                spider.crawler.stats.inc_value("atp/field/opening_hours/wrong_type")
            elif not self.opening_hours_regex.match(opening_hours) and opening_hours != "24/7":
                spider.crawler.stats.inc_value("atp/field/opening_hours/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/opening_hours/missing")

        return item
