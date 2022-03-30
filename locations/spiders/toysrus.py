import scrapy
from locations.items import GeojsonPointItem
import json
import re
from io import StringIO
from scrapy.http import HtmlResponse

default_headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/63.0.3239.84 Safari/537.36"
}


def get_hours(hours_obj):
    out_hours = []
    for day, hours in hours_obj.items():
        if hours == "open24":
            out_hours.append("{}: 24/7".format(day))
        elif type(hours) is list:
            ranges = ["{}-{}".format(x["open"], x["close"]) for x in hours]
            out_hours.append("{}: {}".format(day, ",".join(ranges)))
    return "; ".join(out_hours)


class ToysRUsSpider(scrapy.Spider):
    name = "toysrus"
    item_attributes = {"brand": "Toys R Us"}

    def start_requests(self):
        urls = ["http://stores.toysrus.com/"]
        for url in urls:
            yield scrapy.Request(
                url=url, callback=self.parse_states, headers=default_headers
            )

    def parse_states(self, response):
        urls = response.css("a[href*='stores.toysrus.com/']")
        for url in [x.xpath("@href").extract_first(default=None) for x in urls]:
            if url and "#" not in url:
                yield scrapy.Request(
                    url=url, callback=self.parse_cities, headers=default_headers
                )

    def parse_cities(self, response):
        urls = response.css("a[href*='stores.toysrus.com/']")
        for url in [x.xpath("@href").extract_first(default=None) for x in urls]:
            if url and "#" not in url:
                yield scrapy.Request(
                    url=url, callback=self.parse, headers=default_headers
                )

    def parse(self, response):
        marker_txt = re.findall(
            re.compile(r"markerData.*\}", re.MULTILINE), response.text
        )
        if not len(marker_txt):
            return
        markers_json = r"{\"" + marker_txt[0]
        markers = list(json.loads(markers_json).values())[0]

        if not len(markers):
            return
        for marker in markers:
            marker_response = HtmlResponse(url="", body=marker["info"].encode("utf-8"))
            hours = re.findall(r"\{\"label.*\}", marker["info"])
            hours = hours[0]
            parsed_hours = json.loads(hours)

            addr_parts = marker_response.css(
                ".address span:not(.phone)::text"
            ).extract()
            url = marker_response.css("header a").xpath("@href").extract_first()
            city, state = addr_parts[-1].split(",")

            yield GeojsonPointItem(
                lat=marker.get("lat"),
                lon=marker.get("lng"),
                name=marker_response.css("header a::text").extract_first(default=None),
                addr_full=", ".join(addr_parts),
                city=city.strip(),
                state=state.strip(),
                country="United States",
                phone=marker_response.css(".phone::text").extract_first(),
                website=url,
                opening_hours=get_hours(parsed_hours["days"]),
                ref=url.split("/")[-1].split(".")[0],
            )
