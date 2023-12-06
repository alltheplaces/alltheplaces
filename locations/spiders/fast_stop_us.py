import re
from urllib.parse import urljoin

import chompjs
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import convert_item, get_object


class FastStopUSSpider(Spider):
    name = "fast_stop_us"
    item_attributes = {"brand": "FAST STOP", "brand_wikidata": "Q116734101"}
    start_urls = ["https://www.efaststop.com/store-locator"]

    def parse(self, response, **kwargs):
        coords_map = {}
        if m := re.search(r"init_map\(.+, (\[.+\]), (\[.+\])\);", response.text):
            coords, popup = m.groups()
            lat_lon = re.compile(r"LatLng\((-?\d+\.\d+), (-?\d+\.\d+)\)")
            for location in chompjs.parse_js_object(coords):
                if ll := re.search(lat_lon, location["position"]):
                    coords_map[location["title"]] = ll.groups()

        for location in response.xpath('//section[@itemtype="http://schema.org/GasStation"]'):
            ld = convert_item(get_object(location.root))
            item = LinkedDataParser.parse_ld(ld)

            item["ref"] = item["website"] = urljoin(response.url, location.xpath(".//a/@href").get())

            if ll := coords_map.get(item["name"]):
                item["lat"], item["lon"] = ll

            apply_category(Categories.FUEL_STATION, item)

            yield item
