from locations.spiders.nevada_dot_us import NevadaDotUSSpider


class ArizonaDotUSSpider(NevadaDotUSSpider):
    name = "arizona_dot_us"
    item_attributes = {"operator": "Arizona DOT", "operator_wikidata": "Q807704"}
    start_urls = ["https://www.az511.com/map/mapIcons/Cameras"]
