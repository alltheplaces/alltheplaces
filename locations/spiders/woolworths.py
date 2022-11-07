import scrapy

from locations.items import GeojsonPointItem


class WoolworthsSpider(scrapy.Spider):
    name = "woolworths"
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q3249145"}
    allowed_domains = ["woolworths.com.au"]
    start_urls = [
        "https://www.woolworths.com.au/apis/ui/StoreLocator/Stores?Max=10000&Division=SUPERMARKETS,PETROL,CALTEXWOW,AMPOLMETRO,AMPOL&Facility=&postcode=*"
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
