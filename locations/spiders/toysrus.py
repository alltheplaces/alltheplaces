import scrapy
from scrapy.spiders import BaseSpider
from locations.items import GeojsonPointItem
import json
import re
from io import StringIO
from scrapy.http import HtmlResponse

default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.84 Safari/537.36"}


class ToysRUsSpider(BaseSpider):
    name = "toysrus"

    def start_requests(self):
        urls = [
            'http://stores.toysrus.com/'
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_states, headers=default_headers)

    def parse_states(self, response):
        urls = response.css("a[href*='stores.toysrus.com/']")
        for url in [x.xpath("@href").extract_first(default=None) for x in urls]:
            if url and "#" not in url:
                yield scrapy.Request(url=url, callback=self.parse_cities, headers=default_headers)

    def parse_cities(self, response):
        urls = response.css("a[href*='stores.toysrus.com/']")
        for url in [x.xpath("@href").extract_first(default=None) for x in urls]:
            if url and "#" not in url:
                yield scrapy.Request(url=url, callback=self.parse_map, headers=default_headers)

    def parse_map(self, response):
        marker_txt = re.findall(re.compile("markerData.*\}", re.MULTILINE), response.body_as_unicode())
        if not len(marker_txt):
            return
        markers_json = "{\"" + marker_txt[0]
        markers = list(json.loads(markers_json).values())[0]

        if not len(markers):
            return
        for marker in markers:
            marker_response = HtmlResponse(url="", body=marker["info"].encode("utf-8"))
            addr_parts = marker_response.css(".address span:not(.phone)::text").extract()
            # split_street = addr_parts[0].split(" ")
            # house_number, street = split_street[0].strip(), " ".join(split_street[1:])
            hours = {x.css(".daypart::text").extract_first(): [x.css(".time-open::text").extract_first(),
                                                               x.css(".time-close::text").extract_first()]
                     for x in marker_response.css(".day-hour-row")}
            url = marker_response.css("header a").xpath("@href").extract_first()
            yield GeojsonPointItem(lat=marker.get("lat"), lon=marker.get("lng"),
                                   name=marker_response.css("header a::text").extract_first(default=None),
                                   addr_full=", ".join(addr_parts),
                                   # housenumber=house_number,
                                   # street=street.strip(),
                                   city=addr_parts[1].strip(),
                                   state=addr_parts[1].strip(),
                                   country="United States",
                                   phone=marker_response.css(".phone::text").extract_first(),
                                   website=url,
                                   opening_hours=hours,
                                   ref=url.split("/")[-1].split(".")[0])
