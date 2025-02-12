import scrapy
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class Century21Spider(scrapy.Spider):
    name = "century_21"
    item_attributes = {"brand": "Century 21", "brand_wikidata": "Q1054480"}
    start_urls = ["https://www.century21global.com/en/countries"]
    total_results = {}

    def parse(self, response):
        # Taking text rather than slug from url because at the moment at least
        # "Cyprus Northern Territory" points to the wrong url and returns different results
        for country in response.xpath('//a[contains(@href, "/en/countries/")]/div/span/text()').getall():
            self.logger.debug(f"Starting requests for {country.strip()}")
            yield self.make_request(country.strip(), 0, True)

    # API appears to return a maximum of 10000 results (or not accept an offset greater than 10000)
    # There is no obvious way to get extra results for any country except by searching both ascending and descending
    def make_request(self, country: str, offset: int, ascending: bool):
        if ascending:
            order = "ASC"
        else:
            order = "DESC"

            # Stop fetching to minimise duplicate results
            if offset > self.total_results[country] - 10000:
                return

        return JsonRequest(
            url="https://www.century21global.com/api/aggregator-service/aggregator/office",
            headers={"Content-Type": "application/json"},
            data={
                "country": country,
                "offset": offset,
                "max": 50,
                "includeListings": False,
                "language": "EN",
                "sortBy": "NAME",
                "sortOrder": order,
            },
            cb_kwargs={"country": country, "offset": offset, "ascending": ascending},
            callback=self.parse_listings,
        )

    def parse_listings(self, response, **kwargs):
        if self.total_results.get(kwargs["country"]) is None and (num_results := response.json()["total"]):
            self.logger.info(f"{num_results} locations for {kwargs['country']}")

            self.total_results[kwargs["country"]] = num_results
            if num_results > 20000:
                self.logger.warning(f"More than 20000 results for {kwargs['country']}, some locations will be missed")
            if num_results > 10000:
                yield self.make_request(kwargs["country"], 0, False)

        if response.json()["result"]:
            for location in response.json()["result"]:
                item = DictParser.parse(location)

                item["street_address"] = item.pop("street")

                # Without 'description' they are in lower case
                item["city"] = location["address"].get("cityDescription")
                item["state"] = location["address"].get("stateDescription")

                item["country"] = kwargs["country"]

                item["website"] = "https://www.century21global.com/offices/" + item["ref"]

                yield item

            current_offeset = kwargs["offset"] + 50
            yield self.make_request(kwargs["country"], current_offeset, kwargs["ascending"])
