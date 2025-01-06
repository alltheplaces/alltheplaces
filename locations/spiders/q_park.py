import json
import re
from typing import Iterable

from scrapy import Request, Spider

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT

COUNTRIES = {
    "be": {"lang": "nl-be", "poi": "bezienswaardigheden", "uri_path": "parkeren", "deals": "goedkoop-parkeren-in-"},
    "de": {"lang": "en-gb", "poi": "poi", "uri_path": "cities", "deals": "gunstig-parken-in-"},
    "dk": {"lang": "en-gb", "poi": "poi", "uri_path": "parking", "deals": "deals-on-parking-in-"},
    "fr": {"lang": "en-gb", "poi": "poi", "uri_path": "cities", "deals": "deals"},
    "ie": {"lang": "en-gb", "poi": "poi", "uri_path": "cities", "deals": "dublin-city-offers"},
    "nl": {"lang": "en-gb", "poi": "poi", "uri_path": "parking", "deals": "cheap-parking-"},
    "co.uk": {"lang": "en-gb", "poi": "poi", "uri_path": "cities", "deals": "deals"},
}


class QParkSpider(Spider):
    name = "q_park"
    item_attributes = {"brand": "Q-Park", "brand_wikidata": "Q1127798"}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def start_requests(self) -> Iterable[Request]:
        for country, info in COUNTRIES.items():
            yield Request(
                url=f"https://www.q-park.{country}/{info['lang']}/{info['uri_path']}/",
                cb_kwargs={"country_info": info},
                callback=self.parse_country,
            )

    def parse_country(self, response, country_info):
        cities = response.xpath(
            f"""//a[@class='no-link'][contains(@href, '/{country_info["lang"]}/{country_info["uri_path"]}/')]/@href"""
        ).getall()
        for city in cities:
            yield Request(
                url=response.urljoin(city),
                cb_kwargs={"city": city, "country_info": country_info},
                callback=self.parse_city,
            )

    def parse_city(self, response, city, country_info):
        hrefs = response.xpath("//a[@class='no-link']/@href").getall()
        hrefs = set(hrefs)

        for href in hrefs:
            if f"/{country_info['poi']}/" not in href and f"{country_info['deals']}" not in href:
                yield Request(
                    url=response.urljoin(href),
                    callback=self.parse_facility,
                )

    def parse_facility(self, response):
        ld_jsons = response.xpath("//script[@type='application/ld+json']/text()").getall()
        for ld_json in ld_jsons:
            facility_info = json.loads(ld_json)
            if facility_info.get("@type") == "ParkingFacility":
                continue
        item = DictParser.parse(facility_info)
        item["phone"] = facility_info.get("address", {}).get("telephone")
        item["website"] = response.url
        item["ref"] = response.url.split("/")[-2]

        try:
            google_urls = response.xpath("//a[contains(@href, 'google.com/maps')]/@href").getall()
            for url in google_urls:
                if "destination=" in url and "destination_place_id=" not in url:
                    item["lat"] = url.split("destination=")[1].split(",")[0]
                    item["lon"] = url.split("destination=")[1].split(",")[1]

            if not item.get("lat") and not item.get("lon"):
                google_api_urls = response.xpath(
                    "//div[@class='img-bg'][contains(@data-background-image, 'googleapis')]/@data-background-image"
                ).getall()
                for url in google_api_urls:
                    if "map-marker-blue.png" in url:
                        item["lat"] = url.split("map-marker-blue.png")[1].split(",")[0]
                        item["lon"] = url.split("map-marker-blue.png")[1].split(",")[1]
                        if "%7C" in item["lat"]:
                            item["lat"] = item["lat"].split("%7C")[1]
                        if "&signature=" in item["lon"]:
                            item["lon"] = item["lon"].split("&signature=")[0]
                        self.crawler.stats.inc_value("zzz/googleapi")
        except Exception:
            self.crawler.stats.inc_value("q_park/failed_to_get_lat_lon")

        match = re.search(r"const customGtmEventsToPush = (\[.*?\]);", response.text, re.DOTALL)
        try:
            match_json = json.loads(match.group(1).strip())
            for element in match_json:
                if "productDetail" in element:
                    item["extras"]["capacity"] = element["productDetail"].get("totalSpots")
                    item["extras"]["capacity:disabled"] = element["productDetail"].get("disabledSpots")
                    item["extras"]["capacity:charging"] = element["productDetail"].get("chargingPoints", "no")
                    item["extras"]["maxheight"] = element["productDetail"].get("entryHeight")
                    if item["extras"]["maxheight"]:
                        item["extras"]["maxheight"] = item["extras"]["maxheight"] + " meters"
        except Exception:
            self.crawler.stats.inc_value("q_park/failed_to_get_capacity")

        yield item
