import json
import re

import scrapy

from locations.items import Feature


class PartyCitySpider(scrapy.Spider):
    name = "party_city"
    item_attributes = {"brand": "Party City", "brand_wikidata": "Q7140896"}
    allowed_domains = ["stores.partycity.com"]
    start_urls = ("https://stores.partycity.com/sitemap.xml",)
    download_delay = 0.2

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = response.xpath("//url/loc/text()").extract()
        for url in urls:
            if re.match(r"(.*.html)", url):
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        # Handle redirects to map page, majority are regular store detail pages
        if response.request.meta.get("redirect_urls"):
            for map_item in response.xpath("//div[@class='map-list-item']"):
                properties = self.parse_map_page(map_item)
                yield Feature(**properties)
        else:
            script = json.loads(
                response.xpath(
                    '//script[@type="application/ld+json" and contains(text(), "streetAddress")]/text()'
                ).extract_first()
            )
            data = script[0]
            ref = re.search(r".+/.+?([0-9]+).html", response.url).group(1)

            properties = {
                "ref": ref,
                "name": response.xpath('(//span[@class="location-name fc-black bold"])[1]/text()').extract_first(),
                "street_address": data.get("address").get("streetAddress").strip(),
                "city": data.get("address").get("addressLocality").strip(),
                "state": data.get("address").get("addressRegion").strip(),
                "country": response.xpath(
                    '//body[contains(@class,"loading-search-result")]/@data-country-code'
                ).extract_first(),
                "postcode": data.get("address").get("postalCode"),
                "lat": data.get("geo").get("latitude"),
                "lon": data.get("geo").get("longitude"),
                "phone": data.get("address").get("telephone"),
                "website": response.request.url,
            }

            yield Feature(**properties)

    def parse_map_page(self, element):
        # Use the store urls for the ref even if it redirects, it's still unique and consistent with parse_store refs
        ref_url = element.xpath(".//a[@class='gaq-link address-link']/@href").extract_first()
        ref = re.search(r".+/.+?([0-9]+).html", ref_url).group(1)
        name = element.xpath(".//span[@class='location-name fc-black bold']/text()").extract_first()
        street_address = element.xpath(".//a[@class='gaq-link address-link']/div[1]/text()").extract_first()
        city_state_zip = element.xpath(".//a[@class='gaq-link address-link']/div[2]/text()").extract_first()
        city, state_zip = city_state_zip.split(",")
        state, zipcode = state_zip.strip().split(" ")
        country = re.search(r".+/(.+?)/(.+?)/(.+?)/(.+?)/?(?:\.html|$)", ref_url).group(1)
        phone = element.xpath(".//a[@class='phone']/text()").extract_first()
        map_link = element.xpath(".//a[@class='directions gaq-link']/@href").extract_first()

        # extract coordinates from map linkb
        if re.search(r".+=([0-9.-]+),\s?([0-9.-]+)", map_link):
            lat = re.search(r".+=([0-9.-]+),\s?([0-9.-]+)", map_link).group(1)
            lon = re.search(r".+=([0-9.-]+),\s?([0-9.-]+)", map_link).group(2)
        else:
            lat = None
            lon = None

        properties = {
            "ref": ref,
            "name": name,
            "street_address": street_address,
            "city": city,
            "state": state,
            "country": country,
            "postcode": zipcode,
            "lat": lat,
            "lon": lon,
            "phone": phone,
            "website": ref_url,
        }

        return properties
