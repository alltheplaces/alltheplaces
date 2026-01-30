from typing import Any, AsyncIterator

import chompjs
from scrapy import Request
from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.react_server_components import parse_rsc


class IntermarcheSpider(SitemapSpider):
    name = "intermarche"
    allowed_domains = ["intermarche.com"]
    sitemap_urls = ["https://www.intermarche.com/sitemap.xml"]
    sitemap_rules = [(r"/magasins/\d+/[^/]+/infos-pratiques$", "parse")]

    INTERMARCHE = {
        "brand": "Intermarché",
        "brand_wikidata": "Q3153200",
    }
    INTERMARCHE_SUPER = {
        "brand": "Intermarché Super",
        "brand_wikidata": "Q98278038",
    }
    INTERMARCHE_CONTACT = {
        "brand": "Intermarché Contact",
        "brand_wikidata": "Q98278049",
    }
    INTERMARCHE_EXPRESS = {
        "brand": "Intermarché Express",
        "brand_wikidata": "Q98278043",
    }
    INTERMARCHE_HYPER = {
        "brand": "Intermarché Hyper",
        "brand_wikidata": "Q98278022",
    }
    LA_POSTE_RELAIS = {
        "brand": "Pickup Station",
        "brand_wikidata": "Q110748562",
        "operator": "La Poste",
        "operator_wikidata": "Q373724",
    }

    STORE_SERVICES = {
        "dis": Extras.ATM,  # distributeur
        "FR_IM_DRIVE_SANS_SAC": Extras.DRIVE_THROUGH,
        "drv": Extras.DRIVE_THROUGH,
        "POINT-RETRAIT-COLIS": Extras.PARCEL_PICKUP,
        "inpost": Extras.PARCEL_PICKUP,
        "FR_IM_MONDIAL_RELAY": Extras.PARCEL_PICKUP,
        "FR_IM_POINT_DE_RETRA1": Extras.PARCEL_PICKUP,
        "FR_IM_RETRAIT_COLIS_": Extras.PARCEL_PICKUP,
        "TOILETTES": Extras.TOILETS,
        "HOTSPOT-WIFI": Extras.WIFI,
        "BORNE_CHARGE_ELEC": Fuel.ELECTRIC,
    }

    FUEL_SERVICES = {
        # Services
        "GONFLEUR_PNEUS": Extras.COMPRESSED_AIR,
        "FR_IM_ASPIRATEUR": Extras.VACUUM_CLEANER,
        "PISTE_POIDS_LOURD": Access.HGV,  # truck lane
        "BORNE_CHARGE_ELEC": Fuel.ELECTRIC,
        "FR_IM_BORNE_DE_RECHA": Fuel.ELECTRIC,
        # Fuel types
        "GAZOLE": Fuel.DIESEL,
        "SP95": Fuel.OCTANE_95,
        "SP95E10": Fuel.E10,
        "SP98": Fuel.OCTANE_98,
        "E85": Fuel.E85,
        "gpl": Fuel.LPG,
        "ADBLUE": Fuel.ADBLUE,
    }

    item_attributes = {"country": "FR"}

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_TIMEOUT": 180,
        "CONCURRENT_REQUESTS": 4,
    }

    async def start(self) -> AsyncIterator[Request]:
        for url in self.sitemap_urls:
            yield Request(
                url,
                self._parse_sitemap,
                meta={"zyte_api": {"httpResponseBody": True, "geolocation": "FR"}},
            )

    def _parse_sitemap(self, response):
        for request in super()._parse_sitemap(response):
            request.meta["zyte_api"] = {
                "browserHtml": True,
                "geolocation": "FR",
                "javascript": True,
            }
            yield request

    def extract_nextjs_data(self, response: Response) -> dict:
        """Extract and parse Next.js React Server Components data."""
        scripts = response.xpath("//script[starts-with(text(), 'self.__next_f.push')]/text()").getall()
        objs = [chompjs.parse_js_object(s) for s in scripts]
        rsc = "".join([s for n, s in objs]).encode()
        return dict(parse_rsc(rsc))

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = self.extract_nextjs_data(response)

        pdv_data = DictParser.get_nested_key(data, "pdv")
        if not pdv_data:
            self.logger.warning(f"Could not extract pdv data from {response.url}")
            return

        gas_station_data = DictParser.get_nested_key(data, "gasStationInformation")

        if addr := pdv_data.get("address"):
            pdv_data["latitude"] = addr.get("latitude")
            pdv_data["longitude"] = addr.get("longitude")

        item = DictParser.parse(pdv_data)
        item["website"] = response.url

        if store_hours := pdv_data.get("storeHours"):
            item["opening_hours"] = self.parse_opening_hours(store_hours)

        store_format = pdv_data.get("format", "")
        if store_format == "Super":
            item.update(self.INTERMARCHE_SUPER)
        elif store_format == "Contact":
            item.update(self.INTERMARCHE_CONTACT)
        elif store_format == "Express":
            item.update(self.INTERMARCHE_EXPRESS)
        elif store_format == "Hyper":
            item.update(self.INTERMARCHE_HYPER)
        elif store_format == "Retrait La Poste":
            item.update(self.LA_POSTE_RELAIS)
            apply_category(Categories.PARCEL_LOCKER, item)
            item["located_in"], item["located_in_wikidata"] = self.INTERMARCHE.values()
        elif store_format == "Pro & Assos":
            apply_category(Categories.SHOP_E_CIGARETTE, item)
            item["located_in"], item["located_in_wikidata"] = self.INTERMARCHE.values()
        elif store_format == "Réservé Soignants":
            return  # Skip medical worker-only stores
        elif store_format:
            self.crawler.stats.inc_value(f"atp/intermarche/unmapped_store_format/{store_format}")

        services = set(pdv_data.get("allServicesCodes", []))

        # Check for fuel station ("ess" = essence)
        if "ess" in services and gas_station_data:
            yield from self.create_fuel_station(item, gas_station_data)

        yield from self.parse_accessory_units(item, services)

        for code in services:
            if attr := self.STORE_SERVICES.get(code):
                apply_yes_no(attr, item, True)
            else:
                self.crawler.stats.inc_value(f"atp/intermarche/unmapped_store_service/{code}")

        yield item

    def parse_accessory_units(self, item: Feature, services: set[Any]):
        car_wash_codes = {"lav", "lavr", "lavp"}
        if car_wash_codes.intersection(services):
            car_wash = item.deepcopy()
            car_wash["ref"] = f"{item['ref']}_carwash"
            car_wash.update(self.INTERMARCHE)
            apply_category(Categories.CAR_WASH, car_wash)
            yield car_wash

    def parse_opening_hours(self, hours_list: list) -> OpeningHours:
        oh = OpeningHours()
        for entry in hours_list:
            if entry.get("is24"):
                oh.add_days_range(DAYS, "00:00", "24:00")
            else:
                days_mask = entry.get("days", "")
                start = entry.get("startHours")
                end = entry.get("endHours")
                if days_mask and start and end:
                    for i, is_open in enumerate(days_mask):
                        if is_open == "1" and i < 7:
                            oh.add_range(DAYS[i], start, end)
        return oh

    def create_fuel_station(self, store_item: Feature, gas_station_data: dict):
        fuel = store_item.deepcopy()
        fuel["ref"] = f"{store_item['ref']}_fuel"
        fuel.update(self.INTERMARCHE)

        if gas_addr := gas_station_data.get("address"):
            if lat := gas_addr.get("latitude"):
                fuel["lat"] = lat
            if lon := gas_addr.get("longitude"):
                fuel["lon"] = lon
            if street := gas_addr.get("address"):
                fuel["street_address"] = street

        if gas_hours := gas_station_data.get("openingHours"):
            fuel["opening_hours"] = self.parse_opening_hours(gas_hours)

        all_services = gas_station_data.get("services", []) + gas_station_data.get("unpublishedServices", [])
        for service in all_services:
            code = service.get("code")
            if attr := self.FUEL_SERVICES.get(code):
                apply_yes_no(attr, fuel, True)
            else:
                self.crawler.stats.inc_value(f"atp/intermarche/unmapped_fuel_service/{code}")

        apply_category(Categories.FUEL_STATION, fuel)
        yield fuel
