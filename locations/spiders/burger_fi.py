import scrapy

from locations.items import Feature


class BurgerFISpider(scrapy.Spider):
    name = "burger_fi"
    item_attributes = {"brand": "Burger Fi", "brand_wikidata": "Q39045496"}
    allowed_domains = ["api.dineengine.io"]
    start_urls = ("https://api.dineengine.io/burgerfi/custom/dineengine/vendor/olo/restaurants?includePrivate=false",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for r in response.xpath("//restaurant"):
            if r.xpath("@slug").get() == "burgerfi-test-vendor":
                continue

            properties = {
                "ref": r.xpath("@id").extract_first(),
                "name": r.xpath("@name").extract_first(),
                "street_address": r.xpath("@streetaddress").extract_first(),
                "phone": r.xpath("@telephone").extract_first(),
                "city": r.xpath("@city").extract_first(),
                "state": r.xpath("@state").extract_first(),
                "postcode": r.xpath("@zip").extract_first(),
                "country": r.xpath("@country").extract_first(),
                "lat": r.xpath("@latitude").extract_first(),
                "lon": r.xpath("@longitude").extract_first(),
                "website": "https://order.burgerfi.com/locations/" + r.xpath("@slug").extract_first(),
            }

            yield Feature(**properties)
