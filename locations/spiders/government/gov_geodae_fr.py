from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.items import Feature
from locations.licenses import Licenses


class GovGeodaeFRSpider(CSVFeedSpider):
    name = "gov_geodae_fr"
    allowed_domains = ["www.data.gouv.fr", "static.data.gouv.fr"]
    # https://www.data.gouv.fr/datasets/geodae-base-nationale-des-defibrillateurs
    start_urls = ["https://www.data.gouv.fr/api/1/datasets/r/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c"]
    delimiter = ";"
    # robots.txt disallows /api/, which is where data.gouv.fr's stable download links point.
    custom_settings = {"ROBOTSTXT_OBEY": False}
    dataset_attributes = Licenses.ETALAB2.value | {
        "attribution:name": "Géo'DAE, Ministère de la Santé",
        "attribution:website": "https://geodae.atlasante.fr/",
    }

    def parse_row(self, response, row):
        # Mobile devices are carried in vehicles and have no fixed location.
        if row["c_etat_fonct"] != "En fonctionnement" or row["c_doublon"] == "t" or row["c_dae_mobile"] == "t":
            return
        item = Feature()
        item["ref"] = row["c_gid"]
        item["lat"] = row["c_lat_coor1"]
        item["lon"] = row["c_long_coor1"]
        item["housenumber"] = row["c_adr_num"]
        item["street"] = row["c_adr_voie"]
        item["postcode"] = row["c_com_cp"]
        item["city"] = row["c_com_nom"]
        item["operator"] = row["c_expt_rais"]
        item["extras"]["start_date"] = row["c_date_instal"]
        item["extras"]["defibrillator:location"] = row["c_acc_complt"]
        # "Mo-Su off" is the form's default and is also set on outdoor units open around the clock.
        if not row["c_dispo_horaires"].startswith(("Mo-Su off", "OFF")):
            item["opening_hours"] = row["c_dispo_horaires"]
        apply_yes_no("indoor", item, row["c_acc"] == "Intérieur", True)
        if row["c_acc_lib"] == "t":
            item["extras"]["access"] = "yes"
        apply_category(Categories.DEFIBRILLATOR, item)
        return item
