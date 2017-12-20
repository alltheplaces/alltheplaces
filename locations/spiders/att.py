import scrapy
from scrapy.spiders import BaseSpider
from locations.items import GeojsonPointItem
import json
import re
from io import StringIO
from scrapy.http import HtmlResponse
from xml.dom import minidom

default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.84 Safari/537.36"}

def process_hours(result):
    ret = []
    # for days in hours_str.split(", "):
    #     range, hours = days.split(" ")
    #     start_range, end_range = range.split("-")
    #     start_split, end_split = start_range.split(":"), end_range.split(":")
    #     start_split[0] = start_split[0].zfill(2)
    #     end_split[0] = "%02d" % (int(end_split[0]) + 12)
    #     range = "-".join(x[:2].title() for x in range.split("-"))
    for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
        open, close = result[day.lower+"_open"],result[day.lower+"_close"]
        if "-1" not in (open, close):
            ret.append("{} {}-{}".format(day[:2], open, close))

    return "; ".join(ret)

class ATTScraper(scrapy.Spider):
    name = "toysrus"

    start_urls = ['https://www.att.com/sitemapfiles/stores-sitemap.xml']
    api_base = "https://www.att.com/apis/maps/v2/locator/place/cpid/{}.json"

    def parse(self, response):
        document = minidom.parseString(response.body_as_unicode())
        for loc in document.getElementsByTagName("loc"):
            url = loc.firstChild.nodeValue
            store_id = url.split("/")[-1]
            yield scrapy.Request(url=self.api_base.format(store_id), callback=self.parse_location)

    def parse_location(self, response):
        store_data = json.loads(response.body_as_unicode())
