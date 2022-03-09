# -*- coding: utf-8 -*-
import scrapy
import json
import re
from locations.items import GeojsonPointItem

DAY_MAPPING = {
    "Mon": "Mo",
    "Tue": "Tu",
    "Wed": "We",
    "Thu": "Th",
    "Fri": "Fr",
    "Sat": "Sa",
    "Sun": "Su",
}


class ReiSpider(scrapy.Spider):
    name = "rei"
    allowed_domains = ["www.rei.com"]
    start_urls = ("https://www.rei.com/stores/map",)

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
            '//script[@id="store-schema"]/text()'
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

    def parse(self, response):
        urls = set(
            response.xpath(
                '//a[contains(@href,"stores") and contains(@href,".html")]/@href'
            ).extract()
        )
        for path in urls:
            if path == "/stores/bikeshop.html":
                continue

            yield scrapy.Request(
                response.urljoin(path),
                callback=self.parse_store,
            )
