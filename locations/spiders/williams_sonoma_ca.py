from locations.spiders.williams_sonoma_us import WilliamsSonomaUSSpider


class WilliamsSonomaCASpider(WilliamsSonomaUSSpider):
    name = "williams_sonoma_ca"
    allowed_domains = ["www.williams-sonoma.ca"]
    start_urls = [
        "https://www.williams-sonoma.ca/search/stores.json?brands=WS,PB&lat=40.71304703&lng=-74.00723267&radius=100000&includeOutlets=false",
    ]
