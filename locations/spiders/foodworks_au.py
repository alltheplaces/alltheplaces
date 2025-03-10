from html import unescape
from typing import Iterable
from urllib.parse import unquote, urlparse

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.geo import country_iseadgg_centroids
from locations.google_url import url_to_coords
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class FoodworksAUSpider(Spider):
    name = "foodworks_au"
    item_attributes = {"brand": "Foodworks", "brand_wikidata": "Q5465579"}
    allowed_domains = ["myfoodworks.com.au", "www.google.com"]
    follow_google_maps_urls = True
    download_delay = 2  # Crawl slower as chooser.myfoodworks.com.au can return HTTP 429
    custom_settings = {
        "ROBOTSTXT_OBEY": False
    }  # Disable robots.txt as it adds many unwanted requests for each feature's subdomain

    def start_requests(self) -> Iterable[Request]:
        url_template = "https://chooser.myfoodworks.com.au/shops/all?latitude={}&longitude={}"
        for coordinates in country_iseadgg_centroids(["AU"], 48):
            yield Request(url_template.format(coordinates[0], coordinates[1]), callback=self.parse_store_list)

    def parse_store_list(self, response: Response) -> Iterable[Request]:
        for store in response.xpath('//div[@class="StoreLink StoreLink--WithStoreAttributes"]'):
            properties = {
                "branch": store.xpath('./span[@class="StoreLink__Name"]/text()').get(),
                "addr_full": merge_address_lines(store.xpath('./span[@class="StoreLink__Details"]/text()').getall()),
            }
            if phone := store.xpath('.//a[contains(@href, "tel:")]/@href').get():
                properties["phone"] = phone.removeprefix("tel:")
            apply_category(Categories.SHOP_SUPERMARKET, properties)

            website_redirect_path = store.xpath(
                './/a[contains(@class, "StoreLink__CallToAction__Button--Primary")]/@href'
            ).get()
            yield response.follow(
                website_redirect_path, meta={"properties": properties}, callback=self.parse_store, dont_filter=True
            )

    def parse_store(self, response: Response) -> Iterable[Feature | Request]:
        if urlparse(response.url).path.strip("/"):
            # Sometimes the store list redirector points not to the store
            # official website but rather a sub-path which is a manager/store
            # employee portal. Re-do the request for the official website in
            # such instances.
            yield Request(
                url="https:{}".format(urlparse(response.url).hostname),
                meta={"properties": response.meta["properties"]},
                callback=self.parse_store,
            )
            return

        properties = response.meta["properties"]
        properties["ref"] = response.url
        properties["website"] = response.url
        if email := response.xpath(
            '//div[@class="Microsite-Component__Content"]/p/a[contains(@href, "mailto:")]/@href'
        ).get():
            properties["email"] = email.removeprefix("mailto:")
        hours_text = " ".join(response.xpath('//div[contains(@class, "TradingHours__Day")]//text()').getall())
        properties["opening_hours"] = OpeningHours()
        properties["opening_hours"].add_ranges_from_string(hours_text)

        if self.follow_google_maps_urls:
            if google_maps_url := response.xpath('//div[@class="Microsite__GoogleMap"]/iframe/@src').get():
                google_maps_places_id = unquote(unescape(google_maps_url)).split("place_id:", 1)[1].split("&", 1)[0]
                yield Request(
                    url=f"https://www.google.com/maps/place/?q=place_id:{google_maps_places_id}",
                    meta={"properties": properties, "handle_httpstatus_list": [429]},
                    callback=self.parse_coordinates,
                )
                return

        yield Feature(**properties)

    def parse_coordinates(self, response: Response) -> Iterable[Feature]:
        properties = response.meta["properties"]
        if response.status == 429:
            self.follow_google_maps_urls = False
            self.logger.error(
                "Google Maps rate limiting encountered when following redirect to obtain feature coordinates. Coordinates could not be extracted for feature."
            )
        if self.follow_google_maps_urls and "https://www.google.com/maps/preview/place/" in response.text:
            properties["lat"], properties["lon"] = url_to_coords(
                "https://www.google.com/maps/preview/place/"
                + response.text.split(r"\"https://www.google.com/maps/preview/place/", 1)[1].split(r"\"", 1)[0]
            )
        yield Feature(**properties)
