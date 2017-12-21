import scrapy
from locations.items import GeojsonPointItem
import re


class PlanetFitnessSpider(scrapy.Spider):
    name = "planet-fitness"
    allowed_domains = ["planetfitness.com"]
    start_urls = (
        "https://www.planetfitness.com/sitemap.xml",
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        for path in city_urls:
            if "https://www.planetfitness.com/gyms/" in path:
                yield scrapy.Request(
                    path,
                    callback=self.parse_gym
                )

    def parse_gym(self, response):
        coordinates = re.findall(r"(?<=\.setLngLat\(\[).*(?=\]\))", response.body_as_unicode())
        lat, lon = coordinates[0].split(", ") if len(coordinates) else [None, None]

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
            "ref": response.url
        }

        yield GeojsonPointItem(**point)
