import re
from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider

# LD hasOfferCatalog product codes to OSM fuel tags. Codes are exact product
# keys from asemat.neste.fi, comments give the Finnish display form.
FUEL_TYPES_MAPPING = {
    "BE95-E10": Fuel.E10,  # Neste Futura 95 E10 (95-oktan E10-bensiini)
    "BE98-E5": Fuel.E5,  # Neste Futura 98 E5 (98-oktan E5-bensiini)
    "DI-10/-20": Fuel.DIESEL,  # Neste Futura Diesel -10/-20 (talvidiesel)
    "DI-kesalaatu": Fuel.DIESEL,  # Neste Futura Diesel Kesälaatu (sommardiesel)
    "DI-29/-38": Fuel.DIESEL,  # Neste Futura Diesel -29/-38
    "DI-40/-40": Fuel.DIESEL,  # Neste Futura Diesel -40/-40
    "Neste-MY--10": Fuel.BIODIESEL,  # Neste MY Uusiutuva Diesel -10 (HVO)
    "Neste-MY--32": Fuel.BIODIESEL,  # Neste MY Uusiutuva Diesel -32 (HVO)
    "Pro-MPO--29-38": Fuel.UNTAXED_DIESEL,  # Neste Pro Moottoripolttoöljy -29/-38
    "Pro-MPO-Kesa": Fuel.UNTAXED_DIESEL,  # Neste Pro Moottoripolttoöljy kesälaatu
    "Neste-MY-PO-10": Fuel.HEATING_OIL,  # Neste MY Uusiutuva Polttoöljy -10
    "PO--29/-34": Fuel.UNTAXED_DIESEL,  # Neste Pro Moottoripolttoöljy -29/-34
    "PO--0/-7": Fuel.HEATING_OIL,  # Neste Tempera polttoöljy kesälaatu
    "BE-PRO-4T": Fuel.ALKYLATE,  # Neste Pro 4-T pienmoottoribensiini
    "BE-2-T": Fuel.ALKYLATE,  # Neste Pro 2-T pienmoottoribensiini
    "AdBlue": Fuel.ADBLUE,
    "Washer-fluid": None,  # Lasinpesuneste, not a fuel
    "bottled Gas": None,  # Pullokaasu, autogas ambiguity
    # Service codes occasionally leaking into the fuel catalogue
    "vacuum Cleaner": None,
    "child Care Room": None,
    "play Area": None,
    "trailer Rent": None,
    "disability Charging": None,
    "suitable For Heavy Vehicle": None,
    "gaiss": None,
}

# Service icon labels to OSM tags. Payment methods, cafés, shops and fuel
# display names carry no mappable tag. Raw stationService_* labels are
# untranslated template fallbacks.
SERVICES_MAPPING = {
    "Autopesu": Extras.CAR_WASH,
    "Imuri": Extras.VACUUM_CLEANER,
    "Rengaspaine": Extras.COMPRESSED_AIR,
    "Käteisautomaatti": Extras.ATM,
    "Lataus": Fuel.ELECTRIC,
    "Sähköautojen latauspiste": Fuel.ELECTRIC,
    "Truck+": Access.HGV,  # Neste Truck serves heavy transport
    "Sopii raskaille ajoneuvoille": Access.HGV,
    "Neste Futura 95 E10": None,
    "Neste Futura 98 E5": None,
    "Neste Futura Diesel -10/-20": None,
    "Neste Futura Diesel Kesälaatu": None,
    "Neste Futura Diesel -29/-38": None,
    "Neste Futura Diesel -40/-40": None,
    "Neste MY Uusiutuva Diesel -10": None,
    "Neste MY Uusiutuva Diesel -32": None,
    "Neste MY Uusiutuva Polttoöljy -10": None,
    "Neste Pro Moottoripolttoöljy -29/-38": None,
    "Neste Pro Moottoripolttoöljy -29/-34": None,
    "Neste Pro Moottoripolttoöljy kesälaatu": None,
    "Neste Tempera polttoöljy kesälaatu": None,
    "Neste Pro 4-T pienmoottoribensiini": None,
    "Neste Pro 2-T pienmoottoribensiini": None,
    "AdBlue": None,
    "Lasinpesuneste": None,
    "Pullokaasu": None,
    "Neste-kortti": None,
    "Kortti": None,
    "Neste-äppi": None,
    "Ravintola": None,
    "Kahvila": None,
    "Kauppa": None,
    "Autohuolto": None,
    "TI-halli": None,
    "Peräkärryvuokraus": None,
    "Autonvuokraus": None,
    "Leikkipaikka": None,
    "Lastenhoitohuone": None,
    "Saostuskaivo": None,
    "stationService_trailerFriendly": None,
    "stationService_disabilityCharging": None,
    "stationService_solarPanels": None,
}

