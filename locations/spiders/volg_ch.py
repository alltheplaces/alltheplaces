import re

import scrapy

from locations.categories import Categories, apply_category
from locations.geo import point_locations
from locations.items import GeojsonPointItem


class VolgCHSpider(scrapy.Spider):
    name = "volg_ch"
    item_attributes = {"brand": "Volg", "brand_wikidata": "Q2530746"}
    allowed_domains = ["www.volg.ch"]

    def start_requests(self):
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", ["CH"]):
            yield scrapy.FormRequest(
                url="https://www.volg.ch/standorte-oeffnungszeiten/action/suche/",
                callback=self.parse_list,
                formdata={
                    "tx_kochvolgstores_storelist[latitude]": lat,
                    "tx_kochvolgstores_storelist[longitude]": lon,
                    "tx_kochvolgstores_storelist[location]": "",
                },
            )

    def parse_list(self, response):
        for link in response.css("div.c-location-list__link").xpath("a/@href").extract():
            yield response.follow(link.split("?")[0], self.parse_store)

    def parse_store(self, response):
        # The site displays opening hours for the next seven days, but without telling
        # whether these are exceptional or regular. So we don't extract any hours.
        marker = response.css(".map-marker")
        text = marker.xpath("@data-text").get()
        lines = [line.strip() for line in text.split("<br />")]
        item = GeojsonPointItem(
            city=lines[2],
            country="CH",
            extras=self.parse_extras(response),
            lat=float(marker.xpath("@data-lat").get()),
            lon=float(marker.xpath("@data-lng").get()),
            name="Volg",
            phone=self.parse_phone(response),
            ref=response.url.split("/")[-2].removeprefix("volg-"),
            street_address=lines[1],
            website=response.url,
        )
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item

    @staticmethod
    def parse_extras(response):
        extras = {}
        services = response.css(".c-location-offer").get()
        if "Postagentur" in services:
            extras.update(
                {
                    "post_office": "post_partner",
                    "post_office:brand": "Die Post",
                    "post_office:brand:wikidata": "Q614803",
                }
            )
        if "Heimlieferservice" in services:
            extras.update(
                {
                    "delivery": "yes",
                    "delivery:partner": "Die Post",
                    "delivery:partner:wikidata": "Q614803",
                }
            )
        return extras

    @staticmethod
    def parse_phone(response):
        if m := re.search(r'<a href="tel:([0-9\s\+]+)"', response.text):
            return m.group(1)
        else:
            return None
