import json

from scrapy import Spider

from locations.categories import apply_category
from locations.items import Feature


class GLSCGazetteerGYSpider(Spider):
    name = "glsc_gazetteer_gy"
    start_urls = ["https://gazetteer.glsc.gov.gy/gazetteer/data/NationalGazetteer_0.js"]
    no_refs = True

    cats = {
        "Village": {"place": "village"},
        "Township": {"place": "town"},
        "Settlement": {"place": "hamlet"},
        "Locality": {"place": "locality"},
        "Island": {"place": "island"},
        "River": {"waterway": "river"},
        "Mountain": {"natural": "peak"},
        "Creek": {"waterway": "stream"},
        "Estate": {"place": "isolated_dwelling"},
        "Fall": {"waterway": "waterfall"},
        "Falls": {"waterway": "waterfall"},
        "Rapid": {"waterway": "rapids"},
        "Rapids": {"waterway": "rapids"},
    }

    def parse(self, response, **kwargs):
        fc = json.loads(response.text.replace("var json_NationalGazetteer_0 =", ""))

        for feature in fc["features"]:
            item = Feature()
            item["geometry"] = feature["geometry"]
            item["name"] = feature["properties"]["NAME"]
            item["addr_full"] = feature["properties"]["LOCATION"]
            item["extras"]["addr:state:ref"] = feature["properties"]["REGIONAL_C"]

            if cat := self.cats.get(feature["properties"]["FEATURE"]):
                apply_category(cat, item)
            else:
                self.crawler.stats.inc_value(
                    f'atp/glsc_gazetteer_gy/unmapped_category/{feature["properties"]["FEATURE"]}'
                )
                item["extras"]["type"] = feature["properties"]["FEATURE"]

            yield item
