from scrapy.spiders import CSVFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.licenses import Licenses


class VilleDeMontrealTreesCASpider(CSVFeedSpider):
    name = "ville_de_montreal_trees_ca"
    item_attributes = {"operator": "Ville de Montréal", "operator_wikidata": "Q340", "nsi_id": "N/A"}
    dataset_attributes = Licenses.CCBY4.value | {"attribution:name": "Ville de Montréal"}
    start_urls = [
        "https://donnees.montreal.ca/dataset/b89fd27d-4b49-461b-8e54-fa2b34a628c4/resource/64e28fe6-ef37-437a-972d-d1d3f1f7d891/download/arbres-publics.csv"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 300, "DOWNLOAD_WARNSIZE": 268435456}

    def parse_row(self, response, row):
        item = Feature(
            # Site numbers are only unique per borough and inventory (street or park)
            ref=f"{row['ARROND']}-{row['INV_TYPE']}-{row['EMP_NO']}",
            lat=row["Latitude"],
            lon=row["Longitude"],
            housenumber=row["No_civique"],
            street=row["Rue"],
            city="Montréal",
        )
        apply_category(Categories.NATURAL_TREE, item)
        if " " in row["Essence_latin"] and " sp." not in row["Essence_latin"]:
            item["extras"]["species"] = row["Essence_latin"]
        elif row["Essence_latin"] != "Divers":
            item["extras"]["genus"] = row["Essence_latin"].split(" ")[0]
        item["extras"]["taxon:fr"] = row["Essence_fr"]
        item["extras"]["taxon:en"] = row["Essence_ang"]
        if row["DHP"]:
            item["extras"]["diameter"] = f"{row['DHP']} cm"
        if row["Date_Plantation"]:
            item["extras"]["start_date"] = row["Date_Plantation"][:10]
        return item
