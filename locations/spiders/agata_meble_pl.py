import json

import scrapy

from locations.dict_parser import DictParser


class AgataMeblePLSpider(scrapy.Spider):
    name = "agata_meble_pl"
    item_attributes = {"brand": "Agata Meble", "brand_wikidata": "Q9141928"}

    def start_requests(self):
        url = "https://www.agatameble.pl/graphql"
        query = """
        query PickupLocations($deviceType: Int!) {
          pickupLocations(pageSize: 1000) {
            total_count
            items {
              city
              latitude
              longitude
              name
              phone
              pickup_location_code
              postcode
              street
              is_megabox_location_active
              url_key
              opening_hours {
                monday_friday_hours
                saturday_hours
                sunday_hours
              }
              salon_data {
                salon_code
                salon_id
                salon_name
              }
            }
          }
          getStoresBanners(input: {
            type: $deviceType
            source_code: ""
            listing: true
          }) {
            top_banner {
              image
              url
            }
          }
        }
        """

        payload = {"query": query, "operationName": "PickupLocations", "variables": {"deviceType": 1}}

        headers = {"Content-Type": "application/json"}

        yield scrapy.Request(url=url, method="POST", body=json.dumps(payload), headers=headers, callback=self.parse)

    def parse(self, response):
        for location in response.json()["data"]["pickupLocations"]["items"]:
            item = DictParser.parse(location)
            item["website"] = item["ref"] = "https://www.agatameble.pl/sklep/" + location["url_key"]
            yield item
