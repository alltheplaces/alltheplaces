# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import math
import re

import phonenumbers
import reverse_geocode
from phonenumbers import NumberParseException
from scrapy.exceptions import DropItem

from locations.categories import get_category_tags
from locations.country_utils import CountryUtils
from locations.hours import OpeningHours
from locations.name_suggestion_index import NSI


class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if hasattr(spider, "no_refs") and getattr(spider, "no_refs"):
            return item

        ref = (spider.name, item["ref"])
        if ref in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(ref)
            return item


class ApplySpiderNamePipeline:
    def process_item(self, item, spider):
        existing_extras = item.get("extras", {})
        existing_extras["@spider"] = spider.name
        item["extras"] = existing_extras

        return item


class ApplySpiderLevelAttributesPipeline:
    def process_item(self, item, spider):
        if not hasattr(spider, "item_attributes"):
            return item

        item_attributes = spider.item_attributes

        for (key, value) in item_attributes.items():
            if key == "extras":
                extras = item.get("extras", {})
                for k, v in value.items():
                    if extras.get(k) is None:
                        extras[k] = v
                item["extras"] = extras
            else:
                if item.get(key) is None:
                    item[key] = value

        return item


class CountryCodeCleanUpPipeline:
    def __init__(self):
        self.country_utils = CountryUtils()

    def process_item(self, item, spider):
        if country := item.get("country"):
            if clean_country := self.country_utils.to_iso_alpha2_country_code(country):
                item["country"] = clean_country
        else:
            if hasattr(spider, "skip_auto_cc") and getattr(spider, "skip_auto_cc"):
                return item

            # No country set, see if it can be cleanly deduced from the spider name
            if country := self.country_utils.country_code_from_spider_name(spider.name):
                spider.crawler.stats.inc_value("atp/field/country/from_spider_name")
                item["country"] = country
                return item

            # Still no country set, see if it can be cleanly deduced from a website URL if present
            if country := self.country_utils.country_code_from_url(item.get("website")):
                spider.crawler.stats.inc_value("atp/field/country/from_website_url")
                item["country"] = country
                return item

            # Still no country set, try an offline reverse geocoder.
            lat, lon = item.get("lat"), item.get("lon")
            if lat is not None and lon is not None:
                if c := reverse_geocode.search([(lat, lon)]):
                    spider.crawler.stats.inc_value("atp/field/country/from_reverse_geocoding")
                    item["country"] = c[0]["country_code"]
                    return item

        return item


