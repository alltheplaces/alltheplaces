from locations.storefinders.sweetiq import SweetIQSpider


class PenningtonsCASpider(SweetIQSpider):
    name = "penningtons_ca"
    item_attributes = {
        "brand_wikidata": "Q16956527",
        "brand": "Penningtons",
    }
    allowed_domains = ["locations.penningtons.com", "sls-api-service.sweetiq-sls-production-east.sweetiq.com"]
    start_urls = [
        "https://locations.penningtons.com/en",
    ]
