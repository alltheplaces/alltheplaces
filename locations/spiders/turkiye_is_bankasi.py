from urllib.parse import urljoin
import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class TurkiyeIsBankasi(scrapy.Spider):
    name = "turkiye_is_bankasi"
    item_attributes = {"brand": "Türkiye İş Bankası", "brand_wikidata": "Q909613"}
    allowed_domains = ["www.isbank.com.tr"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    base_url = "https://www.isbank.com.tr/_layouts/15/DV.Isbank.Web/ATMBranchLocatorHandler.ashx"

    # def start_requests(self):
    #     yield JsonRequest(
    #         url="https://www.isbank.com.tr/_layouts/15/DV.Isbank.Web/ATMBranchLocatorHandler.ashx?MethodName=getAllDomesticCities&lang=tr",
    #         callback=self.parse,
    #     )
    #     yield JsonRequest(
    #         url="https://www.isbank.com.tr/_layouts/15/DV.Isbank.Web/ATMBranchLocatorHandler.ashx?MethodName=getAbroadCountries&lang=tr",
    #         callback=self.parse,
    #     )

    def start_requests(self):
        urls = [
            {"url": urljoin(self.base_url, "?MethodName=getAllDomesticCities&lang=tr"), "callback": self.parse_cities},
            {"url": urljoin(self.base_url, "?MethodName=getAbroadCountries&lang=tr"), "callback": self.parse_countries},
        ]

        for url in urls:
            yield scrapy.Request(url=url["url"], callback=url["callback"])

    def parse_cities(self, response):
        data = response.json()
        cities = data

        for city in cities:
            city_name = city["CityName"]
            form_data = {
                "CityName": city_name,
                "Province": "",
                "isBranch": "true",
                "BranchInput": "{}",
                "isATM": "true",
                "ATMInput": "{}",
            }

            yield scrapy.FormRequest(
                urljoin(self.base_url, "?MethodName=doSearchByCityProvince"),
                formdata=form_data,
                callback=self.parse_pois,
                meta={"city_name": city_name},
            )

    def parse_countries(self, response):
        data = response.json()
        countries = data

        for country in countries:
            country_code = country["CountryCode"]
            form_data = {
                "Country": country_code,
                "CityName": "",
                "isBranch": "true",
                "isATM": "true",
                "lang": "tr",
            }
            # TODO: get city for pois in countries other than Turkey
            #       from "?MethodName=getCityByCountry" endpoint

            yield scrapy.FormRequest(
                urljoin(self.base_url, "?MethodName=doSearchByCityCountry"),
                formdata=form_data,
                callback=self.parse_pois,
                meta={"country_code": country_code},
            )

    def parse_pois(self, response):
        pois = response.json()
        city_name = response.meta.get("city_name")
        country_code = response.meta.get("country_code")

        for poi in pois:
            item = DictParser.parse(poi)
            item["ref"] = poi.get("MarkerID")

            if city_name:
                item["city"] = city_name
            if country_code:
                item["country"] = country_code
            else:
                item["country"] = "TR"

            if poi.get("Type") == "A":
                apply_category(Categories.ATM, item)
            elif poi.get("Type") == "B":
                apply_category(Categories.BANK, item)
            # TODO: parse opening hours
            yield item
