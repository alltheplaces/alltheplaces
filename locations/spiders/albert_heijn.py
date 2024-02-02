import json
from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_NL, OpeningHours
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class AlbertHeijnSpider(Spider):
    name = "albert_heijn"
    allowed_domains = ["www.ah.nl", "www.ah.be"]
    start_urls = ["https://www.ah.nl/winkels", "https://www.ah.be/winkels"]
    user_agent = BROWSER_DEFAULT
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    brand_map = {
        "REGULAR": {"brand": "Albert Heijn", "brand_wikidata": "Q1653985"},
        "TOGO": {"brand": "Albert Heijn to go", "brand_wikidata": "Q77971185"},
        "XL": {"brand": "Albert Heijn XL", "brand_wikidata": "Q78163765"},
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Collect cookies
        yield JsonRequest(
            response.urljoin("/gql"),
            data={
                "query": """query storesMapResults {
                  storesSearch(start: 0, limit: 5000) {
                    result {
                      id
                      storeType
                      phone
                      address {
                        city
                        countryCode
                        houseNumber
                        houseNumberExtra
                        postalCode
                        street
                      }
                      openingDays {
                        date
                        dayName
                        openingHour {
                          openFrom
                          openUntil
                        }
                        type
                      }
                      geoLocation {
                        latitude
                        longitude
                      }
                      storeType
                    }
                  }
                }
                """
            },
            callback=self.parse_api,
        )

    def parse_api(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(response.xpath("/html/body/pre/text()").get())["data"]["storesSearch"]["result"]:
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
            for day_hours in days_hours[0]:  # For some reason it has a 2D list [[{Mo},{Tu},...]]
                if openingHours := day_hours.get("openingHour"):
                    day = DAYS_NL[str(day_hours.get("dayName")).capitalize()]
                    open = openingHours.get("openFrom")
                    close = openingHours.get("openUntil")
                    oh.add_range(day, open, close)
            item["opening_hours"] = oh.as_opening_hours()
