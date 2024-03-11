from scrapy.spiders import SitemapSpider

from locations.linked_data_parser import LinkedDataParser


class PlanetFitnessSpider(SitemapSpider):
    name = "planet_fitness"
    item_attributes = {"brand": "Planet Fitness", "brand_wikidata": "Q7201095"}
    download_delay = 4
    sitemap_urls = [
        "https://www.planetfitness.com/sitemap.xml",
    ]
    sitemap_rules = [
        (r"https://www.planetfitness.com/gyms/", "parse"),
    ]
    requires_proxy = True

    def parse(self, response):
        item = LinkedDataParser.parse(response, "ExerciseGym")
        yield item
