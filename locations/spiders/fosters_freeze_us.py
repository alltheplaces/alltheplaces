import chompjs
from scrapy import Spider

from locations.items import Feature


class FostersFreezeUSSpider(Spider):
    name = "fosters_freeze_us"
    item_attributes = {"brand": "Fosters Freeze", "brand_wikidata": "Q5473851"}
    start_urls = ["https://fostersfreeze.com/locations/"]

    def parse(self, response):
        js = response.xpath("//script[contains(text(), 'gMapResp')]/text()").get()
        for location in chompjs.parse_js_object(js[js.find("markers:") + 8 : js.find("'}}],") + 4]):
            html = location["html"].split("<br>")
            yield Feature(
                lat=location["latitude"],
                lon=location["longitude"],
                ref=location["key"],  # Note: not the real branch code
                branch=html[0].strip().removeprefix("Fosters Freeze, "),  # Note: not unique
                addr_full=html[1].strip(),
            )
