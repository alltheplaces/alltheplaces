import json

from scrapy import Request, Spider
from scrapy.http import Response

from locations.geo import point_locations
from locations.hours import DAYS_PL, OpeningHours
from locations.items import Feature


class DealzPLSpider(Spider):
    name = "dealz_pl"
    item_attributes = {"brand": "Dealz", "brand_wikidata": "Q16942585"}

    def start_requests(self):
        # Fifty closest shops are returned
        for lat, lon in point_locations("eu_centroids_120km_radius_country.csv", "PL"):
            yield Request(url=f"https://www.dealz.pl/sklepy/?lat={lat}&lng={lon}")

    def parse(self, response: Response, **kwargs):
        shops = json.loads(response.xpath("//div/@shops-map-markers").get())
        for shop in shops:
            properties = {
                "lat": shop["coordinates"]["lat"],
                "lon": shop["coordinates"]["lng"],
                "ref": shop["shop_id"],
            }
            shop_div = response.xpath(f'//div[@shops-map-marker-html={shop["shop_id"]}]')
            if not shop_div:
                continue
            address = shop_div.xpath("div/div[contains(@class, 'leaflet-popup__data')]/text()").get()
            address = address.strip()

            address_parts = list(map(str.strip, address.split(",")))
            properties["street_address"] = address_parts[0]
            post_code_city = address_parts[-1]
            properties["postcode"] = post_code_city.split(" ")[0]
            properties["city"] = " ".join(post_code_city.split(" ")[1:])
            properties["opening_hours"] = OpeningHours()
            for hours in shop_div.xpath("div/div[contains(@class, 'leaflet-popup__footer')]/text()").getall():
                properties["opening_hours"].add_ranges_from_string(hours, days=DAYS_PL)
            yield Feature(**properties)
