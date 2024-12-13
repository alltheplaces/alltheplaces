from scrapy.spiders import SitemapSpider

from locations.categories import Extras, PaymentMethods, apply_yes_no
from locations.hours import OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class TheCoffeeBeanAndTeaLeafSpider(SitemapSpider, StructuredDataSpider):
    name = "the_coffee_bean_and_tea_leaf"
    item_attributes = {
        "brand": "The Coffee Bean & Tea Leaf",
        "brand_wikidata": "Q1141384",
    }
    sitemap_urls = ["https://www.coffeebean.com/sitemap.xml"]
    sitemap_rules = [
        (r"/stores?/.+", "parse"),
        (r"/node/\d+", "parse"),
    ]
    search_for_facebook = False
    search_for_twitter = False

    def parse(self, response):
        geolist = response.xpath("//span[@property='geo']")
        if geolist:
            geo = geolist[0]
            geo.drop()
            response.xpath("//div[@vocab]")[0].root.append(geo.root)
            response.xpath("//div[@typeof='Place']")[0].drop()
        yield from self.parse_sd(response)

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("name"):
            item["branch"] = item.pop("name").removeprefix("The Coffee Bean & Tea Leaf ")
        else:
            item["branch"] = response.css(".field--name-title::text").get()

        if item.get("country") == "NULL":
            del item["country"]

        oh = OpeningHours()
        for hours in response.css(".paragraph--type--store-hours"):
            if weekday := hours.css(".field--name-field-weekday::text").get():
                if weekday.endswith(" CLOSED"):
                    oh.set_closed(weekday.removesuffix(" CLOSED"))
                else:
                    hours_open = hours.css(".field--name-field-store-open::text").get()
                    hours_close = hours.css(".field--name-field-store-closed::text").get()
                    try:
                        oh.add_range(weekday, hours_open, hours_close, "%I:%M%p")
                    except ValueError:
                        oh.add_ranges_from_string(f"{weekday} {hours_open}-{hours_close}")
        item["opening_hours"] = oh

        yield item

    def extract_amenity_features(self, item, response, ld_item):
        features = set(ld_item.get("amenityFeature", []))
        apply_yes_no(Extras.WIFI, item, "Wifi" in features)
        apply_yes_no("payment:gift_card", item, "Gift Cards Accepted" in features)
        apply_yes_no(PaymentMethods.CONTACTLESS, item, "Mobile Payments" in features)
        apply_yes_no(Extras.OUTDOOR_SEATING, item, "Outdoor Seating" in features)
