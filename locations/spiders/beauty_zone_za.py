from locations.structured_data_spider import StructuredDataSpider


class BeautyZoneZASpider(StructuredDataSpider):
    name = "beauty_zone_za"
    item_attributes = {"brand": "Beauty Zone", "brand_wikidata": "Q118185921"}
    start_urls = ["https://beautyzone.co.za/stores"]
