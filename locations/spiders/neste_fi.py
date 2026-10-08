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
    item_attributes = {"brand": "Neste", "brand_wikidata": "Q616376", "name": "Neste"}
    allowed_domains = ["asemat.neste.fi"]
    sitemap_urls = ["https://asemat.neste.fi/sitemap/fi.xml"]
    sitemap_rules = [(r"/neste-", "parse_sd")]
    search_for_email = False
    search_for_phone = False
    search_for_twitter = False
    search_for_facebook = False
    search_for_image = False

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            # Sitemap templating bug emits "[object Promise]" as locale prefix
            entry["loc"] = entry["loc"].replace("/[object Promise]", "")
            if entry["loc"] == "https://asemat.neste.fi/":
                continue
            yield entry

    def post_process_item(
        self, item: Feature, response: TextResponse, ld_data: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        if ld_data.get("@type") != "GasStation":
            self.crawler.stats.inc_value("atp/neste_fi/type/skip/{}".format(ld_data.get("@type")))
            return
        if m := re.search(r"Asemanumero:\s*(\d+)", response.text):
            item["ref"] = m.group(1)
        else:
            self.crawler.stats.inc_value("atp/neste_fi/ref/missing")
            return
        if name := item.pop("name", None):
            if branch := re.sub(r"\s+", " ", name.removeprefix("Neste ").strip()):
                item["branch"] = branch
        if phone := item.get("phone"):
            phone = phone.split(",")[0].strip()
            item["phone"] = None if phone in HOTLINE_NUMBERS else phone
        item.pop("image", None)
        item.pop("twitter", None)
        item.pop("facebook", None)
        if "-veneasema-" in response.url:
            apply_category(Categories.BOAT_FUEL_STATION, item)
        else:
            apply_category(Categories.FUEL_STATION, item)
        fuels = []
        if isinstance(ld_data.get("hasOfferCatalog"), dict):
            for offer in ld_data["hasOfferCatalog"].get("itemListElement", []) or []:
                if product := (offer.get("itemOffered") or {}).get("name"):
                    fuels.append(product)
        for fuel in fuels:
            if fuel not in FUEL_TYPES_MAPPING:
                self.crawler.stats.inc_value("atp/neste_fi/fuel/unmapped/{}".format(fuel))
            elif tag := FUEL_TYPES_MAPPING[fuel]:
                apply_yes_no(tag, item, True)
        services = response.xpath('//*[contains(@class, "ServiceIcon_text")]/text()').getall()
        for service in [s.strip() for s in services if s.strip()]:
            if service not in SERVICES_MAPPING:
                self.crawler.stats.inc_value("atp/neste_fi/service/unmapped/{}".format(service))
            elif tag := SERVICES_MAPPING[service]:
                apply_yes_no(tag, item, True)
        if "-truck-" in response.url:
            apply_yes_no(Access.HGV, item, True)
        yield item
