from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Request

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT

GQL_QUERY = """query storesMapResults {
    storesSearch(start: 0, limit: 5000) {
        result {
            id
            storeType
            phone
            address { city countryCode houseNumber houseNumberExtra postalCode street }
            openingDays { date dayName openingHour { openFrom openUntil } type }
            geoLocation { latitude longitude }
        }
    }
}"""


class AlbertHeijnNLSpider(PlaywrightSpider):
    name = "albert_heijn_nl"
    allowed_domains = ["www.ah.nl"]
    start_urls = ["https://www.ah.nl/winkels"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {
        "USER_AGENT": BROWSER_DEFAULT,
        "PLAYWRIGHT_ABORT_REQUEST": lambda request: request.resource_type not in ["document", "fetch", "xhr"],
    }

    brand_map = {
        "REGULAR": {"brand": "Albert Heijn", "brand_wikidata": "Q1653985"},
        "TOGO": {"brand": "Albert Heijn to go", "brand_wikidata": "Q77971185"},
        "XL": {"brand": "Albert Heijn XL", "brand_wikidata": "Q78163765"},
    }

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url=self.start_urls[0],
            callback=self.parse,
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse(self, response, **kwargs: Any) -> Any:
        page = response.meta["playwright_page"]
        try:
            data = await page.evaluate(
                """async (query) => {
                    const response = await fetch('/gql', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query: query})
                    });
                    return await response.json();
                }""",
                GQL_QUERY,
            )
        finally:
            await page.close()

        for location in data["data"]["storesSearch"]["result"]:
            item = DictParser.parse(location)
            self.parse_hours(item, location)
            item.update(self.brand_map.get(location["storeType"]))

            slug = "/winkel/{}".format(item["ref"])
            item["website"] = response.urljoin(slug)
            item["extras"]["website:be"] = urljoin("https://www.ah.be/", slug)
            item["extras"]["website:nl"] = urljoin("https://www.ah.nl/", slug)

            yield item

    def parse_hours(self, item, store):
        if days_hours := store.get("openingDays"):
            oh = OpeningHours()
            for day_hours in days_hours[0]:
                if opening_hours := day_hours.get("openingHour"):
                    day = DAYS_NL[str(day_hours.get("dayName")).capitalize()]
                    oh.add_range(day, opening_hours.get("openFrom"), opening_hours.get("openUntil"))
            item["opening_hours"] = oh.as_opening_hours()
