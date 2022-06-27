# -*- coding: utf-8 -*-
import scrapy
import json
from locations.brands import Brand
from locations.seo import extract_geo, extract_details


class TheBodyShopSpider(scrapy.spiders.SitemapSpider):
    name = "thebodyshop"
    brand = Brand.from_wikidata("Body Shop", "Q837851")
    allowed_domains = ["thebodyshop.com"]
    download_delay = 1.0
    sitemap_urls = ["https://www.thebodyshop.com/sitemap.xml"]
    sitemap_rules = [("/store-details/", "parse_store")]
    json_template_url = "https://api.thebodyshop.com/rest/v2/thebodyshop-{}/stores/{}"
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
        "/nl-be/": "be"
    }

    def parse_store(self, response):
        headers = {"Accept": "application/json"}
        store_id = response.url.split("/")[-1]
        for key in self.parse_pages:
            if key in response.url:
                json_url = self.json_template_url.format(
                    self.parse_pages[key], store_id
                )
                yield scrapy.Request(
                    json_url,
                    headers=headers,
                    callback=self.parse_json,
                    cb_kwargs=dict(html_response=response),
                )
                return
        self.logger.info("ignoring page: %s", response.url)

    def parse_json(self, response, html_response):
        store = json.loads(response.text)
        item = self.brand.item(html_response)
        if extract_geo(item, store["geoPoint"]).has_geo():
            address = store["address"]
            extract_details(item, address)
            item["street_address"] = address["line1"]
            item["country"] = address["country"]["isocode"]
            yield item
