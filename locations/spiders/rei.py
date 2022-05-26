# -*- coding: utf-8 -*-
import json
import re

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class ReiSpider(SitemapSpider):
    name = "rei"
    allowed_domains = ["www.rei.com"]
    sitemap_urls = ["https://www.rei.com/sitemap-stores.xml"]
    sitemap_rules = [("https:\/\/www\.rei\.com\/stores\/[-\w]+$", "parse_store")]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"] != "https://www.rei.com/stores/bike-shop":
                yield entry

    # Fix formatting for ["Mon - Fri 10:00-1800","Sat 12:00-18:00"]
    def format_days(self, range):
        pattern = r"^(.{3})( - (.{3}) | )(\d.*)"
        start_day, seperator, end_day, time_range = re.search(
            pattern, range.strip()
        ).groups()
        result = DAY_MAPPING[start_day]
        if end_day:
            result += "-" + DAY_MAPPING[end_day]
        result += " " + time_range
        return result

    def fix_opening_hours(self, opening_hours):
        return ";".join(map(self.format_days, opening_hours))

    def parse_store(self, response):
        json_string = response.xpath(
            '//script[@id="store-schema"][@type="application/ld+json"]/text()'
        ).extract_first()
        store_dict = json.loads(json_string)

        # The above dict has more clearly laid-out info, but doesn't include storeId or country, which is found here:
        store_id_js_text = str(
            response.xpath('//script[@id="modelData"]/text()').extract_first()
        )
        store_data_model = json.loads(store_id_js_text)["pageData"]["storeDataModel"]

        properties = {
            "lat": store_dict["geo"].get("latitude"),
            "lon": store_dict["geo"].get("longitude"),
            "addr_full": store_dict["address"].get("streetAddress"),
            "city": store_dict["address"].get("addressLocality"),
            "state": store_dict["address"].get("addressRegion"),
            "postcode": store_dict["address"].get("postalCode"),
            "country": store_data_model.get("countryCode"),
            "opening_hours": self.fix_opening_hours(store_dict["openingHours"]),
            "phone": store_dict.get("telephone"),
            "website": store_dict.get("url"),
            "ref": store_data_model.get("storeNumber"),
        }

        yield GeojsonPointItem(**properties)
