import re

import scrapy
from chompjs import chompjs

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class KlierHairGroupSpider(scrapy.Spider):
    """
    Klier Hair Group is a chain of hairdressers in Germany with several brands.

    See https://www.wikidata.org/wiki/Q1465159

    This class contains the common code to scrape all their brands.
    """

    def parse(self, response, **kwargs):
        locations_re = re.compile(r"locations\.push\(\s*({.*?})\);", re.DOTALL)
        locations_javascript = response.xpath('//script/text()[contains(., "locations.push")]').re(locations_re)
        for location_javascript in locations_javascript:
            location = next(chompjs.parse_js_objects(location_javascript))
            location["id"] = location.pop("internal_id")
            location["street_address"] = location.pop("street")
            location["website"] = location.pop("sanitized")
            item = DictParser.parse(location)
            item["opening_hours"] = self.parse_opening_hours(location["business_hours"])
            apply_category(Categories.SHOP_HAIRDRESSER, item)
            yield item

    @staticmethod
    def parse_opening_hours(business_hours):
        hours = OpeningHours()
        for day in business_hours:
            if not day["closed"]:
                hours.add_range(day["openDay"], day["openTime"], day["closeTime"])
        return hours
