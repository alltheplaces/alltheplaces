from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class EnglishHeritageGBSpider(JSONBlobSpider):
    name = "english_heritage_gb"
    item_attributes = {"brand": "English Heritage", "brand_wikidata": "Q936287"}
    start_urls = ["https://www.english-heritage.org.uk/api/PropertySearch/GetAll"]
    no_refs = True
    locations_key = "Results"
