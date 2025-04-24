from scrapy import Spider

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines


class CoventryBuildingSocietyGBSpider(Spider):
    name = "coventry_building_society_gb"
    item_attributes = {
        "brand": "Coventry Building Society",
        "brand_wikidata": "Q5179055",
    }
    start_urls = ["https://www.coventrybuildingsociety.co.uk/content/datasource/api/branch/allbranches.data.json"]

    def parse(self, response, **kwargs):
        for location in response.json()["branches"]:
            item = DictParser.parse(location["address"])
            item["ref"] = location["branchdetails"]["branchname"]
            item["street_address"] = merge_address_lines(
                [location["address"].get("address1"), location["address"].get("address2")]
            )
            if "html" in location["branchdetails"]["branchnumber"]:
                item["branch"] = (
                    location["branchdetails"]["branchnumber"]
                    .replace("/content/cbs/member/en/our-branches/", "")
                    .replace(".html", "")
                )
                item["website"] = (
                    "https://www.coventrybuildingsociety.co.uk/member/our-branches/" + item["branch"] + ".html"
                )
                item["name"] = "Coventry Building Society"
            else:
                item["name"] = location["branchdetails"]["branchname"]
            yield item
