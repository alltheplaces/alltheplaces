import re
from datetime import date
from typing import Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature


class PlusNLSpider(Spider):
    """
    PLUS's store finder is an OutSystems React SPA with no server-rendered
    data. Store data comes from two internal "screenservices" JSON RPC
    endpoints, both of which require an "apiVersion" hash that changes on
    every deploy. Rather than hardcode a hash that will go stale, we harvest
    the current hashes at the start of each crawl from the compiled JS
    bundles that call these endpoints (the hash is a literal string sitting
    right next to the endpoint path there), following the same manifest
    lookup the site's own JS runtime uses.
    """

    name = "plus_nl"
    item_attributes = {"brand": "PLUS", "brand_wikidata": "Q1978981"}
    allowed_domains = ["www.plus.nl"]
    start_urls = ["https://www.plus.nl/moduleservices/moduleversioninfo"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    # OutSystems issues this fixed CSRF token to anonymous (non-logged-in) sessions.
    CSRF_TOKEN = "T6C+9iB49TLra4jEsMeSckDMNhQ="

    EXTENDED_DATA_ACTION = "CMS_Monolith/ActionStore_GetExtendedDataObj_Cache"
    OPENING_HOURS_ACTION = "CMS_Monolith/CMS_Store_RCW/MainFlow_Store/DataActionGetOpenningHours"
    EXTENDED_DATA_SCRIPT = "/ECOP/scripts/CMS_Monolith.controller.js"
    OPENING_HOURS_SCRIPT = "/ECOP/scripts/CMS_Monolith.CMS_Store_RCW.MainFlow_Store.mvc.js"

    def api_headers(self) -> dict:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=UTF-8",
            "OutSystems-Locale": "nl-NL",
            "X-CSRFToken": self.CSRF_TOKEN,
        }

    def parse(self, response: Response) -> Iterable[Response]:
        module_version = response.json()["versionToken"]
        yield response.follow(
            f"/moduleservices/moduleinfo?{module_version}",
            meta={"module_version": module_version},
            callback=self.parse_manifest,
        )

    def parse_manifest(self, response: Response) -> Iterable[Response]:
        self.module_version = response.meta["module_version"]
        self.url_versions = response.json()["manifest"]["urlVersions"]
        yield self.request_script(self.EXTENDED_DATA_SCRIPT, self.parse_extended_data_script)

    def request_script(self, script_path: str, callback) -> Request:
        script_version = self.url_versions[script_path].lstrip("?")
        return Request(f"https://www.plus.nl{script_path}?{script_version}", callback=callback)

    def parse_extended_data_script(self, response: Response) -> Iterable[Response]:
        self.extended_data_api_version = self.extract_api_version(response.text, self.EXTENDED_DATA_ACTION)
        yield self.request_script(self.OPENING_HOURS_SCRIPT, self.parse_opening_hours_script)

    def parse_opening_hours_script(self, response: Response) -> Iterable[Response]:
        self.opening_hours_api_version = self.extract_api_version(response.text, self.OPENING_HOURS_ACTION)
        yield response.follow(
            "https://www.plus.nl/ECP_Sitemap_Engine/rest/Sitemap/content-pages", callback=self.parse_sitemap
        )

    @staticmethod
    def extract_api_version(script_text: str, action_path: str) -> str | None:
        if match := re.search(r'"screenservices/' + re.escape(action_path) + r'"\s*,\s*"([^"]+)"', script_text):
            return match.group(1)
        return None

    def parse_sitemap(self, response: Response) -> Iterable[JsonRequest]:
        for loc in response.xpath("//*[local-name()='loc']/text()").getall():
            if match := re.search(r"/supermarkten/[^/]+_(\d+)$", loc):
                yield JsonRequest(
                    url=f"https://www.plus.nl/screenservices/{self.EXTENDED_DATA_ACTION}",
                    data={
                        "versionInfo": {
                            "moduleVersion": self.module_version,
                            "apiVersion": self.extended_data_api_version,
                        },
                        "viewName": "MainFlow.StorePage",
                        "inputParameters": {"StoreId": match.group(1)},
                    },
                    headers=self.api_headers(),
                    callback=self.parse_extended_data,
                )

    def parse_extended_data(self, response: Response) -> Iterable[JsonRequest]:
        store_str = response.json()["data"]["StoreStr"]
        store = store_str["Store"]
        address = store_str["StoreAddress"]

        if not store.get("Id") or store["Id"] == "0":
            return

        meta = {
            "ref": store["Id"],
            "name": store.get("StoreName"),
            "phone": store.get("Phone") or None,
            "email": store.get("Email") or None,
            "housenumber": address.get("HouseNumber") or None,
            "street": (address.get("Street") or "").strip() or None,
            "postcode": address.get("ZipCode") or None,
            "city": address.get("City") or None,
            "website": (
                f"https://www.plus.nl/supermarkten/{store_str['StoreSlug']}" if store_str.get("StoreSlug") else None
            ),
        }
        yield JsonRequest(
            url=f"https://www.plus.nl/screenservices/{self.OPENING_HOURS_ACTION}",
            data=self.opening_hours_payload(store["Id"]),
            headers=self.api_headers(),
            meta=meta,
            callback=self.parse_opening_hours,
        )

    def opening_hours_payload(self, store_id: str) -> dict:
        return {
            "versionInfo": {"moduleVersion": self.module_version, "apiVersion": self.opening_hours_api_version},
            "viewName": "MainFlow.StorePage",
            "screenData": {
                "variables": {
                    "Store": {
                        "StoreId": store_id,
                        "Name": "",
                        "Text": "",
                        "IsEcomStore": False,
                        "Address": "",
                        "City": "",
                        "Contact": "",
                        "Image": {"Url": "", "AltText": ""},
                        "Services": {"List": [], "EmptyListItem": {"Name": "", "Icon": {"Url": "", "AltText": ""}}},
                        "N_Column_Container": {
                            "InternalTitle": "",
                            "Title": "",
                            "anchorLinkTitle": "",
                            "Subtitle": "",
                            "SmallBanners": {
                                "List": [],
                                "EmptyListItem": {
                                    "InternalTitle": "",
                                    "Title": "",
                                    "Image": {"Url": "", "AltText": ""},
                                    "Link": "",
                                    "CTA": "",
                                    "BackgroundColor": "",
                                    "PlacementId": "",
                                },
                            },
                        },
                    },
                    "IsExpanded": False,
                    "RowLimit": 6,
                    "ButtonGroupInt": 1,
                    "LocalStoreId": store_id,
                    "StyleguideColorList": {
                        "List": [],
                        "EmptyListItem": {
                            "StyleguideColor": {"Id": 0, "ColorName": "", "BackgroundClass": "", "TextClass": ""}
                        },
                    },
                    "SlugParameter": "",
                    "_slugParameterInDataFetchStatus": 1,
                    "ActiveDevice": {"IsPhone": False, "IsTablet": False, "IsDesktop": True},
                    "_activeDeviceInDataFetchStatus": 1,
                }
            },
        }

    def parse_opening_hours(self, response: Response) -> Iterable[Feature]:
        data = response.json()["data"]
        address = data.get("AddressVar", {})

        item = Feature()
        item["ref"] = response.meta["ref"]
        item["name"] = response.meta["name"]
        item["phone"] = response.meta["phone"]
        item["email"] = response.meta["email"]
        item["website"] = response.meta["website"]
        item["housenumber"] = response.meta["housenumber"]
        item["street"] = response.meta["street"]
        item["postcode"] = response.meta["postcode"]
        item["city"] = response.meta["city"]
        item["country"] = address.get("CountryAddress") or "NL"

        if address.get("Latitude") and address["Latitude"] != "0.0":
            item["lat"] = address["Latitude"]
            item["lon"] = address["Longitude"]

        item["opening_hours"] = OpeningHours()
        for entry in data.get("StoreOpeningHour_Current", {}).get("List", []):
            day_name = date.fromisoformat(entry["Date"]).strftime("%A")
            if entry.get("IsStoreOpened"):
                item["opening_hours"].add_range(day_name, entry["OpenTime"], entry["CloseTime"])
            else:
                item["opening_hours"].set_closed(day_name)

        apply_yes_no(Extras.DELIVERY, item, bool(address.get("HasDelivery")))
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
