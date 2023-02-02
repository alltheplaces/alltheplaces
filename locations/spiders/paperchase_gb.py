from locations.spiders.next_gb import NextGBSpider
from locations.spiders.tesco_gb import set_located_in
from locations.storefinders.storemapper import StoremapperSpider


class PaperchaseGBSpider(StoremapperSpider):
    name = "paperchase_gb"
    item_attributes = {"brand": "Paperchase", "brand_wikidata": "Q7132739"}
    key = "17436-GF33k6oDwoiOfdUg"

    def parse_item(self, item, location, **kwargs):
        if item["addr_full"].startswith("Next"):
            set_located_in(NextGBSpider.item_attributes, item)

        yield item
