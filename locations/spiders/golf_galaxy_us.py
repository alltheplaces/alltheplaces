from locations.storefinders.where2getit import Where2GetItSpider


class GolfGalaxyUSSpider(Where2GetItSpider):
    name = "golf_galaxy_us"
    item_attributes = {
        "brand_wikidata": "Q69364358",
        "brand": "Golf Galaxy",
    }
    api_endpoint = "https://storelocator.golfgalaxy.com/rest/getlist"
    api_key = "CE23B360-C828-11E4-B146-ED9AA38844B8"
