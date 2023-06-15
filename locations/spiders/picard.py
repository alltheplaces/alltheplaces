import re

import scrapy

from locations.hours import OpeningHours
from locations.items import Feature


class PicardSpider(scrapy.Spider):
    name = "picard"
    item_attributes = {"brand": "Picard Surgelés", "brand_wikidata": "Q3382454"}
    allowed_domains = ["magasins.picard.fr"]
    start_urls = [
        "https://magasins.picard.fr/locationsitemap1.xml",
        "https://magasins.picard.fr/locationsitemap2.xml",
        "https://magasins.picard.fr/locationsitemap3.xml",
    ]

    def parse_stores(self, response):
        full_address = response.css("address.lf-parts-address div::text").getall()
        properties = {
            "ref": re.search(r".+/(.+?)/?(?:\.html|$)", response.url).group(1),
            "name": response.xpath('//*[@id="libelle-magasin"]/text()').extract_first(),
            "addr_full": " ".join([line.strip() for line in full_address if line.strip()]),
            "city": full_address[2].split()[1].strip(),
            "postcode": full_address[2].split()[0].strip(),
            "country": "FR",
            "phone": response.css("a.lf-parts-phone__button span.lf-button-text__label::text").get(),
            "website": response.url,
        }
        yield Feature(**properties)

    def parse(self, response):
        xml = scrapy.selector.Selector(response)
        xml.remove_namespaces()

        urls = xml.xpath("//loc/text()").extract()
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_stores)
