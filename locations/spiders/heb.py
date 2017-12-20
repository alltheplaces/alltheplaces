import scrapy
from locations.items import GeojsonPointItem
import json
import re
from scrapy.http import HtmlResponse
from xml.dom import minidom
import ast


def get_hours(sidebar):
    try:
        hours = []
        ret = []
        is_hours = False
        for hour in sidebar:
            if hour.strip().startswith("Store Hours"):
                is_hours = True
                continue
            if is_hours:
                if "AM" in hour or "PM" in hour:
                    hours.append(hour)
                else:
                    break
        for hour in hours:
            hour = hour.strip()
            range, start, _, _, _, end, _ = hour.split(" ")
            split_end = end.split(":")
            new_end = "%02d:%s" % (int(split_end[0]) + 12, split_end[1])
            if "-" in range:
                new_range = "{}-{}".format(*[x[:2] for x in range.split("-")])
            else:
                new_range = range[:2]
            ret.append("{} {}-{}".format(new_range, start, new_end))
        return "; ".join(ret)
    except:
        pass


class HEBSpider(scrapy.Spider):
    name = "heb"

    start_urls = ["https://www.heb.com/sitemap/storeSitemap.xml"]

    def parse(self, response):
        document = minidom.parseString(response.body_as_unicode())
        for url in (node.firstChild.nodeValue for node in document.getElementsByTagName("loc")):
            yield scrapy.Request(url=url, callback=self.parse_store, meta={"url": url})

    def parse_store(self, response):
        dat = re.findall(r"search_createMapPin\(.*\);", response.body_as_unicode())
        if len(dat):
            pin_call = dat[0]
            store_str = pin_call[len("search_createMapPin("):-2]
            if len(store_str.split(",")) == 17:
                _, url, lat, lon, _, _, name, address, city, state, zip, _, phone, _, _, _, _ = store_str.split(",")
                if lat and lon:
                    sidebar = response.css(".hoursDetail span::text, .hoursDetail p:not(:contains('\t'))::text").extract()
                    yield GeojsonPointItem(
                        lat=lat,
                        lon=lon,
                        name=name.strip('"'),
                        addr_full=address.strip('"'),
                        city=city.strip('"'),
                        state=state.strip('"'),
                        postcode=zip.strip('"'),
                        phone=phone.replace(" - ", "-").strip('"'),
                        website=response.meta.get("url"),
                        opening_hours=get_hours(sidebar),
                        ref=response.meta.get("url")
                    )
