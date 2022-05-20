# -*- coding: utf-8 -*-
import scrapy, json
from locations.items import GeojsonPointItem


class OldChicagoSpider(scrapy.Spider):

    name = "oldchicago"
    item_attributes = {"brand": "Old Chicago", "brand_wikidata": "Q64411347"}
    allowed_domains = ["oc-api-prod.azurewebsites.com"]

    query_id = "q0"
    query_name = "locations"

    def start_requests(self):
        urls = [
            "https://oc-api-prod.azurewebsites.net/graphql/batch",
        ]
        query_all = [
            {
                "id": self.query_id,
                "query": 'query ViewerQuery {viewer {id,...F0}} fragment F0 on Viewer {%s:locations(first:150,geoString:"") {edges {node {id,slug,locationId,title,isOpen,latitude,longitude,simpleHours {days,hours,id},phone,address {route,streetNumber,stateCode,stateName,city,postalCode,id},comingSoon},cursor},pageInfo {hasNextPage,hasPreviousPage}},id}'
                % self.query_name,
            }
        ]
        for url in urls:
            yield scrapy.Request(
                url=url,
                method="POST",
                body=json.dumps(query_all),
                headers={"Content-Type": "application/json"},
                callback=self.parse,
            )

    def parse(self, response):
        response_json = response.json()
        stores = response_json[0]["payload"]["data"]["viewer"][self.query_name]["edges"]
        for loc in stores:
            node = loc["node"]
            address = node["address"]
            hours = ", ".join(
                ["%s %s" % (h["days"], h["hours"]) for h in node["simpleHours"]]
            )
            addr_full = "%s %s" % (address["streetNumber"], address["route"])
            yield GeojsonPointItem(
                ref=node["locationId"],
                lat=node["latitude"],
                lon=node["longitude"],
                addr_full=addr_full,
                housenumber=address["streetNumber"],
                street=address["route"],
                city=address["city"],
                state=address["stateCode"],
                postcode=address["postalCode"],
                opening_hours=hours,
            )
