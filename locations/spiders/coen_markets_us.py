from scrapy import Spider

from locations.hours import OpeningHours
from locations.items import Feature


class CoenMarketsUSSpider(Spider):
    name = "coen_markets_us"
    item_attributes = {"name": "Coen", "brand": "Coen Markets Inc", "brand_wikidata": "Q122856721"}
    allowed_domains = ["www.coenmarkets.com"]
    start_urls = ["https://www.coenmarkets.com/locations/?location_city=10000&zip_radius=10000"]

    def parse(self, response):
        markers = {}
        for marker in response.xpath('//div[contains(@class, "js-map-marker")]'):
            marker_id = marker.xpath(".//@data-title").get()
            markers[marker_id] = {}
            markers[marker_id]["lat"] = marker.xpath(".//@data-lat").get()
            markers[marker_id]["lon"] = marker.xpath(".//@data-lng").get()
            markers[marker_id]["ref"] = (
                marker.xpath('.//h4[contains(@class, "location-title")]/text()').get().split(" ", 1)[0]
            )
            markers[marker_id]["name"] = " ".join(
                marker.xpath('.//h4[contains(@class, "location-title")]/text()').get().split(" ")[2:]
            )
            markers[marker_id]["addr_full"] = marker.xpath('.//p[contains(@class, "location-address")]/text()').get()
        for marker in response.xpath('.//div[contains(@class, "acf-map-popup")]'):
            marker_id = marker.xpath(".//@data-title").get()
            markers[marker_id]["phone"] = marker.xpath('.//h6[contains(@class, "phone")]/text()').get()
            hours_string = "Mon - Sun: " + marker.xpath('.//h6[contains(@class, "hours")]/text()').get()
            markers[marker_id]["opening_hours"] = OpeningHours()
            markers[marker_id]["opening_hours"].add_ranges_from_string(hours_string)
        for marker in markers.values():
            yield Feature(**marker)
