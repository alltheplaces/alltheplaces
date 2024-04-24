import scrapy
import xmltodict

from locations.categories import Categories, apply_category
from locations.items import Feature, SocialMedia, set_social_media


class SamsoniteEuSpider(scrapy.Spider):
    name = "samsonite_eu"
    CHIC_ACCENT = {"brand": "Chic Accent"}
    SAMSONITE = {"brand": "Samsonite", "brand_wikidata": "Q1203426"}
    allowed_domains = ["samsonite.com"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 30}

    def start_requests(self):
        country_eu = [
            "AL",
            "CZ",
            "DE",
            "DK",
            "CY",
            "AT",
            "BE",
            "BG",
            "CH",
            "EE",
            "EL",
            "ES",
            "FI",
            "FR",
            "HR",
            "HU",
            "IE",
            "IS",
            "IT",
            "LT",
            "LU",
            "NL",
            "NO",
            "LV",
            "ME",
            "MT",
            "MK",
            "LI",
            "PL",
            "SI",
            "SK",
            "TR",
            "UK",
            "RS",
            "SE",
            "PT",
            "RO",
            "GB",
        ]
        template = "https://storelocator.samsonite.eu/data-exchange/getDealerLocatorMapV2_Radius.aspx?s=sams&country={}&search=dealer&lat=48.85799300000001&lng=2.381153&radius=100000"
        for country in country_eu:
            yield scrapy.Request(url=template.format(country), callback=self.parse)

    def parse(self, response):
        data = xmltodict.parse(response.text)
        if data.get("dealers"):
            stores = data.get("dealers", {}).get("dealer")
            stores = stores if isinstance(stores, list) else [stores]
            for store in stores:
                if store["fld_Deal_DeCl_ID"] != "9":
                    continue
                item = Feature()
                item["lat"] = store["Latitude"]
                item["lon"] = store["Longitude"]
                item["ref"] = store.get("fld_Deal_Id")
                item["street_address"] = store.get("fld_Deal_Address1")
                item["city"] = store.get("fld_Deal_City1")
                item["postcode"] = store.get("fld_Deal_Zip")
                item["country"] = store.get("fld_Coun_Name")
                item["email"] = store.get("fld_Deal_Email") or ""
                item["website"] = store["fld_Deal_DetailPageUrl"]

                if "chicaccent.com" in item["email"]:
                    item.update(self.CHIC_ACCENT)
                else:
                    item.update(self.SAMSONITE)

                if phone := store.get("fld_Deal_Phone"):
                    phone = store["fld_Deal_Prefix"] + phone.lower()

                    if "whatsapp" in phone:
                        phone, whats_app = phone.split("whatsapp")
                        set_social_media(item, SocialMedia.WHATSAPP, whats_app.strip(" :"))

                    item["phone"] = phone
                apply_category(Categories.SHOP_BAG, item)
                yield item
