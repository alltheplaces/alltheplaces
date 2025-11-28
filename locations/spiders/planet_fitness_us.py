import html

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class PlanetFitnessUSSpider(CrawlSpider, StructuredDataSpider, CamoufoxSpider):
    name = "planet_fitness_us"
    item_attributes = {"brand": "Planet Fitness", "brand_wikidata": "Q7201095"}
    allowed_domains = ["www.planetfitness.com"]
    start_urls = ["https://www.planetfitness.com/clubs"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/clubs/[a-z]{2}/?$", deny=r"/[a-z]{2}/clubs")
        ),  # Deny language-specific versions like /es/
        Rule(LinkExtractor(allow=r"/clubs/[a-z]{2}/[-\w]+?$", deny=r"/[a-z]{2}/clubs")),
        Rule(LinkExtractor(allow=r"/gyms/[-\w]+/?$", deny=r"/[a-z]{2}/gyms"), callback="parse_sd"),
    ]
    # Rate limiting is additionally applied. Using a single Camoufox context
    # slows the crawl, as does DOWNLOAD_DELAY. RETRY_TIMES is a further help.
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS | {
        "CAMOUFOX_MAX_PAGES_PER_CONTEXT": 1,
        "CAMOUFOX_MAX_CONTEXTS": 1,
        "DOWNLOAD_DELAY": 5,
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
        apply_category(Categories.GYM, item)
        yield item
