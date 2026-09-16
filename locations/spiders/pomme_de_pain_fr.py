import chompjs

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class PommeDePainFRSpider(JSONBlobSpider):
    name = "pomme_de_pain_fr"
    item_attributes = {
        "brand": "Pomme de Pain",
        "brand_wikidata": "Q3276265",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = ["https://cdn-app.myli.io/my/widget/232-NjliMGI5MGNkYmUzMjc4OGYxMTYzMj/widget.js"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.text.split("spots:")[1])

    def post_process_item(self, item, response, location):
        apply_category(Categories.FAST_FOOD, item)
        if "Pastabella" not in (item.get("name") or ""):
            item["ref"] = location.get("placeid")
            item["branch"] = (item.pop("name", "") or "").removeprefix("Pomme de Pain ")
            yield item
