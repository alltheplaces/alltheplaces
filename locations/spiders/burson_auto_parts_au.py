from chompjs import chompjs
from scrapy import Selector, Spider

from locations.hours import OpeningHours
from locations.items import Feature


class BursonAutoPartsAU(Spider):
    name = "burson_auto_parts_au"
    item_attributes = {"brand": "Burson Auto Parts", "brand_wikidata": "Q117075930"}
    allowed_domains = ["www.burson.com.au"]
    start_urls = ["https://www.burson.com.au/find-a-store"]

    def parse(self, response):
        raw_js = (
            response.xpath('//script[contains(text(), "var markers = ")]/text()')
            .get()
            .split("var markers = ", 1)[1]
            .split("var icon = ", 1)[0]
            .strip()[:-1]
        )
        for location in chompjs.parse_js_object(raw_js):
            location_html = Selector(text=location[1])
            properties = {
                "ref": location[0],
                "name": location_html.xpath("//h3/text()").get(),
                "lat": location[3],
                "lon": location[4],
                "addr_full": " ".join(
                    location_html.xpath('//strong[text()="Address"]/following::text()')
                    .get(default="")[2:]
                    .replace("\xa0", " ")
                    .split()
                ),
                "phone": location_html.xpath('//strong[text()="Phone"]/following::text()').get(default="")[2:],
                "email": location_html.xpath('//strong[text()="Email"]/following::text()').get(default="")[2:],
                "opening_hours": OpeningHours(),
            }
            properties["opening_hours"].add_ranges_from_string(
                location_html.xpath('//strong[text()="Hours"]/following::text()').get()[2:]
            )
            yield Feature(**properties)
