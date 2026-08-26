from locations.structured_data_spider import StructuredDataSpider


class RemaxDESpider(StructuredDataSpider):
    name = "remax_de"
    item_attributes = {
        "brand": "RE/MAX",
        "brand_wikidata": "Q965845",
    }
    start_urls = ["https://www.remax.de/en/real-estate-offices-agents"]
