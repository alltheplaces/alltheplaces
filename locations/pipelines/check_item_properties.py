import math
import re
import unicodedata
from re import Pattern
from urllib.parse import urlparse

from geonamescache import GeonamesCache
from scrapy import Spider
from scrapy.crawler import Crawler

from locations.hours import OpeningHours
from locations.items import Feature, set_lat_lon


def check_field(
    item: Feature,
    spider: Spider,
    param: str,
    allowed_types: type | tuple[type],
    match_regex: Pattern | None = None,
) -> None:
    if val := item.get(param):
        if not isinstance(val, allowed_types):
            spider.logger.error(
                f'Invalid type "{type(val).__name__}" for attribute "{param}". Expected type(s) are "{allowed_types}".'
            )
            if spider.crawler and spider.crawler.stats:
                spider.crawler.stats.inc_value(f"atp/field/{param}/wrong_type")
        elif match_regex and not match_regex.match(val):
            spider.logger.warning(
                f'Invalid value "{val}" for attribute "{param}". Value did not match expected regular expression of r"{match_regex.pattern}".'
            )
            if spider.crawler and spider.crawler.stats:
                spider.crawler.stats.inc_value(f"atp/field/{param}/invalid")
    elif spider.crawler and spider.crawler.stats:
        spider.crawler.stats.inc_value(f"atp/field/{param}/missing")


