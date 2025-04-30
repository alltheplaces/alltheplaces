import scrapy
from geonamescache import GeonamesCache

from locations.items import Feature


class DavitaSpider(scrapy.Spider):
    name = "davita"
    item_attributes = {"operator": "DaVita Dialysis", "operator_wikidata": "Q5207184", "country": "US"}
    allowed_domains = ["davita.com"]

    def start_requests(self):
        for state in GeonamesCache().get_us_states():
            yield scrapy.Request(
                url=f"https://www.davita.com/api/find-a-center?location={state}&p=1&lat=32.3182314&lng=-86.902298"
            )

    def parse(self, response):
        data = response.json()
        for location in data.get("locations", []) or []:
            properties = {
                "name": location["facilityname"],
                "ref": location["facilityid"],
                "street_address": location["address"]["address1"],
                "city": location["address"]["city"],
                "state": location["address"]["state"],
                "postcode": location["address"]["zip"],
                "phone": location.get("phone"),
                "website": f'https://davita.com/locations/{location["facilityid"]}',
                "lat": location["address"].get("latitude"),
                "lon": location["address"].get("longitude"),
            }

            yield Feature(**properties)
