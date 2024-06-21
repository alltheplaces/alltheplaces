import re

import chompjs
import scrapy
from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


# https://www.benchmarkpyramid.com/press_media/releases/benchmark-pyramid-merger/
class BenchmarkPyramidHospitalitySpider(scrapy.Spider):
    name = "benchmark_pyramid_hospitality"
    # item_attributes = {'brand': ''}   # doesn't really apply - Benchmark Hospitality is the operator or various
    # hotel franchise locations and other resort/meeting centers.
    start_urls = [
        "https://www.benchmarkrfp.com/mapTest.cfm",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        locations = []
        if match := re.search(r"locations\.push\((.+?)\);", response.text, re.DOTALL):
            locations = list(chompjs.parse_js_objects(match.group(1)))
        for location in locations:
            location_html = Selector(text=location.get("infowindow", ""))
            item = DictParser.parse(location)
            item["name"] = location.get("pointName")
            if address := location_html.xpath('//*[@class="propInfo"]//text()').getall():
                item["street_address"] = address[-1]
            website = location_html.xpath('//a[@id="exploreLink"]/@href').get()
            item["website"] = website if website else "https://www.pyramidglobal.com/portfolio"
            if "Resort" in item["name"]:
                apply_category(Categories.LEISURE_RESORT, item)
            elif "Center" in item["name"]:
                apply_category({"amenity": "conference_centre"}, item)
            else:
                apply_category(Categories.HOTEL, item)

            yield item
