from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CbrfreeAUSpider(Spider):
    name = "cbrfree_au"
    item_attributes = {"operator": "Government of the Australian Capital Territory", "operator_wikidata": "Q27220504"}
    allowed_domains = ["www.google.com"]
    start_urls = [
        "https://www.google.com/maps/d/embed?mid=1KiDsTVMHb_DsRtT2J_mI364o9d6iPeW0&ll=-35.31163605596965%2C149.1047475&z=10"
    ]

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var _pageData = ")]/text()').get()
        js_blob = js_blob.split('var _pageData = "', 1)[1].split('";', 1)[0]
        indoor_hotspots = parse_js_object(js_blob)[1][6][0][4][0][6]
        outdoor_mesh_hotspots = parse_js_object(js_blob)[1][6][1][4][0][6]
        outdoor_hotspots = parse_js_object(js_blob)[1][6][2][4][0][6]
        all_hotspots = indoor_hotspots + outdoor_mesh_hotspots + outdoor_hotspots
        for hotspot in all_hotspots:
            properties = {
                "ref": hotspot[5][0][0].replace('\\"', ""),
                "lat": hotspot[4][0][1][0],
                "lon": hotspot[4][0][1][1],
                "state": "Australian Capital Territory",
                "extras": {
                    "internet_access": "wlan",
                    "internet_access:fee": "no",
                    "internet_access:operator": "iiNet",
                    "internet_access:operator:wikidata": "Q16252604",
                    "internet_access:ssid": "CBRfree WiFi",
                },
            }
            apply_category(Categories.ANTENNA, properties)
            yield Feature(**properties)
