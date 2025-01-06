from html import unescape
from json import loads
from typing import Iterable

from scrapy import Spider
from scrapy.http import FormRequest, Response, Request

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class CottonOnGroupSpider(Spider):
    name = "cotton_on_group"
    allowed_domains = ["cottonon.com"]
    start_urls = ["https://cottonon.com/on/demandware.store/Sites-cog-au-Site/en_AU/Stores-FindStores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    brands = {
        "Cotton On": {"brand": "Cotton On", "brand_wikidata": "Q5175717", "category": Categories.SHOP_CLOTHES},
        "Cotton On Body": {"brand": "Cotton On Body", "brand_wikidata": None, "category": Categories.SHOP_CLOTHES},
        "Cotton On Kids": {"brand": "Cotton On Kids", "brand_wikidata": "Q113961498", "category": Categories.SHOP_CLOTHES},
        "Factorie": {"brand": "Factorie", "brand_wikidata": None, "category": Categories.SHOP_CLOTHES},
        "Rubi Shoes": {"brand": "Rubi", "brand_wikidata": None, "category": Categories.SHOP_SHOES},
        "Supre": {"brand": "Supré", "brand_wikidata": "Q7645153", "category": Categories.SHOP_CLOTHES},
        "TYPO": {"brand": "Typo", "brand_wikidata": None, "category": Categories.SHOP_STATIONERY},
    }
    countries = {
        "AE": ("23.424076", "53.847818"),
        "AU": ("-25.274398", "133.775136"),
        "BR": ("-14.235004", "-51.92528"),
        "GB": ("55.378051", "-3.435973"),
        "HK": ("22.3193039", "114.1693611"),
        "ID": ("-0.789275", "113.921327"),
        "LB": ("33.854721", "35.862285"),
        "MY": ("4.210484", "101.975766"),
        "NA": ("-22.95764", "18.49041"),
        "NZ": ("-40.900557", "174.885971"),
        "OM": ("21.4735329", "55.975413"),
        "PH": ("12.879721", "121.774017"),
        "QA": ("25.354826", "51.183884"),
        "SA": ("23.885942", "45.079162"),
        "SG": ("1.352083", "103.819836"),
        "TH": ("15.870032", "100.992541"),
        "US": ("38.7945952", "-106.5348379"),
        "VN": ("14.058324", "108.277199"),
        "ZA": ("-30.559482", "22.937506"),
    }

    def start_requests(self) -> Iterable[Request]:
        yield Request(url="https://cottonon.com/AU/store-finder/", callback=self.parse_csrf_token)

    def parse_csrf_token(self, response: Response) -> Iterable[FormRequest]:
        csrf_token = response.xpath('//input[@name="csrf_token"]/@value').get()
        headers = {
            "X-Requested-With": "XMLHttpRequest",
        }

        for country_code, coordinates in self.countries.items():
            formdata = {
                "dwfrm_storelocator_brandsInStore": "CottonOn,CottonOnBody,CottonOnKids,RubiShoes,Typo,Factorie,Supre",
                "dwfrm_storelocator_country": country_code,
                "dwfrm_storelocator_textfield": "",
                "csrf_token": csrf_token,
                "format": "ajax",
                "lat": coordinates[0],
                "lng": coordinates[1],
                "dwfrm_storelocator_findByLocation": "x",
            }
            yield FormRequest(url=self.start_urls[0], formdata=formdata, headers=headers, method="POST")

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.xpath('//div[contains(@class, "store-details")]'):
            data = loads(unescape(location.xpath('./@data-store').get()))
            item = DictParser.parse(data)

            primary_brand = location.xpath('.//div[@class="store-brand"]/text()').get().strip()
            if primary_brand not in self.brands.keys():
                self.logger.error("Unknown brand: {}".format(primary_brand))
                return
            item["brand"] = self.brands[primary_brand]["brand"]
            item["brand_wikidata"] = self.brands[primary_brand]["brand_wikidata"]
            apply_category(self.brands[primary_brand]["category"], item)

            if data.get("storeDetailsURL"):
                item["website"] = data["storeDetailsURL"].split("&Distance=", 1)[0]
            item["phone"] = location.xpath('.//div[@class="store-phone"]/a[contains(@href, "tel:")]/@href').get()
            if item["phone"]:
                item["phone"] = item["phone"].removeprefix("tel:")

            item["opening_hours"] = OpeningHours()
            hours_string = " ".join(location.xpath('.//div[contains(@class, "store-hours")]//text()').getall()).replace(" (Today)", "")
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
