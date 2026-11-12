from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class PizzaHutAUSpider(JSONBlobSpider):
    name = "pizza_hut_au"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    start_urls = [
        "https://store.prod.pizzahutaustralia.com.au/api/v1/store?includeComingSoon=false&includeTradingDays=true"
    ]
    name_is_branch = True

    def post_process_item(self, item, response, feature):
        item["street_address"] = merge_address_lines([feature["addressLine1"], feature["addressLine2"]])

        for fulfilment in feature["tradingDaysSummary"]:
            if fulfilment["fulfilmentType"] == "Pickup":
                oh = OpeningHours()
                for day in fulfilment["tradingWeek"]:
                    for period in day["timePeriods"]:
                        oh.add_range(day["dayOfWeek"], period["startTime"], period["endTime"])
                item["opening_hours"] = oh

        apply_category(Categories.RESTAURANT, item)
        apply_yes_no(Extras.DELIVERY, item, True)
        apply_yes_no(Extras.TAKEAWAY, item, True)
        yield item
