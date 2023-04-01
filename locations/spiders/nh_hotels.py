from scrapy.spiders import SitemapSpider, Request
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class NHHotelsSpider(SitemapSpider):
    name = "nh_hotels"
    item_attributes = {"brand": "NH Hotel Group", "brand_wikidata": "Q1604631"}
    allowed_domains = ["nh-hotels.com"]
    sitemap_urls = ["https://www.nh-hotels.com/hotels-sitemap.xml"]
    user_agent = BROWSER_DEFAULT

    def parse(self, response):
        store_id = response.xpath(
            '//section/div/button[@class="btn btn-primary js-track-book-hp js-track-book-hpGA4"]/@data-id'
        ).get()
        url = "https://www.nh-hotels.com/rest/datalayer/hotelPage/" + store_id
        yield Request(url=url, callback=self.parse_site)

    def parse_site(self, response):
        data = response.json()
        item = Feature()
        item["ref"] = data["id"]
        item["name"] = data["name"]
        item["city"] = data["city"]
        item["country"] = data["country"]
        item["street_address"] = data["address"]["street"]
        item["postcode"] = data["address"]["postalCode"]
        item["addr_full"] = f"""{item["street_address"]}, {item["postcode"]} {item["city"]}, {item["country"]}"""
        item["lat"] = data["address"]["latitud"]
        item["lon"] = data["address"]["longitud"]
        item["email"] = data["contact"]["mail"]
        item["phone"] = data["contact"]["phone"]
        item["website"] = response.url

        yield item
