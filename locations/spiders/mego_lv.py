import chompjs
from scrapy import Spider
from scrapy.http import HtmlResponse

from locations.hours import OpeningHours
from locations.items import Feature


class MegoLV(Spider):
    name = "mego_lv"
    start_urls = ["https://mego.lv/en/contact-information"]
    item_attributes = {"brand_wikidata": "Q16363314"}

    def parse(self, response):
        for location in chompjs.parse_js_object(response.xpath("//div[@class='map']/script/text()").get()):
            item = Feature()
            item["ref"] = location["shop_id"]
            item["lat"] = location["x"]
            item["lon"] = location["y"]
            item["street_address"] = location["address"]

            fragment = HtmlResponse(url="#" + str(location["shop_id"]), body=location["info"], encoding="utf-8")
            if hours := fragment.xpath("//p/text()").get().replace(".", ""):
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_ranges_from_string(hours)
            yield item
