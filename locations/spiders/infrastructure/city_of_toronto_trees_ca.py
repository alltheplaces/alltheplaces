import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.items import Feature


class CityOfTorontoTreesCASpider(Spider):
    name = "city_of_toronto_trees_ca"
    item_attributes = {"operator": "City of Toronto", "operator_wikidata": "Q172", "nsi_id": "N/A"}
    dataset_attributes = {
        "license": "Open Government Licence – Toronto",
        "license:website": "https://open.toronto.ca/open-data-license/",
        "attribution": "required",
        "attribution:name": "Contains information licensed under the Open Government Licence – Toronto.",
    }
    allowed_domains = ["ckan0.cf.opendata.inter.prod-toronto.ca"]
    start_urls = [
        "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/datastore_search?resource_id=3dafa392-c6ab-4f37-9bf9-21ddf7308eaf&limit=32000&sort=_id"
    ]
    custom_settings = {"DOWNLOAD_TIMEOUT": 120}

    def parse(self, response):
        result = response.json()["result"]
        for tree in result["records"]:
            lon, lat = json.loads(tree["geometry"])["coordinates"]
            item = Feature(
                ref=tree["STRUCTID"],
                lat=lat,
                lon=lon,
                housenumber=str(tree["ADDRESS"]),
                street=tree["STREETNAME"],
                city="Toronto",
            )
            apply_category(Categories.NATURAL_TREE, item)
            if " " in tree["BOTANICAL_NAME"] and not tree["BOTANICAL_NAME"].endswith(" spp."):
                item["extras"]["species"] = tree["BOTANICAL_NAME"]
            elif tree["BOTANICAL_NAME"] != "None":
                item["extras"]["genus"] = tree["BOTANICAL_NAME"].split(" ")[0]
            if tree["DBH_TRUNK"]:
                item["extras"]["diameter"] = f"{tree['DBH_TRUNK']} cm"
            yield item

        if result["records"]:
            yield response.follow(result["_links"]["next"])
