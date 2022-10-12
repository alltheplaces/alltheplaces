# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import math
import re

from scrapy.exceptions import DropItem

from locations.name_suggestion_index import NSI


class DuplicatesPipeline(object):
    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        ref = (spider.name, item["ref"])
        if ref in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(ref)
            return item


class ApplySpiderNamePipeline(object):
    def process_item(self, item, spider):
        existing_extras = item.get("extras", {})
        existing_extras["@spider"] = spider.name
        item["extras"] = existing_extras

        return item


class ApplySpiderLevelAttributesPipeline(object):
    def process_item(self, item, spider):
        if not hasattr(spider, "item_attributes"):
            return item

        item_attributes = spider.item_attributes

        for (key, value) in item_attributes.items():
            if item.get(key) is None:
                item[key] = value

        return item


class ExtractGBPostcodePipeline(object):
    def process_item(self, item, spider):
        if item.get("country") == "GB":
            if item.get("addr_full") and not item.get("postcode"):
                postcode = re.search(
                    r"(\w{1,2}\d{1,2}\w? \d\w{2})", item["addr_full"].upper()
                )
                if postcode:
                    item["postcode"] = postcode.group(1)
                else:
                    postcode = re.search(
                        r"(\w{1,2}\d{1,2}\w?) O(\w{2})", item["addr_full"].upper()
                    )
                    if postcode:
                        item["postcode"] = postcode.group(1) + " 0" + postcode.group(2)

        return item


class AssertURLSchemePipeline(object):
    def process_item(self, item, spider):
        if item.get("image"):
            if item["image"].startswith("//"):
                item["image"] = "https:" + item["image"]

        return item


class CheckItemPropertiesPipeline(object):
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
    phone_regex = re.compile(
        r"^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$",
    )
    email_regex = re.compile(r"(^[-\w_.+]+@[-\w]+\.[-\w.]+$)")
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

    def process_item(self, item, spider):
        if brand_wikidata := item.get("brand_wikidata"):
            if not isinstance(brand_wikidata, str):
                spider.crawler.stats.inc_value("atp/field/brand_wikidata/wrong_type")
            elif not self.wikidata_regex.match(brand_wikidata):
                spider.crawler.stats.inc_value("atp/field/brand_wikidata/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/brand_wikidata/missing")

        if website := item.get("website"):
            if not isinstance(website, str):
                spider.crawler.stats.inc_value("atp/field/website/wrong_type")
            elif not self.url_regex.match(website):
                spider.crawler.stats.inc_value("atp/field/website/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/website/missing")

        if image := item.get("image"):
            if not isinstance(image, str):
                spider.crawler.stats.inc_value("atp/field/image/wrong_type")
            elif not self.url_regex.match(image):
                spider.crawler.stats.inc_value("atp/field/image/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/image/missing")

        lat, lon = item.get("lat"), item.get("lon")
        if lat and lon:
            if not (self.min_lat < float(lat) < self.max_lat):
                spider.crawler.stats.inc_value("atp/field/lat/invalid")
            if not (self.min_lon < float(lon) < self.max_lon):
                spider.crawler.stats.inc_value("atp/field/lon/invalid")
            if math.fabs(float(lat)) < 0.01:
                spider.crawler.stats.inc_value("atp/field/lat/invalid")
            if math.fabs(float(lon)) < 0.01:
                spider.crawler.stats.inc_value("atp/field/lon/invalid")

        if phone := item.get("phone"):
            if not isinstance(phone, str):
                spider.crawler.stats.inc_value("atp/field/phone/wrong_type")
            elif not self.phone_regex.match(phone):
                spider.crawler.stats.inc_value("atp/field/phone/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/phone/missing")

        if email := item.get("email"):
            if not isinstance(email, str):
                spider.crawler.stats.inc_value("atp/field/email/wrong_type")
            elif not self.email_regex.match(email):
                spider.crawler.stats.inc_value("atp/field/email/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/email/missing")

        if postcode := item.get("postcode"):
            if not isinstance(postcode, str):
                spider.crawler.stats.inc_value("atp/field/postcode/wrong_type")
        else:
            spider.crawler.stats.inc_value("atp/field/postcode/missing")

        if city := item.get("city"):
            if not isinstance(city, str):
                spider.crawler.stats.inc_value("atp/field/city/wrong_type")
        else:
            spider.crawler.stats.inc_value("atp/field/city/missing")

        if brand := item.get("brand"):
            if not isinstance(brand, str):
                spider.crawler.stats.inc_value("atp/field/brand/wrong_type")
        else:
            spider.crawler.stats.inc_value("atp/field/brand/missing")

        if country := item.get("country"):
            if not isinstance(country, str):
                spider.crawler.stats.inc_value("atp/field/country/wrong_type")
        else:
            spider.crawler.stats.inc_value("atp/field/country/missing")

        if state := item.get("state"):
            if not isinstance(state, str):
                spider.crawler.stats.inc_value("atp/field/state/wrong_type")
        else:
            spider.crawler.stats.inc_value("atp/field/state/missing")

        if opening_hours := item.get("opening_hours"):
            if not isinstance(opening_hours, str):
                spider.crawler.stats.inc_value("atp/field/opening_hours/wrong_type")
            elif (
                not self.opening_hours_regex.match(opening_hours)
                and opening_hours != "24/7"
            ):
                spider.crawler.stats.inc_value("atp/field/opening_hours/invalid")
        else:
            spider.crawler.stats.inc_value("atp/field/opening_hours/missing")

        return item


class ApplyNSICategoriesPipeline(object):

    nsi = NSI()

    important_keys = ["amenity", "leisure", "shop", "tourism"]

    wikidata_cache = {}

    def process_item(self, item, spider):
        code = item.get("brand_wikidata")
        if not code:
            return item

        brand = item.get("brand", "").lower().replace(" ", "")
        extras = item.get("extras", {}).copy()

        current_keys = {}
        for key in self.important_keys:
            if value := extras.get(key):
                current_keys[key] = value

        if not self.wikidata_cache.get(code):
            self.wikidata_cache[code] = list(self.nsi.iter_nsi(code))

        matches = self.wikidata_cache.get(code)

        match = None

        if len(matches) == 0:
            spider.crawler.stats.inc_value("atp/nsi/brand_missing")
            return item
        elif len(matches) == 1:
            spider.crawler.stats.inc_value("atp/nsi/perfect_match")
            match = matches[0]
        else:
            type_possible_matches = []
            for possible_match in matches:
                match_names = [possible_match["displayName"]]
                match_names += possible_match.get("matchNames", [])
                match_names = [m.lower().replace(" ", "") for m in match_names]

                if not brand in match_names:
                    continue

                valid_match = True
                for key, value in current_keys.items():
                    if nsi_value := possible_match["tags"].get(key):
                        if value != nsi_value:
                            valid_match = False
                if valid_match:
                    type_possible_matches.append(possible_match)

            if len(type_possible_matches) == 1:
                match = type_possible_matches[0]

            if match is None:
                spider.crawler.stats.inc_value("atp/nsi/match_failed")
                return item

            spider.crawler.stats.inc_value("atp/nsi/calculated_match")

        extras["nsi_id"] = match["id"]

        for (key, value) in match["tags"].items():
            if key in self.important_keys:
                if extras.get(key) is None:
                    extras[key] = value

        # TODO: evaluate stats from next weekly run
        # item["extras"] = extras

        return item
