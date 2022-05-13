# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class WoolworthsSpider(scrapy.Spider):
    name = "woolworths"
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q3249145"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = [
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-16.0880000&longitude=142.2948779",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-21.3302741&longitude=122.1239795",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-21.0024300&longitude=145.7226123",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-17.0567426&longitude=133.5497607",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-32.5838123&longitude=117.9052295",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-32.9533313&longitude=146.2060107",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-32.1755753&longitude=138.7792529",
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=4500&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&latitude=-42.2284848&longitude=146.3817920",
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        data = response.json()

        for i in data["Stores"]:
            properties = {
                "ref": i["StoreNo"],
                "name": i["Name"],
                "street_address": i["AddressLine1"],
                "city": i["Suburb"],
                "state": i["State"],
                "postcode": i["Postcode"],
                "country": "AU",
                "addr_full": ", ".join(
                    filter(
                        None,
                        (
                            i["AddressLine1"],
                            i["AddressLine2"],
                            i["Suburb"],
                            i["Suburb"],
                            i["State"],
                            i["Postcode"],
                            "Australia",
                        ),
                    )
                ),
                "phone": i["Phone"],
                "lat": i["Latitude"],
                "lon": i["Longitude"],
            }

            yield GeojsonPointItem(**properties)
