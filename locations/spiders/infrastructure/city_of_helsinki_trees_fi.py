from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CityOfHelsinkiTreesFISpider(Spider):
    name = "city_of_helsinki_trees_fi"
    item_attributes = {"operator": "Helsingin kaupunki", "operator_wikidata": "Q1757", "nsi_id": "N/A"}
    dataset_attributes = {
        "license": "Creative Commons Attribution 4.0 International",
        "license:website": "https://creativecommons.org/licenses/by/4.0/",
        "license:wikidata": "Q20007257",
        "attribution": "required",
        "attribution:name": "Source: Urban tree database of the City of Helsinki",
    }
    allowed_domains = ["kartta.hel.fi"]
    start_urls = [
        "https://kartta.hel.fi/ws/geoserver/avoindata/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=avoindata:Puurekisteri_piste&count=10000&startIndex=0&outputFormat=application/json&srsName=EPSG:4326"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 300}

    def parse(self, response):
        data = response.json()
        for tree in data["features"]:
            props = tree["properties"]
            item = Feature(
                ref=props["id"],
                lon=tree["geometry"]["coordinates"][0],
                lat=tree["geometry"]["coordinates"][1],
                city="Helsinki",
            )
            apply_category(Categories.NATURAL_TREE, item)
            item["extras"]["genus"] = props["suku"]
            if props["laji"] and props["laji"] != "sp.":
                item["extras"]["species"] = f"{props['suku']} {props['laji']}"
            if props["suomenknimi"]:
                item["extras"]["taxon:fi"] = props["suomenknimi"].lower()
            yield item

        for link in data["links"]:
            if link["rel"] == "next":
                yield response.follow(link["href"])
