from locations.spiders.technopolis_bg import TechnopolisBGSpider


class PraktikerBGSpider(TechnopolisBGSpider):
    name = "praktiker_bg"
    item_attributes = {"brand": "Praktiker", "brand_wikidata": "Q110399491"}
    allowed_domains = ["praktiker.bg"]
    start_urls = ["https://api.praktiker.bg/videoluxcommercewebservices/v2/praktiker/mapbox/customerpreferedstore"]
