from locations.storefinders.traveliq_web_cameras import TravelIQWebCamerasSpider


class NewEngland511USSpider(TravelIQWebCamerasSpider):
    name = "new_england_511_us"
    allowed_domains = ["www.newengland511.org"]
    operators = {
        "Maine": ["Maine Department of Transportation", "Q4926312", "ME"],
        "NewHampshire": ["New Hampshire Department of Transportation", "Q5559073", "NH"],
        "Vermont": ["Vermont Agency of Transportation", "Q7921675", "VT"],
    }
