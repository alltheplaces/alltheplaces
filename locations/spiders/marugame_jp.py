from locations.storefinders.yext import YextSpider


class MarugameJPSpider(YextSpider):
    name = "marugame_jp"
    api_key = "51c80e247bfe04d6c37bb95d074b26d1"
    api_version = "20220615"
    search_filter = "%7B%22$and%22%20:%20%5B%0A%20%20%20%20%20%20%20%20%20%20%7B%22c_%E5%BA%97%E8%88%97%E9%96%8B%E5%BA%97%E6%97%A5%22:%7B%22$ge%22:%222019-02-15%22%7D%7D,%0A%20%20%20%20%20%20%20%20%20%20%7B%22name%22%20:%7B%22$startsWith%22:%20%22%E4%B8%B8%E4%BA%80%22%20%7D%7D%0A%20%20%20%20%20%20%20%20%5D%7D"
    wanted_types = ["Restaurant"]
    requires_proxy = True
