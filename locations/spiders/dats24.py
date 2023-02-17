import json

import scrapy

from locations.items import Feature


class Dats24BESpider(scrapy.Spider):
    name = "dats24_be"
    item_attributes = {"brand": "DATS 24", "brand_wikidata": "Q15725576"}
    start_urls = ["https://customer.dats24.be/wps/portal/datscustomer/fr/b2c/locator"]

    def parse(self, response, **kwargs):
        script_tags = response.text.split("<script")
        for script_tag in script_tags:
            if 'class="locatorMapData"' in script_tag:
                start_index = script_tag.find(">") + 1
                end_index = script_tag.find("</script>", start_index)
                json_data = script_tag[start_index:end_index]
                break

        data = json.loads(json_data)
        for store in data.get("stores"):
            yield Feature(
                {
                    "ref": store.get("id"),
                    "name": store.get("name"),
                    "addr_full": " ".join(
                        filter(
                            None,
                            [store.get("houseNumber"), store.get("street"), store.get("city"), store.get("postalCode")],
                        )
                    ),
                    "street": store.get("street"),
                    "postcode": store.get("postalCode"),
                    "city": store.get("city"),
                    "housenumber": store.get("houseNumber"),
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                }
            )
