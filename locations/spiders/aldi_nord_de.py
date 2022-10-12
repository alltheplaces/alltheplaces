# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem


class AldiNordDESpider(scrapy.Spider):
    name = "aldi_nord_de"
<<<<<<< HEAD
    item_attributes = {"brand": "ALDI Nord", "brand_wikidata": "Q41171373", "country": "DE"}
=======
    item_attributes = {
        "brand": "ALDI Nord",
        "brand_wikidata": "Q41171373",
        "country": "DE",
    }
>>>>>>> 4979d97c4496dcec5a47fa761ddc55cdbf7bb4cb
    allowed_domains = ["www.aldi-nord.de"]
    start_urls = [
        "https://uberall.com/api/storefinders/ALDINORDDE_UimhY3MWJaxhjK9QdZo3Qa4chq1MAu/locations/all?v=20211005&language=de&fieldMask=id&fieldMask=identifier&fieldMask=googlePlaceId&fieldMask=lat&fieldMask=lng&fieldMask=name&fieldMask=country&fieldMask=city&fieldMask=province&fieldMask=streetAndNumber&fieldMask=zip&fieldMask=businessId&fieldMask=addressExtra&",
    ]

    def parse(self, response):
<<<<<<< HEAD
        shops = response.json()['response']['locations']
        for shop in shops:
            properties = {
                "ref": shop['identifier'],
                "lat": shop['lat'],
                "lon": shop['lng'],
                "city": shop['city'],
                "state": shop['province'],
                "street_address": shop['streetAndNumber'],
                "postcode": shop['zip']
=======
        shops = response.json()["response"]["locations"]
        for shop in shops:
            properties = {
                "ref": shop["identifier"],
                "lat": shop["lat"],
                "lon": shop["lng"],
                "city": shop["city"],
                "state": shop["province"],
                "street_address": shop["streetAndNumber"],
                "postcode": shop["zip"],
>>>>>>> 4979d97c4496dcec5a47fa761ddc55cdbf7bb4cb
            }
            yield GeojsonPointItem(**properties)
