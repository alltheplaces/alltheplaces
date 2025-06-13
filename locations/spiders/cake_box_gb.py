from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class CakeBoxGBSpider(AmastyStoreLocatorSpider):
    name = "cake_box_gb"
    item_attributes = {"brand": "Cake Box", "brand_wikidata": "Q110057905"}
    allowed_domains = ["www.cakebox.com"]

    # def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
    # data = response.xpath('//script[contains(text(), "jsonLocations")]/text()').get()
    # data = re.sub(r"^.*jsonLocations: ", "", data, flags=re.DOTALL)
    # data = re.sub(r",\s+imageLocations.*$", "", data, flags=re.DOTALL)
    # jsondata = json.loads(data)
    # for location in jsondata["items"]:
    #    item = Feature()
    #    item["ref"] = location["id"]
    #    item["lat"] = location["lat"]
    #    item["lon"] = location["lng"]
    #    sel = location["popup_html"]
    #    item["city"] = re.search(r"(?<=City: )[^<]+", sel).group(0)
    #    item["street_address"] = re.search(r"(?<=Address: )[^<]+", sel).group(0)
    #    item["postcode"] = re.search(r"(?<=Zip: )[^<]+", sel).group(0)
    #    yield item
