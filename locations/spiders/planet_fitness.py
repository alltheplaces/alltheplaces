import scrapy
from locations.items import GeojsonPointItem


class PlanetFitnessSpider(scrapy.Spider):
    name = "planet-fitness"
    item_attributes = { 'brand': "Planet Fitness" }
    allowed_domains = ["planetfitness.com"]
    start_urls = (
        "https://www.planetfitness.com/sitemap",
    )

    def parse(self, response):
        city_urls = response.xpath('//td[@class="club-title"]/a/@href').extract()
        for path in city_urls:
            if "/gyms/" in path:
                yield scrapy.Request(
                    response.urljoin(path),
                    callback=self.parse_gym
                )

    def parse_gym(self, response):
        coordinates = response.xpath('//meta[@name="geo.position"]/@content').extract_first()
        lat, lon = coordinates.split(", ") if len(coordinates) else [None, None]

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
