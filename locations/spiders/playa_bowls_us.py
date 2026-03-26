from scrapy import Spider
from scrapy.http import Response

from locations.items import Feature


class PlayaBowlsUSSpider(Spider):
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
        item["ref"] = response.meta["link"].split("/")[-1]
        item["website"] = response.meta["link"]

        address_text_list = texts = response.css(
            'div.elementor-widget-heading .elementor-heading-title::text'
        ).getall()
        address_text_list = [t.replace("\xa0", "").strip(", ") for t in address_text_list]
        item["branch"] = address_text_list[0]
        item["street_address"] = address_text_list[1]
        item["city"] = address_text_list[2]
        item["state"] = address_text_list[3]
        item["postcode"] = address_text_list[4]

        phone_link = response.css('a[href^="tel:"]::attr(href)').get()
        item["phone"] = phone_link.split(":")[1].replace("%20", " ")

        google_maps_link = response.css('a[href*="google.com/maps"]::attr(href)').get()
        lat = google_maps_link.split("?q=")[1].split(",")[0].replace("%20", "")
        lon = google_maps_link.split("?q=")[1].split(",")[1].replace("%20", "")
        lat, lon = float(lat), float(lon)
        item["geometry"] = {"type": "Point", "coordinates": [lon, lat]}

        yield item
