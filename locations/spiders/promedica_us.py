from scrapy.spiders import XMLFeedSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class ProMedicaUSSpider(XMLFeedSpider):
    name = "promedica_us"
    item_attributes = {"brand": "ProMedica", "brand_wikidata": "Q7246673"}
    allowed_domains = ["www.promedicaseniorcare.org"]
    start_urls = [
        "https://www.promedicaseniorcare.org/alllocations?formattedAddress=&boundsNorthEast=&boundsSouthWest="
    ]
    iterator = "xml"
    itertag = "marker"

    def parse_node(self, response, node):
        item = Feature()
        item["ref"] = node.xpath(".//@web").get()
        item["name"] = node.xpath(".//@name").get()
        item["lat"] = node.xpath(".//@lat").get()
        item["lon"] = node.xpath(".//@lng").get()
        item["street_address"] = clean_address([node.xpath(".//@address").get(), node.xpath(".//@address2").get()])
        item["city"] = node.xpath(".//@city").get()
        item["state"] = node.xpath(".//@state").get()
        item["postcode"] = node.xpath(".//@postal").get()
        item["phone"] = node.xpath(".//@phone").get()
        item["website"] = node.xpath(".//@web").get()
        item["image"] = "https://promedicaseniorcare.org" + node.xpath(".//@image").get()
        if "Community" in item["name"]:
            apply_category({"amenity": "social_facility", "social_facility": "assisted_living"}, item)
        else:
            apply_category(Categories.NURSING_HOME, item)
        yield item
