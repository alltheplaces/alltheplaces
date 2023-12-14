import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class ChurchsChickenSpider(scrapy.Spider):
    name = "churchs_chicken"
    item_attributes = {"brand": "Church's Chicken", "brand_wikidata": "Q1089932"}
    allowed_domains = ["locations.churchs.com"]
    start_urls = ("https://locations.churchs.com/sitemap.xml",)

    def parse_store(self, response):
        if response.url == "https://locations.churchs.com/index.html":
            return  # not found, redirects

        ref = re.search(r".*\/([0-9]+[a-z\-]+)", response.url).group(1)
        name = response.xpath("//span[@class='LocationName-geo']/text()").extract_first()
        addr_full = response.xpath("//meta[@itemprop='streetAddress']/@content").extract_first()
        city = response.xpath("//meta[@itemprop='addressLocality']/@content").extract_first()
        postcode = response.xpath("//span[@itemprop='postalCode']/text()").extract_first()
        geo_region = response.xpath("//meta[@name='geo.region']/@content").extract_first().split("-")
        coordinates = response.xpath("//meta[@name='geo.position']/@content").extract_first().split(";")
        phone = response.xpath("//div[@class='Phone-display Phone-display--withLink']/text()").extract_first()

        properties = {
            "ref": ref,
            "name": name,
            "street_address": addr_full,
            "city": city,
            "postcode": postcode,
            "state": geo_region[1],
            "country": geo_region[0],
            "lat": coordinates[0],
            "lon": coordinates[1],
            "phone": phone,
            "website": response.url,
        }

        apply_category(Categories.FAST_FOOD, properties)

        yield Feature(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//loc").re(r"https://locations.churchs.com\/[a-z]{2}\/[a-z\-]+\/[0-9]+[a-z\-]+")
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
