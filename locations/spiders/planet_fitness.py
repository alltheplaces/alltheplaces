import html

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


# Sitemap https://www.planetfitness.com/sitemap.xml isn't accessible for the spider.
class PlanetFitnessSpider(CrawlSpider, StructuredDataSpider):
    name = "planet_fitness"
    item_attributes = {"brand": "Planet Fitness", "brand_wikidata": "Q7201095"}
    start_urls = [
        "https://www.planetfitness.com/clubs",
        "https://www.planetfitness.ca/clubs",
    ]
    rules = [
        Rule(
            LinkExtractor(allow=r"/clubs/[a-z]{2}/?$", deny=r"/[a-z]{2}/clubs")
        ),  # Deny language-specific versions like /es/
        Rule(LinkExtractor(allow=r"/clubs/[a-z]{2}/[-\w]+?$", deny=r"/[a-z]{2}/clubs")),
        Rule(LinkExtractor(allow=r"/gyms/[-\w]+/?$", deny=r"/[a-z]{2}/gyms"), callback="parse_sd"),
    ]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "DOWNLOAD_DELAY": 3,
        "RETRY_TIMES": 5,
    }

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["opening_hours"] = OpeningHours()
        hours = response.xpath('//*[@id="club-hours"]')
        if "24/7" in hours.get(""):
            item["opening_hours"] = "24/7"
        else:
            for rule in hours.xpath(".//li/text() | .//p/text()").getall():
                rule = html.unescape(rule).replace("&", "-").replace("12:00 AM - 12:00 AM", "12:00 AM - 11:59 AM")
                item["opening_hours"].add_ranges_from_string(rule)
        yield item
