from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature

LEAF_TYPES = {"Laubbäume": "broadleaved", "Obstbäume": "broadleaved", "Nadelbäume": "needleleaved"}


class BerlinTreesDESpider(Spider):
    name = "berlin_trees_de"
    item_attributes = {"operator": "Land Berlin", "operator_wikidata": "Q64", "nsi_id": "N/A"}
    dataset_attributes = {
        "license": "Data licence Germany – Zero – Version 2.0",
        "license:website": "https://www.govdata.de/dl-de/zero-2-0",
        "license:wikidata": "Q56064789",
        "attribution": "optional",
    }
    allowed_domains = ["gdi.berlin.de"]
    start_urls = [
        f"https://gdi.berlin.de/services/wfs/baumbestand?service=WFS&version=2.0.0&request=GetFeature&typeNames=baumbestand:{layer}&count=10000&outputFormat=application/json&srsName=EPSG:4326"
        for layer in ("strassenbaeume", "anlagenbaeume")
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def parse(self, response):
        data = response.json()
        for tree in data["features"]:
            props = tree["properties"]
            if props["art_gruppe"] == "Großsträucher":
                continue
            item = Feature(
                ref=tree["id"],
                lon=tree["geometry"]["coordinates"][0],
                lat=tree["geometry"]["coordinates"][1],
                street=props.get("strname"),
                city="Berlin",
            )
            apply_category(Categories.NATURAL_TREE, item)
            if props["art_bot"] and not props["art_bot"].endswith(" spec."):
                item["extras"]["species"] = props["art_bot"]
            item["extras"]["taxon:de"] = props["art_dtsch"]
            item["extras"]["genus"] = props["gattung"]
            item["extras"]["leaf_type"] = LEAF_TYPES.get(props["art_gruppe"])
            item["extras"]["start_date"] = props["pflanzjahr"]
            if props["stammumfg"]:
                item["extras"]["circumference"] = f"{props['stammumfg']} cm"
            if props["baumhoehe"]:
                item["extras"]["height"] = f"{props['baumhoehe']} m"
            if props["kronedurch"]:
                item["extras"]["diameter_crown"] = f"{props['kronedurch']} m"
            yield item

        for link in data.get("links", []):
            if link["rel"] == "next":
                yield response.follow(link["href"])
