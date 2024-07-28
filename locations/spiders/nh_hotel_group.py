from scrapy.spiders import Request, SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT

SUB_BRANDS = ["NH Collection", "nhow", "Tivoli", "Anantara", "Avani", "Elewana", "Oaks", "NH"]


class NhHotelGroupSpider(SitemapSpider):
    name = "nh_hotel_group"
    item_attributes = {"brand_wikidata": "Q1604631"}
    allowed_domains = ["nh-hotels.com"]
    sitemap_urls = ["https://www.nh-hotels.com/hotels-sitemap.xml"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        if store_id := response.xpath("//@data-id").get():
            url = "https://www.nh-hotels.com/rest/datalayer/hotelPage/" + store_id
            yield Request(url=url, callback=self.parse_site, cb_kwargs={"website": response.url, "store_id": store_id})

    def parse_site(self, response, website, store_id):
        data = response.json()
        item = Feature()
        item["ref"] = store_id
        item["name"] = data["name"]
        item["city"] = data["city"]
        item["country"] = data["country"]
        item["street_address"] = data["address"]["street"]
        item["postcode"] = data["address"]["postalCode"]
        item["lat"] = data["address"]["latitud"]
        item["lon"] = data["address"]["longitud"]
        item["email"] = data["contact"]["mail"]
        item["phone"] = data["contact"]["phone"]
        item["website"] = website
        item["brand"] = self.find_sub_brand(data)
        apply_category(Categories.HOTEL, item)

        yield item

    def find_sub_brand(self, data):
        name = data["name"]
        email = data["contact"]["mail"]
        for sub_brand in SUB_BRANDS:
            if (sub_brand in name) or (sub_brand.lower() in email) or ("".join(sub_brand.lower().split(" ")) in email):
                return "NH Hotels" if sub_brand == "NH" else sub_brand
        return "NH Hotel Group"
