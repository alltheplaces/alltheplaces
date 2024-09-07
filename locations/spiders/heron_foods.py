from locations.hours import OpeningHours
from locations.storefinders.wordpress_heron_foods_spider import WordpressHeronFoodsSpider


class HeronFoodsSpider(WordpressHeronFoodsSpider):
    name = "heron_foods"
    item_attributes = {"brand": "Heron Foods", "brand_wikidata": "Q5743472"}
    domain = "heronfoods.com"
    custom_settings = {"ROBOTSTXT_OBEY": False}
    radius = 600
    lat = 51.5072178
    lon = -0.1275862

    def post_process_item(self, item, response, store):
        oh = OpeningHours()
        oh.add_range("Mo", store["op"]["0"].replace(".", ":"), store["op"]["1"].replace(".", ":"))
        oh.add_range("Tu", store["op"]["2"].replace(".", ":"), store["op"]["3"].replace(".", ":"))
        oh.add_range("We", store["op"]["4"].replace(".", ":"), store["op"]["5"].replace(".", ":"))
        oh.add_range(
            "Th",
            store["op"]["6"].replace(".", ":"),
            store["op"]["7"].replace(".", ":").replace("17:20:00", "17:20"),
        )
        oh.add_range("Fr", store["op"]["8"].replace(".", ":"), store["op"]["9"].replace(".", ":"))
        oh.add_range("Sa", store["op"]["10"].replace(".", ":"), store["op"]["11"].replace(".", ":"))
        oh.add_range("Su", store["op"]["12"].replace(".", ":"), store["op"]["13"].replace(".", ":"))

        item["opening_hours"] = oh.as_opening_hours()
        item["country"] = "GB"

        if item["name"].endswith(" (B&M Express)"):
            item["name"] = item["name"].replace(" (B&M Express)", "")
            item["brand"] = "B&M Express"
            item["brand_wikidata"] = "Q99640578"

        yield item
