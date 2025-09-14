from locations.spiders.planet_fitness_us import PlanetFitnessUSSpider


class PlanetFitnessCASpider(PlanetFitnessUSSpider):
    name = "planet_fitness_ca"
    allowed_domains = ["www.planetfitness.ca"]
    start_urls = ["https://www.planetfitness.ca/clubs"]
