import scrapy
from locations.items import GeojsonPointItem


class BeerMappingSpider(scrapy.Spider):
    name = "beermapping"
    allowed_domains = ["beermapping.com"]

    download_delay = 3

    start_urls = (
        "https://beermapping.com/includes/dataradius.php?lat=44.3793041&lng=-113.704071&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=45.7857292&lng=-102.1970288&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=45.4820557&lng=-91.11576209999998&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=41.1567039&lng=-81.62542830000001&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=43.1586356&lng=-71.9282781&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=36.84168&lng=-76.4794435&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=43.191086&lng=0.8197430000000168&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=34.0401106&lng=-89.34166700000003&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=32.625006&lng=-99.83481460000002&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=37.3437874&lng=-108.76009629999999&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=36.1100428&lng=-115.3667218&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=48.55136710000001&lng=-123.07810619999998&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=41.4566102&lng=-102.30058029999998&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=38.8453492&lng=-88.75902009999999&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=41.1650556&lng=-118.48639630000002&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=35.9822676&lng=-120.08963130000001&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=47.5190109&lng=-111.18572319999998&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=44.4219616&lng=-100.7097867&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=45.762049&lng=4.4993220000000065&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=39.0156654&lng=-91.7928402&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=29.7179915&lng=-90.62041649999998&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=26.2625297&lng=-97.654811&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=30.46777519999999&lng=-86.88224450000001&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=25.733888&lng=-80.46046430000001&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=35.2444614&lng=-79.8072611&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=41.8002861&lng=-77.07947050000001&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=47.52159&lng=1.9324329999999463&radius=1000",
        "https://beermapping.com/includes/dataradius.php?lat=40.782433&lng=-85.82814580000002&radius=1000",
    )

    def parse(self, response):
        try:
            results = response.json()
        except ValueError:
            return
        results = results["locations"]
        for data in results:
            properties = {
                "name": data["name"],
                "city": data["city"],
                "ref": data["id"],
                "lon": data["lng"],
                "lat": data["lat"],
                "addr_full": data["street"],
                "phone": data["phone"],
                "state": data["state"],
                "postcode": data["zip"],
                "website": data["url"],
            }

            yield GeojsonPointItem(**properties)
