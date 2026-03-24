from scrapy.http import Response

from locations.items import Feature
import scrapy

class PlayaBowlsUSSpider(scrapy.Spider):
    name = "playa_bowls_us"
    item_attributes = {"brand": "Playa Bowls", "brand_wikidata": "Q114618507"}
    start_urls = ["https://playabowls.com/locations"]

    def parse(self, response: Response):
        location_links = response.css("a::attr(href)").getall()
        location_links = [link for link in location_links if "/location/" in link]
        for link in location_links:
            yield response.follow(link, callback=self.parse_store, meta={"link": link})

    def parse_store(self, response):
        # parse_sd does not work on this site so it had to be done manually
        item = Feature()
        item["street_address"] = response.css('div[data-id="7eeffe5"] span::text').get()
        item["ref"] = response.meta["link"].split("/")[-1]
        item["website"] = response.meta["link"]
        item["city"] = response.css('div[data-id="bd633ea"] span::text').get().strip(",")
        item["state"] = response.css('div[data-id="fc3f0c2"] span::text').get()
        item["postcode"] = response.css('div[data-id="723fa8e"] span::text').get()

        phone_and_map_links = response.css('div[data-id="8640f65"] a::attr(href)').getall()
        item["phone"] = phone_and_map_links[0].split(":")[1].replace("%20", " ")
        # coordinates get extracted from a google maps link
        lat = phone_and_map_links[1].split("?q=")[1].split(",")[0].replace("%20", "")
        lon = phone_and_map_links[1].split("?q=")[1].split(",")[1].replace("%20", "")
        lat, lon = float(lat), float(lon)
        item["geometry"] = {"type": "Point", "coordinates": [lon, lat]}

        yield item