HOTLINE_NUMBERS = {"+358800196196", "+35880020100"}


class NesteFISpider(SitemapSpider, StructuredDataSpider):
    name = "neste_fi"
    item_attributes = {"brand": "Neste", "brand_wikidata": "Q616376"}
    drop_attributes = {"image"}
    allowed_domains = ["asemat.neste.fi"]
    sitemap_urls = ["https://asemat.neste.fi/sitemap/fi.xml"]
    sitemap_rules = [(r"/neste-", "parse_sd")]
    search_for_email = False
    search_for_phone = False
    search_for_twitter = False
    search_for_facebook = False
    search_for_image = False
    wanted_types = ["GasStation"]

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            loc = entry.get("loc") if isinstance(entry, dict) else None
            if not isinstance(loc, str) or not loc:
                continue
            # Sitemap templating bug emits "[object Promise]" as locale prefix
            loc = loc.replace("/[object Promise]", "")
            if loc == "https://asemat.neste.fi/":
                continue
            entry["loc"] = loc
            yield entry

    @staticmethod
    def _fuel_names(ld_data: dict) -> list[str]:
        catalogs = ld_data.get("hasOfferCatalog")
        if isinstance(catalogs, dict):
            catalogs = [catalogs]
        elif not isinstance(catalogs, list):
            return []
        names = []
        for catalog in catalogs:
            if not isinstance(catalog, dict):
                continue
            elements = catalog.get("itemListElement", []) or []
            if isinstance(elements, dict):
                elements = [elements]
            for offer in elements:
                if not isinstance(offer, dict):
                    continue
                offered = offer.get("itemOffered") or {}
                if isinstance(offered, str):
                    product = offered
                elif isinstance(offered, dict):
                    product = offered.get("name")
                else:
                    continue
                if isinstance(product, str) and product:
                    names.append(product)
        return names

    @staticmethod
    def _clean_phone(value: Any) -> str | None:
        if isinstance(value, str):
            candidates = [value]
        elif isinstance(value, list):
            candidates = [p for p in value if isinstance(p, str)]
        else:
            return None
        for candidate in candidates:
            for part in (p.strip() for p in candidate.split(",")):
                if part and re.sub(r"[\s\-]", "", part) not in HOTLINE_NUMBERS:
                    return part
        return None

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        if m := re.search(r"Asemanumero:\s*(\d+)", response.text):
            item["ref"] = m.group(1)

        if name := item.pop("name", None):
            if name.startswith("Neste Express "):
                item["branch"] = name.removeprefix("Neste Express ")
                item["name"] = "Neste Express"
            elif name.startswith("Neste Truck "):
                item["branch"] = name.removeprefix("Neste Truck ")
                item["name"] = "Neste Truck"
            elif name.startswith("Neste veneasema "):
                item["branch"] = name.removeprefix("Neste veneasema ")
                item["name"] = "Neste veneasema"
            elif name.startswith("Neste "):
                item["branch"] = name.removeprefix("Neste ")
                item["name"] = "Neste"
            else:
                item["name"] = name

        if item.get("phone"):
            item["phone"] = self._clean_phone(item.get("phone"))

        url = (response.url or "").lower()
        if "-veneasema-" in url:
            apply_category(Categories.BOAT_FUEL_STATION, item)
        else:
            apply_category(Categories.FUEL_STATION, item)

        for fuel in self._fuel_names(ld_data):
            if fuel not in FUEL_TYPES_MAPPING:
                self.crawler.stats.inc_value("atp/neste_fi/fuel/unmapped/{}".format(fuel.replace("/", "-")))
            elif tag := FUEL_TYPES_MAPPING[fuel]:
                apply_yes_no(tag, item, True)
        services = response.xpath('//*[contains(@class, "ServiceIcon_text")]/text()').getall()
        for service in [s.strip() for s in services if s.strip()]:
            if service not in SERVICES_MAPPING:
                self.crawler.stats.inc_value("atp/neste_fi/service/unmapped/{}".format(service.replace("/", "-")))
            elif tag := SERVICES_MAPPING[service]:
                apply_yes_no(tag, item, True)

        if "-truck-" in url:
            apply_yes_no(Access.HGV, item, True)
        yield item
