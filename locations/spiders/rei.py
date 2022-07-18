# -*- coding: utf-8 -*-
import json
import re

from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class ReiSpider(SitemapSpider):
    name = "rei"
    item_attributes = {"brand": "REI", "brand_wikidata": "Q3414933", "country": "US"}
    allowed_domains = ["www.rei.com"]
    sitemap_urls = ["https://www.rei.com/sitemap-stores.xml"]
    sitemap_rules = [("https:\/\/www\.rei\.com\/stores\/[-\w]+$", "parse_store")]
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"
    }

    def sitemap_filter(self, entries):
        for entry in entries:
            if not entry["loc"] in [
                "https://www.rei.com/stores/bike-shop",
                "https://www.rei.com/stores/ski-snowboard-shop",
                "https://www.rei.com/stores/rentals",
                "https://www.rei.com/stores/map",
            ]:
                yield entry

    # Fix formatting for ["Mon - Fri 10:00-1800","Sat 12:00-18:00"]
    def format_days(self, range):
        pattern = r"^(.{3})( - (.{3}) | )(\d.*)"
        start_day, seperator, end_day, time_range = re.search(
            pattern, range.strip()
        ).groups()
        result = start_day[:2]
        if end_day:
            result += "-" + end_day[:2]
        result += " " + time_range
        return result

    def fix_opening_hours(self, opening_hours):
        return "; ".join(map(self.format_days, opening_hours))

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
            "name": store_dict["name"],
            "street_address": store_dict["address"].get("streetAddress"),
            "city": store_dict["address"].get("addressLocality"),
            "state": store_dict["address"].get("addressRegion"),
            "postcode": store_dict["address"].get("postalCode"),
            "opening_hours": self.fix_opening_hours(store_dict["openingHours"]),
            "phone": store_dict.get("telephone"),
            "website": response.url,
            "ref": store_data_model.get("storeNumber"),
        }

        yield GeojsonPointItem(**properties)
