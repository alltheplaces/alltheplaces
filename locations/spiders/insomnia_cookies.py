from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.state_clean_up import STATES

COUNTRIES_QUERY = """query COUNTRIES($countryId: ID) {
  countries(countryId: $countryId) {
    all {
      id
      name
      url
      api_url
      iso3166_code
    }
  }
}"""

LOCATION_SEARCH_QUERY = """query locations($address: String!) {
  locationSearch(data: {address: $address}) {
    externalId
  }
}"""

STORE_SEARCH_QUERY = """query stores($externalId: String) {
  storeSearch(data: {externalId: $externalId}) {
    stores {
      id
      countryId
      name
      slug
      address
      mailingAddress
      city
      state
      zip
      phone
      storefrontImage
      lat
      lng
      hours {
        type
        days {
          day
          hour
        }
      }
    }
  }
}"""


class InsomniaCookiesSpider(Spider):
    name = "insomnia_cookies"
    item_attributes = {"brand": "Insomnia Cookies", "brand_wikidata": "Q16997024"}

    # Too many requests in too short a time puts your IP into a long (>4hr)
    # timeout. A 15 second delay between requests seems to work.
    custom_settings = {"DOWNLOAD_DELAY": 15}

    def start_requests(self):
        # First get a list of countries with their names, websites, and API
        # endpoints.
        yield JsonRequest(
            "https://api.insomniacookies.com/graphql",
            data={"query": COUNTRIES_QUERY},
            callback=self.parse_countries,
        )

    def parse_countries(self, response):
        # The store search query searches for stores within a location, using an
        # "externalId" (from Google), so we need to get some of those. Too large
        # areas, like entire countries, return 0 results, so we need the largest
        # subdivision that does return results. In my testing, provinces/states
        # work for CA and US, but countries don't work for UK.
        countries = response.json()["data"]["countries"]["all"]
        for country in countries:
            if country["iso3166_code"] in STATES:
                subdivisions = STATES[country["iso3166_code"]].values()
            else:
                # Too many requests also trigger the timeout, so only query the
                # most populous cities. Of the 34 largest cities in UK, the
                # smallest with any locations is Nottingham, population 323632.
                subdivisions = city_locations(country["iso3166_code"], 323632)
            for subdivision in subdivisions:
                yield JsonRequest(
                    country["api_url"] + "/graphql",
                    data={
                        "variables": {"address": f"{subdivision['name']}, {country['name']}"},
                        "query": LOCATION_SEARCH_QUERY,
                    },
                    headers={
                        "selected-country": country["id"],
                    },
                    callback=self.parse_location,
                    cb_kwargs={"countries": countries},
                )

    def parse_location(self, response, countries):
        # Choose the first search result.
        external_id = response.json()["data"]["locationSearch"][0]["externalId"]
        yield JsonRequest(
            response.url,
            data={
                "variables": {"externalId": external_id},
                "query": STORE_SEARCH_QUERY,
            },
            headers={
                "selected-country": response.request.headers["selected-country"],
            },
            callback=self.parse_stores,
            cb_kwargs={"countries": countries},
        )

    def parse_stores(self, response, countries):
        for store in response.json()["data"]["storeSearch"]["stores"]:
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
