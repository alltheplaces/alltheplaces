from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class FastsignsSpider(JSONBlobSpider):
    name = "fastsigns"
    item_attributes = {
        "brand": "Fastsigns",
        "brand_wikidata": "Q5437127",
    }
    # Not covered: Dominican Republic, Grand Cayman, Malta
    start_urls = [
        "https://www.fastsigns.com/locations/?CallAjax=AllLocations",  # covers CA, PR, US
        "https://www.fastsigns.co.uk/locations/?CallAjax=AllLocations",
        "https://www.fastsigns.cl/locales/?CallAjax=AllLocations",
        "https://www.signwave.com.au/locations/?CallAjax=AllLocations",
    ]

    def post_process_item(self, item, response, location):
        item.pop("name")
        item["street_address"] = merge_address_lines([location["Address1"], location["Address2"]])
        item["extras"]["addr:unit"] = location["Address2"]
        item["ref"] = location["FranchiseLocationID"]
        item["branch"] = location["FriendlyName"]
        item["website"] = response.urljoin(location["Path"])

        if location["LaunchDate"][:10] not in ("2021-07-19", "2022-07-07", "2022-08-29", "2022-11-28"):
            item["extras"]["start_date"] = location["LaunchDate"][:10]
        if location["StorefrontImage"]:
            item["image"] = response.urljoin(location["StorefrontImage"])

        if location["Country"] == "AUS":
            item["name"] = item["brand"] = "Signwave"
            item["brand_wikidata"] = "Q136850122"

        yield item
