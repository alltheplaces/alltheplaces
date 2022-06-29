# -*- coding: utf-8 -*-
import scrapy

from locations.items import GeojsonPointItem


class AsdaSpider(scrapy.Spider):
    name = "asda"
    item_attributes = {"brand": "Asda", "brand_wikidata": "Q297410", "country": "GB"}
    allowed_domains = ["virtualearth.net"]
    start_urls = (
        "https://spatial.virtualearth.net/REST/v1/data/2c85646809c94468af8723dd2b52fcb1/AsdaStoreLocator/asda_store"
        "?key=AtAs6PiQ3e0HE187rJgUEqvoKcKfTklRKTvCN1X1mpumYE-Z4VQFvx62X7ff13t6"
        "&$filter=country%20eq%20%27United%20Kingdom%27"
        "&$select=Latitude,Longitude,name,street,town,county,region,post_code,country,telephone,url_key,"
        "store_photo_url,imp_id,asda_store_type"
        "&$top=250"
        "&$format=json"
        "&$skip=",
    )

    def parse(self, response):
        if response.meta.get("start"):
            start = response.meta["start"]
        else:
            start = 250

        shops = response.json()["d"]["results"]
        for place in shops:
            yield GeojsonPointItem(
                lat=place["Latitude"],
                lon=place["Longitude"],
                name=place["name"],
                addr_full=", ".join(
                    filter(
                        None,
                        [
                            place["street"],
                            place["town"],
                            place["county"],
                            place["region"],
                            place["post_code"],
                            place["country"],
                        ],
                    )
                ),
                street_address=place["street"],
                postcode=place["post_code"],
                city=place["town"],
                phone="+44 " + place["telephone"][1:],
                website="https://storelocator.asda.com/store/"
                + place[
                    "url_key"
                ],  # Unfortunately this is a redirect, not the canonical URL
                image=place[
                    "store_photo_url"
                ],  # TODO: find the root url for the images
                ref=place["imp_id"],
                brand="Asda " + place["asda_store_type"],
            )

        if len(shops) == 250:
            yield scrapy.Request(
                self.start_urls[0] + str(start),
                callback=self.parse,
                meta={"start": start + 250},
            )
