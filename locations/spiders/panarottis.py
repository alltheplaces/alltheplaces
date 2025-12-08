from locations.spiders.rocomamas import RocomamasSpider

PANAROTTIS_COUNTRIES = {
    "NA",
    "NG",
    "SZ",
    "ZM",
    "ZA",
}

PANAROTTIS_BRANDS = {
    "PANA": {"brand": "Panarottis", "brand_wikidata": "Q130220087"},
}


class PanarottisSpider(RocomamasSpider):
    name = "panarottis"
    start_urls = ["https://www.panarottis.com/api/proxy"]
    base_url = "https://www.panarottis.com/"
    countries = PANAROTTIS_COUNTRIES
    brands = PANAROTTIS_BRANDS
