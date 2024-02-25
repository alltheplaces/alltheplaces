import functools

import pycountry
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class FordSpider(scrapy.Spider):
    name = "ford"
    available_countries = [
        "PER",
        "ATG",
        "JAM",
        "LBN",
        "NIC",
        "FRA",
        "IRL",
        "CAN",
        "HTI",
        "AGO",
        "KEN",
        "DMA",
        "ZAF",
        "ITA",
        "FJI",
        "MNG",
        "BRA",
        "GUM",
        "DNK",
        "THA",
        "PYF",
        "BHR",
        "MYS",
        "VEN",
        "COG",
        "SXM",
        "SAU",
        "YEM",
        "SYC",
        "TTO",
        "ASM",
        "MWI",
        "MOZ",
        "COL",
        "AFG",
        "BMU",
        "SEN",
        "QAT",
        "BEN",
        "NPL",
        "ARE",
        "MUS",
        "MNP",
        "SWE",
        "HUN",
        "ESP",
        "UGA",
        "DOM",
        "TLS",
        "CUW",
        "NGA",
        "NZL",
        "ZMB",
        "BRB",
        "GAB",
        "KOR",
        "PRI",
        "NAM",
        "AUT",
        "DEU",
        "LUX",
        "LKA",
        "BOL",
        "PAN",
        "NLD",
        "CHE",
        "IND",
        "SGP",
        "ETH",
        "POL",
        "BRN",
        "CIV",
        "FIN",
        "KHM",
        "GBR",
        "VNM",
        "RUS",
        "LBR",
        "GHA",
        "BEL",
        "SLV",
        "LCA",
        "MDG",
        "NCL",
        "JPN",
        "CZE",
        "JOR",
        "BLZ",
        "WSM",
        "GRD",
        "PRT",
        "KWT",
        "ABW",
        "ARG",
        "PHL",
        "MAF",
        "ZWE",
        "VIR",
        "CHL",
        "CPV",
        "NOR",
        "BHS",
        "MMR",
        "USA",
        "BFA",
        "BGD",
        "GTM",
        "IRQ",
        "BWA",
        "LAO",
        "OMN",
        "HKG",
        "TZA",
        "SUR",
        "VUT",
        "CYM",
        "MEX",
        "SLE",
        "HND",
        "CMR",
        "GRC",
        "AUS",
        "PNG",
        "ROU",
    ]

    brand_mapping = {
        "Ford": {"brand": "Ford", "brand_wikidata": "Q44294"},
        "Lincoln": {"brand": "Lincoln", "brand_wikidata": "Q216796"},
        "Fuso": {"brand": "Fuso", "brand_wikidata": "Q1190247"},
        "Setra": {"brand": "Setra", "brand_wikidata": "Q938615"},
        "Motorcraft": {"brand": "Ford", "brand_wikidata": "Q44294"},
    }
    custom_settings = {"DEFAULT_REQUEST_HEADERS": {"x-apikey": "45ab9277-3014-4c9e-b059-6c0542ad9484"}}

    def start_requests(self):
        for country in self.available_countries:
            url = f"https://spatial.virtualearth.net/REST/v1/data/1652026ff3b247cd9d1f4cc12b9a080b/FordEuropeDealers_Transition/Dealer?$filter=CountryCode%20Eq%20%27{country}%27&$top=100000&$format=json&key=Al1EdZ_aW5T6XNlr-BJxCw1l4KaA0tmXFI_eTl1RITyYptWUS0qit_MprtcG7w2F&$skip=0"
            yield scrapy.Request(url=url, callback=self.parse_stores)

    def parse_stores(self, response):
        results = response.json().get("d").get("results")

        for data in results:
            oh = OpeningHours()

            for day in DAYS_FULL:
                if opening_time := data.get(f"Sales{day}OpenTime"):
                    closing_time = data.get(f"Sales{day}CloseTime")
                    if not self.is_opening_hour_valid(opening_time) or not self.is_opening_hour_valid(closing_time):
                        continue
                    opening_time = opening_time.replace("pm", "00").replace("am", "00").replace(":", "")
                    closing_time = closing_time.replace("pm", "00").replace("am", "00").replace(":", "")
                    if int(opening_time) > 2400 or int(closing_time) > 2400:
                        continue
                    oh.add_range(day=day, open_time=opening_time, close_time=closing_time, time_format="%H%M")

            item = DictParser.parse(data)
            item["ref"] = data.get("EntityID")
            item["phone"] = data.get("PrimaryPhone")
            item["name"] = data.get("DealerName")
            item["country"] = self.get_country_code(data.get("CountryCode"))
            item["opening_hours"] = oh
            item["website"] = data["PrimaryURL"]
            item["brand"] = self.brand_mapping.get(data.get("Brand")).get("brand")
            item["brand_wikidata"] = self.brand_mapping.get(data.get("Brand")).get("brand_wikidata")

            if data["HasSalesDepartmentPV"] or data["HasSalesDepartmentCV"]:
                apply_category(Categories.SHOP_CAR, item)
            elif data["HasServiceDepartmentPV"] or data["HasServiceDepartmentCV"]:
                apply_category(Categories.SHOP_CAR_REPAIR, item)
            elif data["HasPartsDepartment"]:
                apply_category(Categories.SHOP_CAR_PARTS, item)
            else:
                apply_category(Categories.SHOP_CAR, item)
            yield item

        if len(results) == 250:
            base_url, skip_value = response.url.split("skip=")
            yield scrapy.Request(url=f"{base_url}skip={int(skip_value) + 250}", callback=self.parse_stores)

    def is_ascii(self, str):
        return all(ord(c) < 128 for c in str)

    @functools.lru_cache()
    def get_country_code(self, alpha_3):
        return pycountry.countries.get(alpha_3=alpha_3).alpha_2

    def is_opening_hour_valid(self, opening_hour):
        if len(opening_hour) > 6:
            return False
        invalid_values = {"", "-", "0", "closed"}
        return opening_hour.lower() not in invalid_values and "." not in opening_hour and self.is_ascii(opening_hour)
