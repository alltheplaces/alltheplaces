from locations.categories import Categories, apply_category
from locations.country_utils import CountryUtils
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.state_clean_up import STATES


class GreystarSpider(JSONBlobSpider):
    name = "greystar"
    item_attributes = {
        "operator": "Greystar",
        "operator_wikidata": "Q60749135",
    }
    start_urls = ["https://www.greystar.com/api/properties/search?Distance=25000&Latitude=0&Longitude=0"]
    download_timeout = 120
    locations_key = "Results"

    def post_process_item(self, item, response, location):
        # "PropertyId" is a better ref than "Id" but it's not clean/unique
        item["website"] = response.urljoin(location["Path"])
        item["street_address"] = item.pop("addr_full")

        if len(location["Images"]) > 0:
            item["image"] = location["Images"][0]["Src"]

        # Try to guess the country, given just the state.
        # Sometimes the "State" field is the country.
        for country, states in STATES.items():
            if location["State"] in states:
                item["country"] = country
        if not item["country"]:
            item["country"] = CountryUtils().to_iso_alpha2_country_code(location["State"])

        apply_category(Categories.RESIDENTIAL_APARTMENTS, item)

        yield item
