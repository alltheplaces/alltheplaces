from typing import AsyncIterator, Iterable
from urllib.parse import urlencode

from scrapy.http import Request, TextResponse

from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

STORES_QUERY = """
query {
  stores {
    items {
      seller_code
      name
      url_key
      contact_phone
      contact_fax
      inauguration_date
      images_gallery
      position {
        latitude
        longitude
      }
      address {
        street
        address_additional
        indication
        postcode
        city
        country_code
      }
      opening_hours {
        dayofweek
        start_time
        end_time
      }
    }
  }
}
"""


class CulturaFRSpider(JSONBlobSpider):
    name = "cultura_fr"
    item_attributes = {"brand": "Cultura", "brand_wikidata": "Q3007154"}
    allowed_domains = ["www.cultura.com"]
    locations_key = ["data", "stores", "items"]
    requires_proxy = True

    async def start(self) -> AsyncIterator[Request]:
        yield Request(
            url="https://www.cultura.com/m2/graphql?" + urlencode({"query": STORES_QUERY}),
            headers={"Store": "cultura_b2c_fr_FR"},
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["seller_code"]
        item["branch"] = item.pop("name").removeprefix("Cultura ")
        item["website"] = f"https://www.cultura.com/les-magasins/{feature['url_key']}.html"

        address = feature["address"]
        item["street_address"] = merge_address_lines(
            [address["street"], address["address_additional"], address["indication"]]
        )
        item.pop("street", None)

        if images := feature["images_gallery"]:
            item["image"] = images[0]
        if fax := feature["contact_fax"]:
            item["extras"]["fax"] = fax
        if inauguration_date := feature["inauguration_date"]:
            item["extras"]["start_date"] = inauguration_date.split(" ")[0]

        item["opening_hours"] = OpeningHours()
        for rule in feature["opening_hours"]:
            item["opening_hours"].add_range(
                DAYS_FROM_SUNDAY[int(rule["dayofweek"])], rule["start_time"], rule["end_time"]
            )

        yield item
