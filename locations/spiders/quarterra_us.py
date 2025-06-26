from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider

QUERY = """query {
  locations: entries(section: "communities", showInListing: true) {
    id
    title
    url
    ... on communities_community_Entry {
      thumbnail {
        url @transform(format: "jpg")
      }
      stateAndCity {
        title
        level
        ... on statesCities_Category {
          stateCode
        }
      }
      position: location {
        lat
        lng
      }
    }
  }
}
"""


class QuarterraUSSpider(JSONBlobSpider):
    name = "quarterra_us"
    item_attributes = {
        "operator": "Quarterra",
        "operator_wikidata": "Q134723073",
    }
    locations_key = ["data", "locations"]

    def start_requests(self):
        yield JsonRequest("https://quarterra.com/api", data={"query": QUERY})

    def post_process_item(self, item, response, feature):
        if len(feature["thumbnail"]) > 0:
            item["image"] = feature["thumbnail"][0]["url"]
        if states := [sc for sc in feature["stateAndCity"] if sc["level"] == 1]:
            item["state"] = states[0]["stateCode"]
        if cities := [sc for sc in feature["stateAndCity"] if sc["level"] == 2]:
            item["city"] = cities[0]["title"]

        apply_category(Categories.RESIDENTIAL_APARTMENTS, item)

        yield item
