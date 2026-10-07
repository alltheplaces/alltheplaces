from scrapy.http import HtmlResponse

from locations.items import Feature
from locations.spiders.daiwa_cycle_jp import DaiwaCycleJPSpider

LIST_HTML = """
<section class="shop_list">
  <p>結果<b>2</b>店舗</p>
  <ul>
    <li data-lat="34.713535484852" data-lng="135.37140366195">
      <div class="shop_title"><h2>ダイワサイクル 西宮鳴尾店</h2></div>
      <dl>
        <dt>住所</dt><dd>〒663-8184 兵庫県西宮市鳴尾町2-24-17</dd>
        <dt>TEL</dt><dd>0798-31-2688</dd>
        <dt>営業時間</dt><dd>10:00~20:00</dd>
      </dl>
      <div class="btn_wrapper">
        <div class="btn01"><a href="/shop/nishinomiyanaruo">店舗情報を見る</a></div>
        <div class="btn01 btn01--gray"><a href="https://coubic.com/daiwa-cycle/1">来店予約をする</a></div>
      </div>
    </li>
    <li data-lat="" data-lng="">
      <div class="shop_title"><h2>ダイワサイクルSTYLE 新三郷店</h2></div>
      <dl><dt>TEL</dt><dd>048-950-1178（繋がらない場合は090-1910-3812までご連絡ください）</dd></dl>
      <div class="btn_wrapper"><div class="btn01"><a href="/shop/fujisawaekikitaguchi">店舗情報を見る</a></div></div>
    </li>
  </ul>
</section>
"""

STORE_HTML = """
<div class="shop_detail">
  <ul>
    <li><b>住所</b><p>〒663-8184<br>兵庫県西宮市鳴尾町2-24-17</p></li>
    <li><b>TEL</b><p>0798-31-2688</p></li>
    <li><b>FAX</b><p>0798-31-2689</p></li>
    <li><b>定休日</b><p>12/31 , 1/1</p></li>
    <li><b>営業時間</b><p>【平日】10:00~20:00<br />
【土曜日】10:00~21:00<br />
【日曜祝日】10:00~20:00</p></li>
  </ul>
</div>
"""


def make_response(url: str, body: str) -> HtmlResponse:
    return HtmlResponse(url=url, body=body, encoding="utf-8")


def test_parse_list():
    requests = list(
        DaiwaCycleJPSpider().parse(make_response("https://www.daiwa-cycle.co.jp/shop/default.aspx", LIST_HTML))
    )
    assert [request.url for request in requests] == [
        "https://www.daiwa-cycle.co.jp/shop/nishinomiyanaruo",
        "https://www.daiwa-cycle.co.jp/shop/fujisawaekikitaguchi",
    ]

    item = requests[0].cb_kwargs["item"]
    assert item["ref"] == "nishinomiyanaruo"
    assert item["name"] == "ダイワサイクル"
    assert item["branch"] == "西宮鳴尾店"
    assert item["lat"] == "34.713535484852"
    assert item["lon"] == "135.37140366195"
    assert item["phone"] == "0798-31-2688"

    assert "name:en" not in item["extras"]

    item = requests[1].cb_kwargs["item"]
    assert item["name"] == "ダイワサイクルSTYLE"
    assert item["branch"] == "新三郷店"
    assert item["extras"]["name:ja"] == "ダイワサイクルSTYLE"
    assert item["extras"]["name:en"] == "Daiwa Cycle STYLE"
    assert item["phone"] == "048-950-1178"
    assert item["lat"] is None
    assert item["lon"] is None


def test_parse_store():
    item = Feature(ref="nishinomiyanaruo", extras={})
    (item,) = DaiwaCycleJPSpider().parse_store(
        make_response("https://www.daiwa-cycle.co.jp/shop/nishinomiyanaruo", STORE_HTML), item
    )
    assert item["postcode"] == "663-8184"
    assert item["addr_full"] == "兵庫県西宮市鳴尾町2-24-17"
    assert item["phone"] == "0798-31-2688"
    assert item["extras"]["fax"] == "0798-31-2689"
    assert item["opening_hours"].as_opening_hours() == "Mo-Fr 10:00-20:00; Sa 10:00-21:00; Su 10:00-20:00"


def test_parse_name():
    parse_name = DaiwaCycleJPSpider.parse_name
    assert parse_name("ダイワサイクル 西宮鳴尾店") == ("ダイワサイクル", "西宮鳴尾店")
    assert parse_name("ダイワサイクル芦屋店") == ("ダイワサイクル", "芦屋店")
    assert parse_name("ダイワサイクルSTYLE 東神奈川店") == ("ダイワサイクルSTYLE", "東神奈川店")
    assert parse_name("ダイワサイクルPRO 川崎野川店") == ("ダイワサイクルPRO", "川崎野川店")


def test_parse_hours():
    def parse_hours(lines):
        return DaiwaCycleJPSpider.parse_hours(lines).as_opening_hours()

    assert parse_hours(["10:00～20:00"]) == "Mo-Su 10:00-20:00"
    assert parse_hours(["10：00～20：00"]) == "Mo-Su 10:00-20:00"
    assert parse_hours(["通常営業時間：10:00～20:00"]) == "Mo-Su 10:00-20:00"
    assert parse_hours(["平日・土日祝 10:00～20:00"]) == "Mo-Su 10:00-20:00"
    assert parse_hours(["【平日】10:00-20:00【土日祝】10:00-21:00"]) == "Mo-Fr 10:00-20:00; Sa-Su 10:00-21:00"
    assert parse_hours(["10：00～20：00 （平　日）", "10：00～21：00 （土日祝）"]) == (
        "Mo-Fr 10:00-20:00; Sa-Su 10:00-21:00"
    )
    assert parse_hours(["平日：10:00-20:00", "土曜：10:00-21:00", "日曜：10:00-20:00"]) == (
        "Mo-Fr 10:00-20:00; Sa 10:00-21:00; Su 10:00-20:00"
    )
    assert (
        DaiwaCycleJPSpider.parse_hours(
            ["時短営業（10月1日～11月31日）", "平日　10:30〜19:30", "土日祝　10:00〜20:00 通常営業"]
        )
        is None
    )
