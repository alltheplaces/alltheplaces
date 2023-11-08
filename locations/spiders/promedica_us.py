from scrapy.spiders import XMLFeedSpider

from locations.items import Feature


class ProMedicaUSSpider(XMLFeedSpider):
    name = "promedica_us"
    item_attributes = {"brand": "ProMedica", "brand_wikidata": "Q7246673"}
    allowed_domains = ["promedicaseniorcare.org"]
    start_urls = ["https://promedicaseniorcare.org/alllocations?formattedAddress=&boundsNorthEast=&boundsSouthWest="]
    iterator = "xml"
    itertag = "marker"

    def parse_node(self, response, node):
        properties = {
            "ref": node.xpath(".//@web").get(),
            "name": node.xpath(".//@name").get(),
            "lat": node.xpath(".//@lat").get(),
            "lon": node.xpath(".//@lng").get(),
            "street_address": ", ".join(
                filter(None, [node.xpath(".//@address").get(), node.xpath(".//@address2").get()])
            ),
            "city": node.xpath(".//@city").get(),
            "state": node.xpath(".//@state").get(),
            "postcode": node.xpath(".//@postal").get(),
            "phone": node.xpath(".//@phone").get(),
            "website": node.xpath(".//@web").get(),
            "image": "https://promedicaseniorcare.org" + node.xpath(".//@image").get(),
        }
        yield Feature(**properties)
