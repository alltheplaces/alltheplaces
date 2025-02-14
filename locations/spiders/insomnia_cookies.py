from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours

COUNTRIES_QUERY = """query COUNTRIES($countryId: ID) {
  countries(countryId: $countryId) {
    all {
      api_url
      id
      iso3166_code
      url
    }
  }
}"""

STORES_QUERY = """{
  regularStores {
    address
    city
    countryId
    email
    id
    lat
    lng
    mailingAddress
    name
    phone
    slug
    state
    storefrontImage
    zip
    hours {
      type
      days {
        day
        hour
      }
    }
  }
}"""


class InsomniaCookiesSpider(Spider):
    name = "insomnia_cookies"
    item_attributes = {"brand": "Insomnia Cookies", "brand_wikidata": "Q16997024"}

    def start_requests(self):
        # First get a list of countries with their IDs, websites, and API
        # endpoints.
        yield JsonRequest(
            "https://api.insomniacookies.com/graphql",
            data={"query": COUNTRIES_QUERY},
            callback=self.parse_countries,
        )

    def parse_countries(self, response):
        countries = response.json()["data"]["countries"]["all"]
        for country in countries:
            yield JsonRequest(
                country["api_url"] + "/graphql",
                data={
                    "query": STORES_QUERY,
                },
                headers={
                    "selected-country": country["id"],
                },
                callback=self.parse_stores,
                cb_kwargs={"countries": countries},
            )

    def parse_stores(self, response, countries):
        for error in response.json().get("errors", []):
            self.logger.error(error["message"])
        for store in response.json()["data"]["regularStores"]:
            item = DictParser.parse(store)
            item["ref"] = f'{store["countryId"]}:{item["ref"]}'
            item["branch"] = item.pop("name")
            item["street_address"] = store["mailingAddress"]
            item["image"] = store["storefrontImage"]

            store_countries = [c for c in countries if c["id"] == store["countryId"]]
            if len(store_countries) == 0:
                self.logger.warn(f"Can't find country ID {store['countryId']!r}")
            else:
                country = store_countries[0]
                item["country"] = country["iso3166_code"]
                item["extras"]["website:menu"] = f"{country['url']}/menu/{store['slug']}"

            for hours in store["hours"]:
                oh = OpeningHours()
                for day in hours["days"]:
                    oh.add_ranges_from_string(f"{day['day']} {day['hour']}")
                if hours["type"] == "Retail Hours":
                    item["opening_hours"] = oh
                elif hours["type"] == "Delivery Hours":
                    item["extras"]["opening_hours:delivery"] = oh.as_opening_hours()

            yield item
