from locations.spiders.mazda_gr import MazdaGRSpider


class MazdaMESpider(MazdaGRSpider):
    name = "mazda_me"
    api_url = "https://www.mazda.co.me/api/2sxc/app/auto/query/DealerListByPortalAlias/Default"
    module_id = "2702"
    tab_id = "1258"
    country = "ME"
