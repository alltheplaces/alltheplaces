from locations.storefinders.storemapper import StoremapperSpider


class BedsRusNZSpider(StoremapperSpider):
    name = "bedsrus_nz"
    item_attributes = {"brand": "BedsRus", "brand_wikidata": "Q111018938"}
    key = "16389"

    def parse_item(self, item, location):
        item["branch"] = item["name"].replace("BedsRus ", "")
        yield item
