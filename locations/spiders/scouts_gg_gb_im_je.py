from scrapy.http import JsonRequest

from locations.json_blob_spider import JSONBlobSpider


class ScoutsGGGBIMJESpider(JSONBlobSpider):
    name = "scouts_gg_gb_im_je"
    item_attributes = {
        "brand": "The Scout Association",
        "brand_wikidata": "Q849740",
    }
    start_urls = ["https://groupfinder.azurewebsites.net/GroupFinder?page=1&pageSize=500&location=london"]
    locations_key = "Data"
    skip_auto_cc_domain = True

    def parse(self, response):
        features = self.extract_json(response)
        yield from self.parse_feature_array(response, features)
        if not response.json()["PagingData"]["LastPage"]:
            yield JsonRequest(
                url="https://groupfinder.azurewebsites.net" + response.json()["PagingData"]["nextPage"],
                callback=self.parse,
            )

    def post_process_item(self, item, response, location):
        if item.get("postcode") is not None and item["postcode"].lower() == "null":
            item.pop("postcode")
        item["website"] = f"https://www.scouts.org.uk/groups/{location['Id']}?slug={location['Slug']}"
        yield item
