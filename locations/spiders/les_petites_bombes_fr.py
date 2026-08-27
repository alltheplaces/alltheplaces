from scrapy import Spider
from locations.categories import Categories, apply_category, apply_clothes, Clothes
from locations.items import Feature
from locations.hours import DAYS_FR, OpeningHours



class LesPetitesBombesFRSpider(Spider):
    name = "les_petites_bombes_fr"
    item_attributes = {
        "brand": "Les Petites Bombes", 
        "brand_wikidata": "Q141190957"
    }

    allowed_domains = ["lespetitesbombes.com"]

    start_urls = [
        "https://lespetitesbombes.com/pages/store-locator-les-petites-bombes",
    ]

    def parse(self, response):
        stores = response.css("map-viewer template")

        for store in stores:
            item = Feature()
            apply_category(Categories.SHOP_CLOTHES, item)
            apply_clothes(Clothes.WOMEN, item)


            item["ref"] = store.attrib.get("name")
            item["branch"] = store.css(".map-place-list__modal-store-name::text").get().removeprefix("LPB ")        
            item["addr_full"] = store.css(".map-place-list__modal-address::text").get()

            item["lat"] = store.attrib.get("latitude")
            item["lon"] = store.attrib.get("longitude")
            item["postcode"], item["city"] = store.css(".map-place-list__modal-city::text").get().split("\xa0")
            item["country"] = store.css(".map-place-list__modal-country::text").get()

            item["phone"] = store.css('a[href^="callto:"]::text').get()
            item["email"] = store.css('a[href^="mailto:"]::text').get()

            item["opening_hours"] = OpeningHours()
            for day in store.css(".map-place-list__modal-store-opening-hours::text").getall():
                item["opening_hours"].add_ranges_from_string(day, DAYS_FR)

            yield item 
            