import re
from typing import Any, Iterable

from geonamescache import GeonamesCache
from scrapy import Request
from scrapy.http import Response

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


# Sitemap https://www.planetfitness.com/sitemap.xml isn't accessible for the spider.
class PlanetFitnessSpider(StructuredDataSpider):
    name = "planet_fitness"
    item_attributes = {"brand": "Planet Fitness", "brand_wikidata": "Q7201095"}
    requires_proxy = True
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "ROBOTSTXT_OBEY": False,
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000,
        "DOWNLOAD_DELAY": 3,
        "RETRY_TIMES": 5,
    }

    def start_requests(self) -> Iterable[Request]:
        for state in GeonamesCache().get_us_states_by_names():
            yield Request(f'https://www.planetfitness.com/gyms.data?limit=1000&q={state.lower().replace(" ", "-")}')

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for slug in set(re.findall(r"planetfitness\.com/gyms/([-\w]+)/offers", response.text)):
            yield Request(url=f"https://www.planetfitness.com/gyms/{slug}", callback=self.parse_sd)
