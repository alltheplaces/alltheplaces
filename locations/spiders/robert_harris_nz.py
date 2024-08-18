import chompjs

from locations.json_blob_spider import JSONBlobSpider


class RobertHarrisNZSpider(JSONBlobSpider):
    name = "robert_harris_nz"
    item_attributes = {
        "brand_wikidata": "Q121652432",
        "brand": "Robert Harris",
    }
    allowed_domains = [
        "www.robertharris.co.nz",
    ]
    start_urls = ["https://www.robertharris.co.nz/find-a-local-cafe/"]

    def extract_json(self, response):
        return chompjs.parse_js_object(response.xpath('//script[contains(text(), "var branches = ")]/text()').get())

    def post_process_item(self, item, response, location):
        # {'id': 'Robert Harris Whakatane', 'url': 'https://www.robertharris.co.nz/cafe/robert-harris-whakatane/', 'name': 'Robert Harris Whakatane',
        # 'hours': 'Closed Now', 'latlng': {'lat': '-37.9525392', 'lng': '176.99331410000002'},
        # 'lat': '-37.9525392', 'lng': '176.99331410000002',
        # 'html': {'id': 541, 'stockistId': 'stockist-541', 'name': 'Robert Harris Whakatane', 'suburb': '', 'city': '', 'country': 'New Zealand',
        # 'phone': '07-308-8997', 'nodeId': 541, 'cleanAddress': '241 The Strand, Whakatane 3120, , ',
        # 'url': 'https://www.robertharris.co.nz/cafe/robert-harris-whakatane/', 'lat': '-37.9525392', 'lng': '176.99331410000002',
        # 'data': '<li class="stockist transition transition-in clearfix" data-lng="176.99331410000002" data-lat="-37.9525392" data-distance="0.00"
        # data-nodeid="541" data-url="https://www.robertharris.co.nz/cafe/robert-harris-whakatane/" id="stockist-541"><div class="stockist-inner"><div class="stockist-info"><h4 class="name stockist-name" data-name="Robert Harris Whakatane">Robert Harris Whakatane</h4></div><div class="stockist-location"><div data-address class="address"><p>241 The Strand, Whakatane 3120<br/><span class="locality"></span><span class="postal-code"></span><span class="country-name">New Zealand</span></p></div></div><div class="stockist-hours">Closed Now</div><div class="stockist-contact"><p>07-308-8997</p><div class="stockist-features"></div></div><div class="stockist-directions clearfix"><a href="https://www.robertharris.co.nz/cafe/robert-harris-whakatane/" class="btnimg seemore"><button class="btn-class">See More</button></a><a target="_blank" href="https://maps.google.com/maps?daddr=241 The Strand, Whakatane 3120, , " class="btnimg directions google_tag_tracking" data-eventname="Find_directions" data-eventlable="Robert Harris Whakatane"><span>Open location in <img src="/wp-content/plugins/custom-google-map/gmap.png" class="img-responsive" alt="Google Map" /></span></a></div><div class="stockist-products"></div></div></li>', 'hours': 'Closed Now', 'features': False}, 'nodeId': 541, 'features': [], 'stockistId': 'stockist-541'}
        item["phone"] = location["html"]["phone"]
        yield item
