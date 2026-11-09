import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class SimmonsBakersGBSpider(scrapy.Spider):
    name = "simmons_bakers_gb"
    item_attributes = {"brand": "Simmons", "brand_wikidata": "Q137041333"}
    start_urls = ["https://www.simmonsbakers.com/shops"]

    def parse(self, response, **kwargs):
        script = response.xpath('//script[contains(text(), "var markers")]/text()').get()
        markers = chompjs.parse_js_object(script.split("var markers", 1)[1].split("=", 1)[1])

        for marker in markers:
            name, lon, lat, street, town, region, postcode, phone, hours = (
                (m.strip() if isinstance(m, str) else m) for m in marker[:9]
            )
            unavailable = marker[9].strip() if len(marker) > 9 else ""
            if unavailable:
                # Site shows these as "Closed for refurbishment"
                self.logger.info(f"Skipping temporarily closed shop: {name}")
                continue

            item = Feature()
            item["ref"] = name
            item["name"] = "Simmons"
            item["branch"] = name.removeprefix("Simmons,").strip()
            item["lat"] = lat
            item["lon"] = lon
            item["street_address"] = street
            item["city"] = town
            item["state"] = region or None
            item["phone"] = phone
            item["country"] = "GB"
            item["postcode"] = postcode
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)
            apply_category(Categories.SHOP_BAKERY, item)
            yield item
