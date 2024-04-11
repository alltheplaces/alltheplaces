from html import unescape

from scrapy import Selector, Spider
from scrapy.http import FormRequest

from locations.hours import OpeningHours
from locations.items import Feature


class LouMalnatisPizzeriaUSSpider(Spider):
    name = "lou_malnatis_pizzeria_us"
    item_attributes = {"brand": "Lou Malnati's Pizzeria", "brand_wikidata": "Q6685628"}
    allowed_domains = ["www.loumalnatis.com"]
    start_urls = ["https://www.loumalnatis.com/resources/js/ajax_php/locatorAJAX.php"]

    def start_requests(self):
        regions = [
            ("1", "Phoenix, AZ, USA", 33.4483771, -112.0740373),
            ("2", "Rockford, IL, USA", 42.2711311, -89.0939952),
            ("3", "Milwaukee, WI, USA", 43.0389025, -87.9064736),
            ("4", "Indianapolis, IN, USA", 39.768403, -86.158068),
        ]
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
        }
        for region in regions:
            formdata = {
                "action": "getLocations",
                "latLng": "({},{})".format(region[2], region[3]),
                "distance": "100000",
                "locationName": region[1],
                "selectedFiltersArr": "",
                "region_id": region[0],
            }
            yield FormRequest(url=self.start_urls[0], formdata=formdata, headers=headers, method="POST")

    def parse(self, response):
        markers = {}
        markers_js = (
            Selector(text=response.json()["locatorNewJSHolder"]["jContentReturn"]).xpath("//script/text()").get()
        )
        for marker_js in markers_js.split("var newMarker = new Array();")[1:]:
            marker_html = Selector(text=marker_js.split('newMarker["html"] = "', 1)[1].split('";', 1)[0])
            marker_ref = marker_html.xpath('.//div[contains(@class, "sideBar_MapOrder")]/a/@href').get().split("/")[-1]
            marker_lat = marker_js.split('newMarker["lat"] = ', 1)[1].split(";", 1)[0]
            marker_lon = marker_js.split('newMarker["lng"] = ', 1)[1].split(";", 1)[0]
            markers[marker_ref] = (marker_lat, marker_lon)

        locations = Selector(text=response.json()["locatorMapList"]["jContentReturn"])
        for location in locations.xpath('//div[contains(@class, "sideBar_MapListAddress")]'):
            properties = {
                "ref": location.xpath('.//div[contains(@class, "sideBar_MapOrder")]/a/@href').get().split("/")[-1],
                "name": unescape(
                    location.xpath(
                        './/div[contains(@class, "sideBar_MapAddressElementClickable desktop-only")]/text()'
                    ).get()
                ).replace(" - Now Open!", ""),
                "addr_full": ", ".join(
                    filter(
                        None,
                        location.xpath('(.//div[@class="sideBar_MapAddressElement"]/text())[position() < 3]').getall(),
                    )
                ),
                "phone": location.xpath('.//div[@class="sideBar_MapAddressElement"]/a[contains(@href, "tel:")]/@href')
                .get()
                .replace("tel:", ""),
                "website": location.xpath('.//div[contains(@class, "sideBar_MapMoreDetails")]/a/@href').get(),
            }
            if properties["ref"] in markers.keys():
                properties["lat"], properties["lon"] = markers[properties["ref"]]
            hours_string = " ".join(
                filter(
                    None,
                    location.xpath('(.//div[@class="sideBar_MapAddressElement"]/text())[position() >= 4]').getall(),
                )
            )
            properties["opening_hours"] = OpeningHours()
            properties["opening_hours"].add_ranges_from_string(hours_string)
            yield Feature(**properties)
