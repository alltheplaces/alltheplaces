from locations.storefinders.alltheplaces import AllThePlacesSpider


class TomtomSpider(AllThePlacesSpider):
    name = "tomtom"
    start_urls = ["https://download.tomtom.com/open/fcd/pois.json"]
    contacts = ["office-pois@groups.tomtom.com"]
