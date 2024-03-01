from scrapy.spiders import XMLFeedSpider

from locations.items import Feature


class DrummondGolfAUSpider(XMLFeedSpider):
    name = "drummond_golf_au"
    item_attributes = {
        "brand": "Drummond Golf",
        "brand_wikidata": "Q124065894",
        "extras": {
            "shop": "golf",
        },
    }
    allowed_domains = ["www.drummondgolf.com.au"]
    start_urls = [
        "https://www.drummondgolf.com.au/storelocator/index/search/?lat=-33.870&lng=151.210&radius=20000&page_limit=10000"
    ]
    iterator = "xml"
    itertag = "marker"

    def parse_node(self, response, node):
        properties = {
            "ref": node.xpath("@storeid").get(),
            "name": node.xpath("@name").get(),
            "lat": node.xpath("@lat").get(),
            "lon": node.xpath("@lng").get(),
            "street_address": node.xpath("@address").get(),
            "city": node.xpath("@city").get(),
            "state": node.xpath("@region").get(),
            "postcode": node.xpath("@postcode").get(),
            "phone": node.xpath("@phone").get(),
            "email": node.xpath("@email").get(),
            "website": node.xpath("@view_url").get(),
            "image": node.xpath("@logo").get().replace(".au/pub/", ".au/"),
        }
        yield Feature(**properties)
