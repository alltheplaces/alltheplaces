from locations.categories import apply_category
from locations.json_blob_spider import JSONBlobSpider


class GreystarSpider(JSONBlobSpider):
    name = "greystar"
    item_attributes = {
        "operator": "Greystar",
        "operator_wikidata": "Q60749135",
    }
    start_urls = ["https://www.greystar.com/api/properties/search?Distance=25000&Latitude=0&Longitude=0"]
    download_timeout = 60
    locations_key = "Results"

    def post_process_item(self, item, response, location):
        # "PropertyId" is a better ref than "Id" but it's not clean/unique
        item["website"] = response.urljoin(location["Path"])
        item["street_address"] = item.pop("addr_full")

        if len(location["Images"]) > 0:
            item["image"] = location["Images"][0]["Src"]

        apply_category({"landuse": "residential", "residential": "apartments"}, item)

        yield item
