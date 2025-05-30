from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


# Sitemap https://www.planetfitness.com/sitemap.xml isn't accessible for the spider.
class PlanetFitnessSpider(CrawlSpider, StructuredDataSpider):
    name = "planet_fitness"
    item_attributes = {"brand": "Planet Fitness", "brand_wikidata": "Q7201095"}
    start_urls = ["https://www.planetfitness.com/clubs"]
    rules = [
        Rule(LinkExtractor(allow=r"/clubs/[a-z]{2}/?$")),
        Rule(LinkExtractor(allow="/gyms/[-\w]+/?$"), callback="parse_sd"),
    ]
    requires_proxy = True
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "DOWNLOAD_DELAY": 3,
        "RETRY_TIMES": 5,
    }
