from locations.categories import Categories, apply_category
from locations.storefinders.woosmap import WoosmapSpider


class AccorSpider(WoosmapSpider):
    name = "accor"
    key = "accor-prod-woos"
    origin = "https://accor.com"

    brand_mapping = {
        "SUI": {"brand": "Novotel", "brand_wikidata": "Q420545"},
        "NOV": {"brand": "Novotel", "brand_wikidata": "Q420545"},
        "NOL": {"brand": "Novotel", "brand_wikidata": "Q420545"},
        "IBS": {"brand": "Ibis Styles", "brand_wikidata": "Q3147425"},
        "PUL": {"brand": "Pullman Hotels and Resorts", "brand_wikidata": "Q3410757"},
        "IBH": {"brand": "Ibis Hotels", "brand_wikidata": "Q920166"},
        "IBB": {"brand": "Ibis Budget", "brand_wikidata": "Q1458135"},
        "ETP": {"brand": "Ibis Budget", "brand_wikidata": "Q1458135"},
        "SOL": {"brand": "Sofitel", "brand_wikidata": "Q749431"},
        "MOV": {"brand": "Mövenpick Hotels & Resorts", "brand_wikidata": "Q691162"},
        "MER": {"brand": "Mercure Hotels", "brand_wikidata": "Q1709809"},
        "BME": {"brand": "Mercure Hotels", "brand_wikidata": "Q1709809"},
        "ADG": {"brand": "Adagio", "brand_wikidata": "Q2823880"},
        "ADA": {"brand": "Adagio", "brand_wikidata": "Q2823880"},
        "ADP": {"brand": "Adagio", "brand_wikidata": "Q2823880"},
        "MSH": {"brand": "Mama Shelter", "brand_wikidata": "Q12716714"},
        "FAI": {"brand": "Fairmont Hotels and Resorts ", "brand_wikidata": "Q1393345"},
        "MEI": {"brand": "Mercure Hotels", "brand_wikidata": "Q1709809"},
        "MEL": {"brand": "Mercure Hotels", "brand_wikidata": "Q1709809"},
        "SEB": {"brand": "The Sebel", "brand_wikidata": "Q110888248"},
        "HOF": {"brand": "Hotel F1 ", "brand_wikidata": "Q1630895"},
        "MGA": {"brand": "MGallery", "brand_wikidata": "Q25419207"},
        "MGS": {"brand": "MGallery", "brand_wikidata": "Q25419207"},
        "SOF": {"brand": "Sofitel", "brand_wikidata": "Q749431"},
        "SWI": {"brand": "Swissôtel", "brand_wikidata": "Q1635974"},
        "SWL": {"brand": "Swissôtel", "brand_wikidata": "Q1635974"},
        "BAN": {"brand": "Banyan Tree", "brand_wikidata": "Q807019"},
        "RIX": {"brand": "Rixos Hotels", "brand_wikidata": "Q6075716"},
        "TWF": {"brand": "25hours Hotels", "brand_wikidata": "Q47503819"},
        "RAF": {"brand": "Raffles Hotels & Resorts", "brand_wikidata": "Q4306661"},
        "JOE": {"brand": "JO&JOE ", "brand_wikidata": "Q84600897"},
        "MTA": {"brand": "Mantra Hotels", "brand_wikidata": "Q110936540"},
        "BKF": {"brand": "BreakFree Hotels", "brand_wikidata": "Q110936724"},
        "PEP": {"brand": "Peppers Hotels", "brand_wikidata": "Q110936677"},
        "MOD": {"brand": "Mondrian Hotel", "brand_wikidata": "Q6898825"},
        "21C": {"brand": "21c Museum Hotels", "brand_wikidata": "Q4631016"},
        "ANG": {"brand": "Angsana", "brand_wikidata": "Q115489061"},
        "ART": {"brand": "Art Series", "brand_wikidata": "Q115489062"},
        "DHA": {"brand": "Dhawa"},
        "GRE": {"brand": "greet", "brand_wikidata": "Q115489066"},
        "MTS": {"brand": "Mantis"},
        "SO": {"brand": "SO/", "brand_wikidata": "Q115489077"},
        "SOU": {"brand": "Handwritten Collection"},
        "TRI": {"brand": "TRIBE", "brand_wikidata": "Q113694525"},
        # Not branded but managed by Accor
        "SAM": None,
        # TODO:
        # Table with brands by Accor: https://group.accor.com/en/sitemap
        # "ASE": 1,
        # "CAS": 3,
        # "DEL": 1,
        # "FAE": 1,
        # "GAR": 1,
        # "HOM": 2,
        # "HOX": 1,
        # "HYD": 2,
        # "MOL": 2,
        # "SLS": 7,
        # "TST": 6,
    }

    def parse_item(self, item, feature, **kwargs):
        if "COMING SOON" in item["name"].upper():
            return
        brand_id = feature["properties"]["types"][0]
        if match := self.brand_mapping.get(brand_id):
            item.update(match)
        else:
            self.crawler.stats.inc_value(f"atp/accor/unknown_brand/{brand_id}")
        item["website"] = f"https://all.accor.com/hotel/{item['ref']}/index.en.shtml"
        apply_category(Categories.HOTEL, item)
        yield item