class CheckItemPropertiesPipeline:
    crawler: Crawler

    countries = GeonamesCache().get_countries().keys()
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

    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_item(self, item: Feature) -> Feature:  # noqa: C901
        if not self.crawler.spider:
            return item
        check_field(item, self.crawler.spider, "brand_wikidata", allowed_types=(str,), match_regex=self.wikidata_regex)
        check_field(
            item, self.crawler.spider, "operator_wikidata", allowed_types=(str,), match_regex=self.wikidata_regex
        )
        check_field(item, self.crawler.spider, "email", (str,), self.email_regex)
        check_field(item, self.crawler.spider, "phone", (str,))
        check_field(item, self.crawler.spider, "street_address", (str,))
        check_field(item, self.crawler.spider, "city", (str,))
        check_field(item, self.crawler.spider, "state", (str,))
        check_field(item, self.crawler.spider, "postcode", (str,))
        check_field(item, self.crawler.spider, "country", (str,))
        check_field(item, self.crawler.spider, "name", (str,))
        check_field(item, self.crawler.spider, "brand", (str,))
        check_field(item, self.crawler.spider, "operator", (str,))
        check_field(item, self.crawler.spider, "branch", (str,))

        self.check_geom(item, self.crawler.spider)
        self.check_twitter(item, self.crawler.spider)
        self.check_opening_hours(item, self.crawler.spider)
        self.check_country(item, self.crawler.spider)
        self.check_url(item, self.crawler.spider, "image")
        self.check_url(item, self.crawler.spider, "website")

        if country_code := item.get("country"):
            if (
                self.crawler
                and self.crawler.spider
                and self.crawler.spider.crawler
                and self.crawler.spider.crawler.stats
            ):
                self.crawler.spider.crawler.stats.inc_value(f"atp/country/{country_code}")

        return item

    def check_geom(self, item: Feature, spider: Spider) -> None:  # noqa: C901
        lat_untyped = None
        lon_untyped = None
        if geometry := item.get("geometry"):
            if isinstance(geometry, dict):
                if geometry.get("type") == "Point":
                    if coords := geometry.get("coordinates"):
                        if isinstance(coords, list):
                            if len(coords) == 2:
                                lat_untyped = coords[1]
                                lon_untyped = coords[0]
                elif geometry.get("type") in [
                    "MultiPoint",
                    "LineString",
                    "MultiLineString",
                    "Polygon",
                    "MultiPolygon",
                ]:
                    # Other geometry types are currently not validated by
                    # ATP so this pipeline will assume they're correct.
                    item.pop("lat", None)
                    item.pop("lon", None)
                    return
                else:
                    # Invalid geometry type. Refer to RFC 7946 for valid
                    # types.
                    if spider.crawler.stats:
                        spider.crawler.stats.inc_value("atp/field/geometry/invalid")
                    item.pop("lat", None)
                    item.pop("lon", None)
                    item.pop("geometry", None)
                    return
            else:
                # Invalid geometry type.
                if spider.crawler.stats:
                    spider.crawler.stats.inc_value("atp/field/geometry/invalid")
                item.pop("lat", None)
                item.pop("lon", None)
                item.pop("geometry", None)
                return
        else:
            lat_untyped = item.get("lat")
            lon_untyped = item.get("lon")

        if lat_untyped is None or lon_untyped is None:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/geometry/missing")
            item.pop("lat", None)
            item.pop("lon", None)
            item.pop("geometry", None)
            return

        # At this point, lat_untyped and lon_untyped were either extracted
        # from the geometry attribute, or lat/lon attributes. They could be
        # invalidly typed (e.g. strings) or have invalid values (e.g. 700).

        try:
            lat_typed = float(lat_untyped)
            lon_typed = float(lon_untyped)
            if math.isnan(lat_typed) or math.isnan(lon_typed):
                raise ValueError("Latitude or longitude is NaN")
        except (TypeError, ValueError):
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/geometry/invalid")
            item.pop("lat", None)
            item.pop("lon", None)
            item.pop("geometry", None)
            return

        if lat_typed < -90.0 or lat_typed > 90.0 or lon_typed < -180.0 or lon_typed > 180.0:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/geometry/invalid")
            item.pop("lat", None)
            item.pop("lon", None)
            item.pop("geometry", None)
            return None

        if math.fabs(lat_typed) < 3 and math.fabs(lon_typed) < 3:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/geometry/null_island")
            item.pop("lat", None)
            item.pop("lon", None)
            item.pop("geometry", None)
            return

        set_lat_lon(item, lat_typed, lon_typed)

    def check_twitter(self, item: Feature, spider: Spider) -> None:
        if twitter := item.get("twitter"):
            if not isinstance(twitter, str):
                if spider.crawler.stats:
                    spider.crawler.stats.inc_value("atp/field/twitter/wrong_type")
                return
            if not self._is_valid_twitter(twitter):
                if spider.crawler.stats:
                    spider.crawler.stats.inc_value("atp/field/twitter/invalid")
                return
        else:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/twitter/missing")

    def _is_valid_twitter(self, twitter: str) -> bool:
        if self.twitter_regex.match(twitter):
            return True
        try:
            url = urlparse(twitter)
        except ValueError:
            return False
        return url.hostname in {"twitter.com", "x.com"}

    def check_opening_hours(self, item: Feature, spider: Spider) -> None:
        opening_hours = item.get("opening_hours")
        if opening_hours is not None:
            if isinstance(opening_hours, OpeningHours):
                if opening_hours:
                    item["opening_hours"] = opening_hours.as_opening_hours()
                else:
                    del item["opening_hours"]
                    if spider.crawler.stats:
                        spider.crawler.stats.inc_value("atp/field/opening_hours/missing")
            elif not isinstance(opening_hours, str):
                if spider.crawler.stats:
                    spider.crawler.stats.inc_value("atp/field/opening_hours/wrong_type")
            elif not self.opening_hours_regex.match(opening_hours) and opening_hours != "24/7":
                if spider.crawler.stats:
                    spider.crawler.stats.inc_value("atp/field/opening_hours/invalid")
        else:
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/opening_hours/missing")

    def check_country(self, item: Feature, spider: Spider) -> None:
        if not isinstance(item.get("country"), str):
            return
        if item.get("country") not in self.countries:
            spider.logger.error('Invalid value "{}" for attribute "{}".'.format(item.get("country"), "country"))
            if spider.crawler.stats:
                spider.crawler.stats.inc_value("atp/field/{}/invalid".format("country"))

    def check_url(self, item: Feature, spider: Spider, param: str) -> None:
        val = item.get(param)
        if not val:
            return

        # Check that param is a string.
        if not isinstance(val, str):
            spider.logger.error(f'Invalid type "{type(val).__name__}" for attribute "{param}". Expected type is "str".')
            if spider.crawler and spider.crawler.stats:
                spider.crawler.stats.inc_value(f"atp/field/{param}/wrong_type")
            return

        # Check that param is a valid URL.
        try:
            url = urlparse(val)
        except ValueError:
            spider.logger.error(f'Invalid value "{val}" for attribute "{param}". Value is not a valid url.')
            if spider.crawler and spider.crawler.stats:
                spider.crawler.stats.inc_value(f"atp/field/{param}/invalid")
            return

        # Restrict URLs to http or https.
        if url.scheme not in ("http", "https"):
            spider.logger.error(f'Invalid value "{val}" for attribute "{param}". URL scheme is not http or https.')
            if spider.crawler and spider.crawler.stats:
                spider.crawler.stats.inc_value(f"atp/field/{param}/invalid")
            return

        # Enforce that hostname is valid.
        if not self._is_valid_hostname(url.hostname):
            spider.logger.error(f'Invalid value "{val}" for attribute "{param}". Hostname is not valid.')
            if spider.crawler and spider.crawler.stats:
                spider.crawler.stats.inc_value(f"atp/field/{param}/invalid")
            return

    @staticmethod
    def _is_valid_hostname(hostname: str | None) -> bool:
        if hostname is None:
            return False
        if len(hostname) > 253:
            return False
        for part in hostname.split("."):
            if not part or len(part) > 63:
                return False
            if part.startswith("-") or part.endswith("-"):
                return False
            if part.lower().startswith("xn--"):  # reject Punycode
                return False
            for ch in part:
                cat = unicodedata.category(ch)
                if not (cat.startswith("L") or cat == "Nd" or ch == "-"):
                    return False
        return True