class PhoneCleanUpPipeline:
    def process_item(self, item, spider):
        phone, country = item.get("phone"), item.get("country")
        extras = item.get("extras", {})
        for key in filter(self.is_phone_key, extras.keys()):
            extras[key] = self.normalize_numbers(extras[key], country, spider)

        if isinstance(phone, int):
            phone = str(phone)
        elif not phone:
            spider.crawler.stats.inc_value("atp/field/phone/missing")
            return item
        elif not isinstance(phone, str):
            spider.crawler.stats.inc_value("atp/field/phone/wrong_type")
            return item
        item["phone"] = self.normalize_numbers(phone, country, spider)
        return item

    @staticmethod
    def is_phone_key(tag):
        return tag in ("phone", "fax") or tag.endswith(":phone") or tag.endswith(":fax")

    def normalize_numbers(self, phone, country, spider):
        numbers = [self.normalize(p, country, spider) for p in re.split(r";|/", str(phone))]
        return ";".join(filter(None, numbers))

    def normalize(self, phone, country, spider):
        phone = phone.strip()
        try:
            ph = phonenumbers.parse(phone, country)
            if phonenumbers.is_valid_number(ph):
                return phonenumbers.format_number(ph, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        except NumberParseException:
            pass
        spider.crawler.stats.inc_value("atp/field/phone/invalid")
        return phone


class ExtractGBPostcodePipeline:
    def process_item(self, item, spider):
        if item.get("country") == "GB":
            if item.get("addr_full") and not item.get("postcode"):
                postcode = re.search(r"(\w{1,2}\d{1,2}\w? \d\w{2})", item["addr_full"].upper())
                if postcode:
                    item["postcode"] = postcode.group(1)
                else:
                    postcode = re.search(r"(\w{1,2}\d{1,2}\w?) O(\w{2})", item["addr_full"].upper())
                    if postcode:
                        item["postcode"] = postcode.group(1) + " 0" + postcode.group(2)
        elif item.get("country") == "IE":
            if item.get("addr_full") and not item.get("postcode"):
                if postcode := re.search(
                    r"([AC-FHKNPRTV-Y][0-9]{2}|D6W)[ -]?([0-9AC-FHKNPRTV-Y]{4})", item["addr_full"].upper()
                ):
                    item["postcode"] = "{} {}".format(postcode.group(1), postcode.group(2))

        return item


class AssertURLSchemePipeline:
    def process_item(self, item, spider):
        if item.get("image"):
            if item["image"].startswith("//"):
                item["image"] = "https:" + item["image"]

        return item


def check_field(item, spider, param, allowed_types, match_regex=None):
    if val := item.get(param):
        if not isinstance(val, *allowed_types):
            spider.crawler.stats.inc_value(f"atp/field/{param}/wrong_type")
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
    email_regex = re.compile(r"(^[-\w_.+]+@[-\w]+\.[-\w.]+$)")
    twitter_regex = re.compile(r"^@?([-\w_]+)$")
    wikidata_regex = re.compile(
        r"^Q[0-9]+$",
    )
    opening_hours_regex = re.compile(
        r"^(?:(?:Mo|Tu|We|Th|Fr|Sa|Su)(?:-(?:Mo|Tu|We|Th|Fr|Sa|Su))? [0-9]{2}:[0-9]{2}-[0-9]{2}:[0-9]{2}(?:; )?)+$"
    )
    min_lat = -90.0
    max_lat = 90.0
    min_lon = -180.0
    max_lon = 180.0

    def process_item(self, item, spider):  # noqa: C901
        check_field(item, spider, "brand_wikidata", allowed_types=(str,), match_regex=self.wikidata_regex)
        check_field(item, spider, "website", (str,), self.url_regex)
        check_field(item, spider, "image", (str,), self.url_regex)
        check_field(item, spider, "email", (str,), self.email_regex)
        check_field(item, spider, "street_address", (str,))
        check_field(item, spider, "city", (str,))
        check_field(item, spider, "state", (str,))
        check_field(item, spider, "postcode", (str,))
        check_field(item, spider, "country", (str,))
        check_field(item, spider, "brand", (str,))

        if lat := item.get("lat"):
            try:
                lat = float(lat)
                if not (self.min_lat < lat < self.max_lat):
                    spider.crawler.stats.inc_value("atp/field/lat/invalid")
                if math.fabs(lat) < 0.01:
                    spider.crawler.stats.inc_value("atp/field/lat/invalid")
            except:
                lat = None
                spider.crawler.stats.inc_value("atp/field/lat/invalid")
            item["lat"] = lat
        else:
            spider.crawler.stats.inc_value("atp/field/lat/missing")
        if lon := item.get("lon"):
            try:
                lon = float(lon)
                if not (self.min_lon < lon < self.max_lon):
                    spider.crawler.stats.inc_value("atp/field/lon/invalid")
                if math.fabs(lon) < 0.01:
                    spider.crawler.stats.inc_value("atp/field/lon/invalid")
            except:
                lon = None
                spider.crawler.stats.inc_value("atp/field/lon/invalid")
            item["lon"] = lon
        else:
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

        if opening_hours := item.get("opening_hours"):
            if isinstance(opening_hours, OpeningHours):
                item["opening_hours"] = opening_hours.as_opening_hours()
            elif not isinstance(opening_hours, str):
                spider.crawler.stats.inc_value("atp/field/opening_hours/wrong_type")
            elif not self.opening_hours_regex.match(opening_hours) and opening_hours != "24/7":
                spider.crawler.stats.inc_value("atp/field/opening_hours/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/opening_hours/missing")

        return item


class ApplyNSICategoriesPipeline:
    nsi = NSI()

    wikidata_cache = {}

    def process_item(self, item, spider):
        if item.get("nsi_id"):
            return item

        code = item.get("brand_wikidata")
        if not code:
            return item

        if not self.wikidata_cache.get(code):
            # wikidata_cache will usually only hold one thing, but can contain more with more complex spiders
            # The key thing is that we don't have to call nsi.iter_nsi on every process_item
            self.wikidata_cache[code] = list(self.nsi.iter_nsi(code))

        matches = self.wikidata_cache.get(code)

        if len(matches) == 0:
            spider.crawler.stats.inc_value("atp/nsi/brand_missing")
            return item

        if len(matches) == 1:
            spider.crawler.stats.inc_value("atp/nsi/perfect_match")
            return self.apply_tags(matches[0], item)

        if cc := item.get("country"):
            matches = self.filter_cc(matches, cc.lower())

            if len(matches) == 1:
                spider.crawler.stats.inc_value("atp/nsi/cc_match")
                return self.apply_tags(matches[0], item)

        if categories := get_category_tags(item):
            matches = self.filter_categories(matches, categories)

            if len(matches) == 1:
                spider.crawler.stats.inc_value("atp/nsi/category_match")
                return self.apply_tags(matches[0], item)

        spider.crawler.stats.inc_value("atp/nsi/match_failed")
        return item

    def filter_cc(self, matches, cc) -> []:
        includes = []
        globals_matches = []

        for match in matches:
            if cc in match["locationSet"].get("exclude", []):
                continue

            include = match["locationSet"].get("include", [])
            # Ignore non string such as: {"include":[[-122.835,45.5,2]]}
            include = filter(lambda i: isinstance(i, str), include)
            # "gb-eng" -> "gb"
            include = [i.split("-")[0] for i in include]
            if cc in include:
                includes.append(match)
            if "001" in include:  # 001 being global in NSI
                globals_matches.append(match)

        return includes or globals_matches

    def filter_categories(self, matches, tags) -> []:
        results = []

        for match in matches:
            if get_category_tags(match["tags"]) == tags:
                results.append(match)

        return results

    def apply_tags(self, match, item):
        extras = item.get("extras", {})
        item["nsi_id"] = match["id"]

        # Apply NSI tags to item
        for (key, value) in match["tags"].items():
            if key == "brand:wikidata":
                key = "brand_wikidata"

            # Fields defined in Feature are added directly otherwise add them to extras
            # Never override anything set by the spider
            if key in item.fields:
                if item.get(key) is None:
                    item[key] = value
            else:
                if extras.get(key) is None:
                    extras[key] = value

        item["extras"] = extras

        return item


class CountCategoriesPipeline:
    def process_item(self, item, spider):
        if categories := get_category_tags(item):
            for k, v in sorted(categories.items()):
                spider.crawler.stats.inc_value("atp/category/%s/%s" % (k, v))
                break
            if len(categories) > 1:
                spider.crawler.stats.inc_value("atp/category/multiple")
        else:
            spider.crawler.stats.inc_value("atp/category/missing")
        return item
