import scrapy
from locations.items import GeojsonPointItem

class TimHortonsSpider(scrapy.Spider):
    name = "timhortons"
    allowed_domains = ["http://www.timhortons.com/"]

    start_urls = (
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=44.3793041&origlng=-113.704071&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=45.7857292&origlng=-102.1970288&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=45.4820557&origlng=-91.11576209999998&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=41.1567039&origlng=-81.62542830000001&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=43.1586356&origlng=-71.9282781&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=36.84168&origlng=-76.4794435&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=43.191086&origlng=0.8197430000000168&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=34.0401106&origlng=-89.34166700000003&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=32.625006&origlng=-99.83481460000002&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=37.3437874&origlng=-108.76009629999999&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=36.1100428&origlng=-115.3667218&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=48.55136710000001&origlng=-123.07810619999998&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=41.4566102&origlng=-102.30058029999998&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=38.8453492&origlng=-88.75902009999999&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=41.1650556&origlng=-118.48639630000002&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=35.9822676&origlng=-120.08963130000001&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=47.5190109&origlng=-111.18572319999998&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=44.4219616&origlng=-100.7097867&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=45.762049&origlng=4.4993220000000065&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=39.0156654&origlng=-91.7928402&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=29.7179915&origlng=-90.62041649999998&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=26.2625297&origlng=-97.654811&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=30.46777519999999&origlng=-86.88224450000001&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=25.733888&origlng=-80.46046430000001&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=35.2444614&origlng=-79.8072611&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=41.8002861&origlng=-77.07947050000001&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=47.52159&origlng=1.9324329999999463&units=km&rad=1000',
        'http://www.timhortons.com/ca/en/php/getRestaurants.php?origlat=40.782433&origlng=-85.82814580000002&units=km&rad=1000'
    )
    

    def parse(self, response):
        data = response.xpath('.//marker')
        for item in data:
            properties = {
                'name': item.xpath("@address1").extract()[0] if item.xpath("@address1").extract()[0] else "Tim Hortons",
                'city': item.xpath("@city").extract()[0],
                'ref': item.xpath("@storeid").extract()[0],
                'lon': item.xpath("@lng").extract()[0],
                'lat': item.xpath("@lat").extract()[0],
                'addr_full': item.xpath("@address2").extract()[0],
                'phone': item.xpath("@phone").extract()[0],
                'state': item.xpath("@province").extract()[0],
                'postcode': item.xpath("@postal").extract()[0],
                'opening_hours': '24/7'
            }

            yield GeojsonPointItem(**properties)

