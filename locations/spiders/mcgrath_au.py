import re

from locations.storefinders.algolia import AlgoliaSpider


class McGrathAUSpider(AlgoliaSpider):
    name = "mcgrath_au"
    item_attributes = {
        "brand_wikidata": "Q105290661",
        "brand": "McGrath",
    }
    api_key = "d1594f8570b9fa5a764d624db7ebd84e"
    app_id = "testingA3VXEX35KE"
    index_name = "office"

    def post_process_item(self, item, response, feature):
        item["branch"] = item.pop("name")
        item["lat"] = feature["_geoloc"]["lat"]
        item["lon"] = feature["_geoloc"]["lng"]
        item["image"] = feature["image"]
        slug = re.sub(r"\W+", "-", feature["name"].strip()).lower()
        item["website"] = f"https://www.mcgrath.com.au/offices/{slug}-{feature['id']}"
        yield item
