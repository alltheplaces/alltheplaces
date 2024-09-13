from locations.storefinders.woosmap import WoosmapSpider


class EuronicsDESpider(WoosmapSpider):
    name = "euronics_de"
    item_attributes = {"brand": "Euronics", "brand_wikidata": "Q2693387"}
    key = "woos-f424377a-a2dd-3fe8-b3cb-0337ebf2ae0a"
    origin = "https://www.euronics.de"

    def parse_item(self, item, feature, **kwargs):
        if "mediaathome" in feature["properties"]["contact"]["website"]:
            item["brand"] = "media@Home"
            item["brand_wikidata"] = "Q117707176"
        yield item
