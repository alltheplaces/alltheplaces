# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from locations.items import GeojsonPointItem
import json
from w3lib.html import remove_tags

STATES = [
    "al",
    "ak",
    "az",
    "ar",
    "ca",
    "co",
    "ct",
    "dc",
    "de",
    "fl",
    "ga",
    "hi",
    "id",
    "il",
    "in",
    "ia",
    "ks",
    "ky",
    "la",
    "me",
    "md",
    "ma",
    "mi",
    "mn",
    "ms",
    "mo",
    "mt",
    "ne",
    "nv",
    "nh",
    "nj",
    "nm",
    "ny",
    "nc",
    "nd",
    "oh",
    "ok",
    "or",
    "pa",
    "ri",
    "sc",
    "sd",
    "tn",
    "tx",
    "ut",
    "vt",
    "va",
    "wa",
    "wv",
    "wi",
    "wy",
]  # U.S States

HEADERS = {"Referer": "https://stores.joann.com"}


class JoAnnFabricsSpider(scrapy.Spider):
    name = "joann_fabrics"
    item_attributes = {"brand": "Jo-Ann Fabrics", "brand_wikidata": "Q6203968"}
    allowed_domains = ["www.joann.com", "stores.joann.com"]

    def start_requests(self):
        """Yields a scrapy.Request object for each state in the USA"""
        base_url = "https://stores.joann.com/{}"

        for state in STATES:
            state_url = base_url.format(state)
            request = scrapy.Request(
                state_url, callback=self.parse_state, headers=HEADERS
            )
            request.meta["state"] = state
            yield request

    def parse_state(self, response):
        """Yields a scrapy.Request object for each city with a store in the state"""
        state_url = "stores.joann.com/{}*".format(response.meta["state"])
        extractor = LinkExtractor(allow=state_url)

        for link in extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse_city, headers=HEADERS)

    def parse_city(self, response):
        """Yields a scrapy.Request for the store information page for each store in the city"""
        stores = response.xpath('//a[@linktrack="Landing page"]/@href').extract()
        for store in stores:

            yield scrapy.Request(store, callback=self.parse_store_data, headers=HEADERS)

    def parse_store_data(self, response):
        """Yield a GeojsonPointItem of the store's data"""  # Pull the data off the stores page
        store = json.loads(
            remove_tags(
                response.xpath('//script[@type="application/ld+json"]')[1:].extract()[0]
            )
        )
        store_hours = self.hours(store)
        yield GeojsonPointItem(
            ref=store["url"],
            lat=store["geo"]["latitude"],
            lon=store["geo"]["longitude"],
            addr_full=store["address"]["streetAddress"],
            city=store["address"]["addressLocality"],
            state=store["address"]["addressRegion"],
            postcode=store["address"]["postalCode"],
            name=store["branchOf"]["name"],
            phone=store["telephone"],
            opening_hours=store_hours,
        )

    def hours(self, store_json_data):
        """Returns a string of the store hours in openstreetmap format"""
        hours = ""  # Ex: Mo 9:00-19:00; Tu 8:00-13:00;

        for open_hours in store_json_data["openingHoursSpecification"]:
            day_abrev = open_hours["dayOfWeek"][0][:2]
            opens = open_hours["opens"]
            closes = open_hours["closes"]
            hours += day_abrev + " " + opens + "-" + closes + "; "
        return hours
