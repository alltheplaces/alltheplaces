import chompjs

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, DELIMITERS_FR, OpeningHours
from locations.json_blob_spider import JSONBlobSpider


class WashNDryFRSpider(JSONBlobSpider):
    name = "wash_n_dry_fr"
    item_attributes = {
        "brand": "Wash’N Dry",
        "brand_wikidata": "Q127277495",
    }
    start_urls = ["https://www.washndry-concept.com/nos-laveries/"]
    locations_key = "laveries"
    drop_attributes = ["state"]

    def extract_json(self, response):
        data = chompjs.parse_js_object(response.xpath('//script[contains(text(), "var Theme = ")]/text()').get())
        return chompjs.parse_js_object(data["laveries"])

    def post_process_item(self, item, response, location):
        item["ref"] = location["url"]
        item["branch"] = (
            (item.pop("name", "") or "").removeprefix("LAVERIE ").removeprefix("WASH’N DRY ").removeprefix("– ")
        )

        apply_category(Categories.SHOP_LAUNDRY, item)

        hours = (
            location["openings"]
            .lower()
            .replace("7j/7", "Lu-Di")
            .replace("7/7", "Lu-Di")
            .replace("h00", ":00")
            .replace("h30", ":00")
            .replace("h45", ":45")
        )

        item["opening_hours"] = OpeningHours()
        hours = location["openings"].lower().replace("7j/7","Lu-Di").replace("7/7","Lu-Di").replace("h00",":00").replace("h30",":00").replace("h45",":45")
        item["opening_hours"].add_ranges_from_string(hours, DAYS_FR, delimiters=DELIMITERS_FR)
        
        yield item
