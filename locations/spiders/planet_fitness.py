import scrapy
from locations.items import GeojsonPointItem
import json
from scrapy.http import XmlResponse, HtmlResponse
import re


class PlanetFitnessSpider(scrapy.Spider):
    name = "planet-fitness"
    allowed_domains = ["planetfitness.com"]

    def start_requests(self):
        sitemap_url = "https://www.planetfitness.com/sitemap.xml"
        yield scrapy.Request(url=sitemap_url, headers={"accept": "text/xml"})

    def parse(self, response):
        # wrong content-type from server, hacky solution by specifying HtmlResponse
        new_response = HtmlResponse(url=response.url, body=response.body)
        urls = [url for url in new_response.css("loc::text").extract() if "https://www.planetfitness.com/gyms/" in url]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_gym)

    def parse_gym(self, response):
        coordinates = re.findall(r"(?<=\.setLngLat\(\[).*(?=\]\))", response.body_as_unicode())
        lat, lon = coordinates[0].split(", ") if len(coordinates) else None, None
        iframe = response.css("iframe[src*='https://mico.myiclubonline.com']::attr('src')")
        club_number = iframe.extract_first().split("=")[-1]
        point = {
            "lat": lat,
            "lon": lon,
            "name": "Planet Fitness " + response.css("h1.alt::text").extract_first(default="").strip(),
            "addr_full": response.css(".address-line1::text").extract_first(),
            "city": response.css(".locality::text").extract_first(),
            "state": response.css(".administrative-area::text").extract_first(),
            "postcode": response.css(".postal-code::text").extract_first(),
            "country": response.css(".country::text").extract_first(),
            "phone": response.css(".field--name-field-phone div::text").extract_first(default="").strip(),
            "website": response.url,
            "opening_hours": "24/7",
            "ref": club_number
        }

        yield GeojsonPointItem(**point)
