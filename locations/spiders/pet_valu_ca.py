from locations.categories import Categories, apply_category
from locations.storefinders.stat import StatSpider


class PetValuCASpider(StatSpider):
    name = "pet_valu_ca"
    PET_VALUE = {"brand": "Pet Valu", "brand_wikidata": "Q58009635"}
    start_urls = ["https://store.petvalu.ca/stat/api/locations/search?limit=20000&fields=displayname_location_name"]

    def post_process_item(self, item, response, store):
        if store["businessName"] == "Pet Valu":
            item.update(self.PET_VALUE)
        else:
            item["brand"] = item["name"] = store["businessName"]

        item["branch"] = store["displayFields"]["displayname_location_name"]

        apply_category(Categories.SHOP_PET, item)

        yield item
