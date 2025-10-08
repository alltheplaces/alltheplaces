from locations.storefinders.nomnom import NomNomSpider


class FreddysUSSpider(NomNomSpider):
    name = "freddys_us"
    start_urls = ["https://www.freddys.com/api/stores"]
    item_attributes = {
        "brand": "Freddy's",
        "brand_wikidata": "Q5496837",
    }

    def post_process_item(self, item, response, feature):
        item["website"] = f"https://www.freddys.com/location/{feature['slug']}"
        yield item
