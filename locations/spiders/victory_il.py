from locations.structured_data_spider import StructuredDataSpider


class VictoryILSpider(StructuredDataSpider):
    name = "victory_il"
    item_attributes = {"brand": "Victory", "brand_wikidata": "Q6564842"}
    start_urls = ["https://www.victory.co.il/branches/"]
    wanted_types = ["Place"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Generate a ref
        item["ref"] = item["street_address"] + item["phone"]

        yield item
