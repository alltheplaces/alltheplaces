from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class CbreSpider(Spider):
    name = "cbre"
    item_attributes = {"brand": "CBRE", "brand_wikidata": "Q1023013"}
    start_urls = ["https://www.cbre.com/offices"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
    country_map = {
        "Korea": "KR",
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for country_selector in response.xpath('//a[contains(@class, "countrySelector")]'):
            country = country_selector.xpath(".//span/text()").get("").strip()
            country_url = country_selector.xpath("./@href").get("").replace("people-and-offices", "offices")
            yield response.follow(url=country_url, callback=self.parse_cities, cb_kwargs=dict(country=country))

    def parse_cities(self, response: Response, country: str) -> Any:
        cities = response.xpath(
            '//a[contains(@href, "offices") and not(contains(@class, "countrySelector"))]/@href'
        ).getall()
        if cities:
            for city_url in cities:
                yield response.follow(url=city_url, callback=self.parse_locations, cb_kwargs=dict(country=country))
        else:
            yield from self.parse_locations(response, country)

    def parse_locations(self, response: Response, country: str) -> Any:
        country = self.country_map.get(country, country)
        primary_location = response.xpath('//*[contains(@class,"contactCardWrapper")]')
        locations = response.xpath(
            '//*[contains(@class,"listCards--office")]'
        )  # multiple locations including primary one
        if locations:
            for location in locations:
                item = Feature()
                # Few duplicate locations from different urls are there, that's why we should make addr_full as ref.
                item["ref"] = item["addr_full"] = clean_address(
                    location.xpath('.//p[contains(@class, "officeAddress")]//text()').getall()
                )
                item["country"] = country
                item["website"] = response.url
                item["phone"] = location.xpath('.//a[contains(@href,"tel:")]/@href').get("")
                item["extras"]["fax"] = (
                    location.xpath('.//a[contains(@href,"fax:")]/@href').get("").replace("fax:", "").strip()
                )
                extract_google_position(item, location)
                yield item
        elif primary_location:  # only one location is present
            item = Feature()
            item["ref"] = item["addr_full"] = clean_address(
                primary_location.xpath('.//p[contains(@class, "personDesignation")]//text()').getall()
            )
            item["country"] = country
            item["website"] = response.url
            item["phone"] = primary_location.xpath('.//a[contains(@href,"tel:")]/@href').get("")
            item["extras"]["fax"] = (
                primary_location.xpath('.//a[contains(@href,"fax:")]/@href').get("").replace("fax:", "").strip()
            )
            extract_google_position(item, primary_location)
            yield item
        else:
            self.logger.warning(f"Failed to collect location info from url: {response.url}")
