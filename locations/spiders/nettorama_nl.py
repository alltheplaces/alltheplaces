from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class NettoramaNLSpider(Spider):
    name = "nettorama_nl"
    item_attributes = {"brand": "Nettorama", "brand_wikidata": "Q1828639"}
    start_urls = [
        'https://www.nettorama.nl/api/v1.0/location?zipcode=&filter[]={"c":"id","v":35,"o":"<>","filter_type":"FieldFilter"}&filter[]={"c":"id","v":36,"o":"<>","filter_type":"FieldFilter"}&filter[]={"c":"state","v":"Online","o":"=","filter_type":"FieldFilter"}'
    ]
    # Filters drop office, warehouse and deleted stores

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for d in response.json()["data"]:
            location = d["data"]
            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location["title"]
            item["email"] = location["emailaddress"]
            item["phone"] = location["phonenumber"]
            item["extras"]["fax"] = location["faxnumber"]
            item["lat"] = location["coord_latitude"]
            item["lon"] = location["coord_longitude"]

            item["housenumber"] = "".join(filter(None, [location["address_housenumber"],location["address_housenumber_suffix"]]))
            item["street"] = location["address_street"]
            item["postcode"] = location["address_zipcode"]
            item["city"] = location["address_place"]
            item["country"] = location["address_country"]

            item["extras"]["ref:google:place_id"] = location["googleplaces_id"]

            item["website"] = "https://www.nettorama.nl/locaties/{}".format(location["access"])

            apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
