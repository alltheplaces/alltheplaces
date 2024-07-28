import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours


class PrixQualityITSpider(scrapy.Spider):
    name = "prix_quality_it"
    start_urls = [
        # Utilises Wordpress' Advanced Custom Fields. Unfortunately this means little commonality in types or fields,
        # beyond using a DictParser in the "acf" record and some of the url patterns
        "https://www.prixquality.com/wp-json/acf/v3/shop?per_page=999&orderby=title",
    ]
    time_format = "%H:%M"
    item_attributes = {"brand": "Prix Quality", "brand_wikidata": "Q61994819"}

    def parse(self, response):
        for record in response.json():
            store = record["acf"]
            item = DictParser.parse(store)
            item["ref"] = store["shop_code"]
            item["name"] = store["shop_name"]
            # 'latlng': {'address': "VIA MARCONI, 157/1 VO' EUGANEO", 'lat': '45.3273025', 'lng': '11.6391062', 'zoom': 14, 'street_number': '157', 'street_name': 'Via G. Marconi', 'street_short_name': 'Via G. Marconi', 'city': "Vo'", 'state': 'Veneto', 'state_short': 'Veneto', 'post_code': '35030', 'country': 'Italy', 'country_short': 'IT', 'place_id': 'EipWaWEgRy4gTWFyY29uaSwgMTU3LzEsIDM1MDMwIFZvJyBQRCwgSXRhbHkiHRobChYKFAoSCcXwLrvAIX9HEY7Fr5NIUwpkEgEx'},
            address = store["latlng"]
            item["state"] = address["state"]
            item["country"] = address["country_short"]
            item["lat"] = address["lat"]
            item["lon"] = address["lng"]
            item["housenumber"] = address["street_number"]
            item["street"] = address["street_name"]
            item["postcode"] = address["post_code"]

            # 'shop_services': ['0', '0', 'invoice', 'pos', 'air', 'access', 'parking']

            item["opening_hours"] = OpeningHours()
            for day in DAYS_IT:
                if times := store.get(day.lower(), "").replace(" - ", "-"):
                    if len(times.split("-")) == 2:
                        item["opening_hours"].add_range(DAYS_IT[day], *times.split("-"), time_format=self.time_format)

            yield item
