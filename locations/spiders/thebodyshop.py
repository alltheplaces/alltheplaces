# -*- coding: utf-8 -*-
import scrapy
import json
from locations.dict_parser import DictParser


class TheBodyShopSpider(scrapy.spiders.SitemapSpider):
    name = "thebodyshop"
    item_attributes = {
        "brand": "Body Shop",
        "brand_wikidata": "Q837851",
    }
    allowed_domains = ["thebodyshop.com"]
    download_delay = 2.0
    sitemap_urls = ["https://www.thebodyshop.com/sitemap.xml"]
    sitemap_rules = [("/store-details/", "parse_store")]

    parse_pages = {
        "/en-gb/": "uk",
        "/es-es/": "es",
        "/en-au/": "au",
        "/en-ca/": "ca",
        "/en-us/": "us",
        "/de-de/": "de",
        "/en-sg/": "sg",
        "/da-dk/": "dk",
        "/sv-se/": "se",
        "/nl-nl/": "nl",
        "/fr-fr/": "fr",
        "/pt-pt/": "pt",
        "/de-at/": "at",
    }

    def parse_store(self, response):
        store_id = response.url.split("/")[-1]
        for key in self.parse_pages:
            if key in response.url:
                yield scrapy.Request(
                    "https://api.thebodyshop.com/rest/v2/thebodyshop-{}/stores/{}".format(
                        self.parse_pages[key], store_id
                    ),
                    headers={"Accept": "application/json"},
                    callback=self.parse_json,
                    cb_kwargs=dict(html_response=response),
                )

    def parse_json(self, response, html_response):
        store = response.json()
        store["location"] = store["geoPoint"]
        item = DictParser.parse(store)
        item["ref"] = store["name"]
        item["name"] = store["displayName"]
        item["website"] = html_response.url
        item["country"] = store["address"]["country"]["isocode"]
        return item
