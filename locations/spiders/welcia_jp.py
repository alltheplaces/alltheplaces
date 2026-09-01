"""welcia field reference.

The store detail page spot/detail?code={code} server-renders
``var spotDetailBean = { ... };`` see parse_detail_page for the object shape and
the code -> OSM tag mapping near the FLAG_* constants.

**Field dictionary (245 codes)**

The detail page's embedded JSON object data.
Each entry: code, label, type (flag/text/date), parameter (backend key dXXXXX),
and where defined metainfo_text (public-facing text when the flag is true).

legend for checkbox:
- x: entered
- -: skipped
- ?: undecided

   | code | label | type | parameter | metainfo_text (flag)
 - | 00001 | カテゴリ1 | text | d00026
 - | 00002 | カテゴリ2 | text | d00027
 - | 00003 | 住所 > 追加説明 | text | d00028
 - | 00004 | メイン電話番号 | text | d00029
 - | 00005 | Featured Message > 説明 | text | d00030
 - | 00006 | 説明 | text | d00031
 x | 00007 | 営業時間 | text | d00032
 - | 00008 | 営業時間 > 営業再開日 | date | d00033
 - | 00009 | 営業時間に関する追加テキスト | text | d00034
 x | 00010 | Alipay | flag | d00035
 x | 00011 | American Express | flag | d00036
 x | 00012 | Bank Pay | flag | d00037
 x | 00013 | Diners Club | flag | d00038
 x | 00014 | Discover | flag | d00039
 - | 00015 | ICカード | flag | d00040
 x | 00016 | ICOCA | flag | d00041
 x | 00017 | JCB | flag | d00042
 x | 00018 | J−Coin Pay | flag | d00043
 x | 00019 | Kitaca | flag | d00044
 x | 00021 | manaca | flag | d00046
 x | 00022 | MasterCard | flag | d00047
 x | 00023 | メルペイ | flag | d00048
 x | 00024 | PASMO | flag | d00049
 x | 00025 | PayPay | flag | d00050
 x | 00026 | QUICPay | flag | d00051
 x | 00027 | 楽天Edy | flag | d00052
 x | 00028 | 楽天Pay | flag | d00053
 x | 00029 | SUGOCA | flag | d00054
 x | 00030 | Suica | flag | d00055
 x | 00031 | TOICA | flag | d00056
 x | 00032 | China UnionPay | flag | d00057
 x | 00033 | Visa | flag | d00058
 x | 00034 | WAON | flag | d00059
 x | 00035 | WeChat Pay | flag | d00060
 x | 00036 | d払い | flag | d00061
 - | 00037 | ウェブサイトURL > URL | text | d00062
 - | 00038 | ウェブサイトURL > 表示URL | text | d00063
 - | 00039 | ウェブサイトURL > 表示URLを使用 | flag | d00064
 x | 00040 | Fax番号 | text | d00065
 - | 00041 | 事業ロゴ > URL | text | d00066
 - | 00042 | 写真ギャラリー > URL | text | d00067
 - | 00043 | Googleカバー写真 | text | d00068
 - | 00044 | Googleロゴ | text | d00069
 - | 00045 | Pages URL | text | d00070
 - | 00046 | shufoo_embed | text | d00071
 - | 00047 | shufoo_shopId | text | d00072
 - | 00048 | タイムライン_embed | text | d00073
 - | 00049 | ブランド | text | d00074
 - | 00050 | 5円コピー | flag | d00075 | 5円コピーあり
 - | 00051 | AED | flag | d00076 | AEDあり
 - | 00052 | WAONPOINT | flag | d00077 | WAONPOINT
 - | 00053 | アルカリイオン水 | flag | d00078 | アルカリイオン水あり
 x | 00054 | イオン銀行ATM | flag | d00079 | イオン銀行ATMあり
 x | 00055 | ウエルカフェ | flag | d00080 | ウエルカフェ
 x | 00056 | オストメイトトイレ | flag | d00081 | オストメイトトイレあり
 x | 00057 | お酒 | flag | d00082 | お酒取扱
 - | 00058 | コインランドリー | flag | d00083 | コインランドリー
 x | 00059 | その他 銀行ATM | flag | d00084 | その他 銀行ATMあり
 - | 00060 | マルチコピー | flag | d00085 | マルチコピーあり
 - | 00061 | マルチコピー（マイナンバー対応） | flag | d00086 | マルチコピー（マイナンバー対応）あり
 x | 00062 | 免税店 | flag | d00087 | 免税店
 - | 00063 | 公共料金支払 | flag | d00088 | 公共料金支払可能
 - | 00064 | 宅配便ロッカー | flag | d00089 | 宅配便ロッカーあり
 x | 00065 | 駐車場 | flag | d00090 | 駐車場あり
 - | 00066 | 24時間営業 | flag | d00091 | 24時間営業
 - | 00068 | 化粧品専門店 | flag | d00093 | 化粧品専門店
 - | 00070 | お薬受取りロッカー | flag | d00095 | お薬受取りロッカーあり
 - | 00071 | 有料抗原検査 | flag | d00096 | 有料抗原検査あり
 - | 00072 | 無菌調剤室 | flag | d00097 | 無菌調剤室あり
 - | 00073 | 第一類医薬品 | flag | d00098
 - | 00074 | 血液検査 | flag | d00099 | 血液検査あり
 - | 00075 | 調剤24時間営業 | flag | d00100 | 調剤24時間営業
 x | 00076 | 調剤受付 | flag | d00101 | 調剤受付
 x | 00077 | 調剤専門店 | flag | d00102 | 調剤専門
 x | 00078 | クレジットカード | flag | d00103 | クレジットカード利用可
 x | 00079 | 電子マネーwaon | flag | d00104 | 電子マネーwaon利用可
 x | 00080 | 楽天Edy | flag | d00105 | 楽天Edy利用可
 x | 00081 | 銀聯カード | flag | d00106 | 銀聯カード利用可
 x | 00082 | 交通系 | flag | d00107 | 交通系IC利用可
 x | 00083 | QUICPay | flag | d00108 | QUICPay利用可
 x | 00085 | ALIPay | flag | d00110 | ALIPay利用可
 x | 00086 | d払い | flag | d00111 | d払い利用可
 x | 00087 | WeChat Pay | flag | d00112 | WeChat Pay利用可
 x | 00088 | PayPay | flag | d00113 | PayPay利用可
 x | 00089 | auPAY | flag | d00114 | auPAY利用可
 x | 00090 | 楽天Pay | flag | d00115 | 楽天Pay利用可
 x | 00091 | りそなWallet | flag | d00116 | りそなWallet利用可
 x | 00092 | ゆうちょPay | flag | d00117 | ゆうちょPay利用可
 x | 00093 | メルペイ | flag | d00118 | メルペイ利用可
 x | 00094 | J-CoinPay | flag | d00119 | J-CoinPay利用可
 x | 00095 | FamiPay | flag | d00120 | FamiPay利用可
 x | 00096 | BankPay | flag | d00121 | BankPay利用可
 x | 00097 | SmartCode | flag | d00122 | SmartCode利用可
 - | 00098 | 対応サービス備考 | text | d00123
 - | 00099 | 店舗ページ Meta Description | text | d00124
 - | 00100 | 店舗ページ Meta Title | text | d00125
 - | 00101 | 店舗ページ生成 | flag | d00126
 - | 00102 | 店舗写真 | text | d00127
 - | 00103 | 店舗営業時間に関する追加テキスト1 | text | d00128
 - | 00104 | 店舗緊急お知らせ | text | d00129
 - | 00105 | 店舗説明 | text | d00130
 - | 00107 | 店舗開店日 | date | d00132
 - | 00108 | 調剤営業時間に関する追加テキスト1 | text | d00133
 - | 00109 | 調剤営業時間に関する追加テキスト(店舗カード) | text | d00134
 x | 00110 | 調剤薬局Fax番号 | text | d00135
 - | 00111 | 調剤薬局フラグ | flag | d00136
 x | 00112 | 調剤薬局営業時間 | text | d00137
   | 00113 | 調剤薬局営業時間 > 営業再開日 | date | d00138
 x | 00114 | 調剤薬局電話番号 | text | d00139
 - | 00115 | 調剤店舗リンク > エンティティID | text | d00140
 - | 00116 | 店舗営業時間に関する追加テキスト(申請分)1 | text | d00141
 - | 00117 | 店舗営業時間に関する追加テキスト(複数行) | text | d00142
 - | 00118 | 店舗営業時間に関する追加テキスト(複数行)2 | text | d00143
 - | 00119 | 調剤営業時間に関する追加テキスト(申請分)1 | text | d00144
 - | 00120 | 調剤営業時間に関する追加テキスト(複数行) | text | d00145
 - | 00121 | 調剤営業時間に関する追加テキスト(複数行)2 | text | d00146
 - | 00122 | 処方箋バナー > URL | text | d00147
 - | 00123 | 処方箋バナー > クリックスルー URL | text | d00148
 - | 00124 | おうちウエルシアバナー > URL | text | d00149
 - | 00125 | おうちウエルシアバナー > クリックスルー URL | text | d00150
 - | 00126 | Information Banner1 > URL | text | d00151
 - | 00127 | Information Banner1 > クリックスルー URL | text | d00152
 - | 00128 | Information Banner2 > URL | text | d00153
 - | 00129 | Information Banner2 > クリックスルー URL | text | d00154
 - | 00130 | Information Banner3 > URL | text | d00155
 - | 00131 | Information Banner3 > クリックスルー URL | text | d00156
 - | 00132 | Information Banner4 > URL | text | d00157
 - | 00133 | Information Banner4 > クリックスルー URL | text | d00158
 - | 00134 | Information Banner5 > URL | text | d00159
 - | 00135 | Information Banner5 > クリックスルー URL | text | d00160
 - | 00136 | WelciaIDバナー > URL | text | d00161
 - | 00137 | WelciaIDバナー > クリックスルー URL | text | d00162
 - | 00138 | DearOne様用ラベル1 | text | d00163
 - | 00139 | DearOne様用URL1 | text | d00164
 - | 00140 | Open Date | date | d00165
 - | 00143 | Shufoo URL | text | d00168
 - | 00145 | ブランド名 | text | d00170
 x | 00147 | 閉店 | flag | d00172
 - | 00154 | 店舗営業時間に関する追加テキスト(短期分)1 | text | d00179
 - | 00155 | 調剤営業時間に関する追加テキスト(短期分)1 | text | d00180
 - | 00156 | 調剤併設店 | flag | d156
 - | 00157 | 店舗営業時間に関する追加テキスト2 | text | d00181
 - | 00158 | 店舗営業時間に関する追加テキスト3 | text | d00182
 - | 00159 | 調剤営業時間に関する追加テキスト2 | text | d00183
 - | 00160 | 調剤営業時間に関する追加テキスト3 | text | d00184
 - | 00161 | 店舗営業時間に関する追加テキスト(申請分)2 | text | d00185
 - | 00162 | 店舗営業時間に関する追加テキスト(申請分)3 | text | d00186
 - | 00163 | 調剤営業時間に関する追加テキスト(申請分)2 | text | d00187
 - | 00164 | 調剤営業時間に関する追加テキスト(申請分)3 | text | d00188
 - | 00165 | 店舗営業時間に関する追加テキスト(短期分)2 | text | d00189
 - | 00166 | 店舗営業時間に関する追加テキスト(短期分)3 | text | d00190
 - | 00167 | 調剤営業時間に関する追加テキスト(短期分)2 | text | d00191
 - | 00168 | 調剤営業時間に関する追加テキスト(短期分)3 | text | d00192
 - | 00169 | #PagesPlusNew | flag | d00194
 - | 00170 | #GroupDS | flag | d00195
 - | 00171 | #GroupPH | flag | d00196
 - | 00172 | #WelciaDS | flag | d00197
 - | 00173 | #WelciaPH | flag | d00198
 - | 00174 | #WelciaGL | flag | d00199
 - | 00175 | #WelciaNA | flag | d00200
 - | 00177 | #ListingOnly | flag | d00202
 - | 00178 | #Closed | flag | d00203
 - | 00179 | @Label_YP_Welcia | flag | d00204
 - | 00180 | @Label_GL_Welcia | flag | d00205
 - | 00181 | @Label_YP_HACdrug | flag | d00206
 - | 00182 | @Label_GL_HACdrug | flag | d00207
 - | 00183 | @Label_YP_Kanamitsu | flag | d00208
 - | 00184 | @Label_GL_Kanamitsu | flag | d00209
 - | 00185 | @Label_YP_NARCIS | flag | d00210
 - | 00186 | @Label_GP_Plus | flag | d00211
 - | 00187 | @Label_GP_Shimizu | flag | d00212
 - | 00188 | @Label_GP_M-Sakurai | flag | d00213
 - | 00189 | @Label_GP_Masaya | flag | d00214
 - | 00190 | @Label_GP_C-Studio | flag | d00215
 - | 00191 | @Label_GP_Albion | flag | d00216
 - | 00192 | @Label_GP_Yodoya | flag | d00217
 - | 00193 | @Label_GP_Marue | flag | d00218
 - | 00194 | @Label_GP_Pupule | flag | d00219
 - | 00195 | @Label_GP_KoKuMiN | flag | d00220
 - | 00196 | @Label_GP_Fuku | flag | d00221
 - | 00197 | \\wcard-ng | flag | d00222
 - | 00198 | \\wcard-ok | flag | d00223
 - | 00199 | ISOリージョンコード | text | d00224
 - | 00202 | 電子処方箋 | flag | d00227
 - | 00203 | マイナ受付 | flag | d00229 | マイナ受付対応
 - | 00204 | ＠Label_YP_Laundry | flag | d00230
 - | 00205 | ＠Label_YP_Laundry | flag | d00230
 - | 00208 | 祝日営業時間表示 | flag | d00233
 - | 00209 | 祝日営業時間表示(調剤薬局) | flag | d00234
 - | 00210 | 栄養相談サービス | flag | d00235 | 栄養相談ができる店舗
 - | 00211 | 移動販売車（うえたん号） | flag | d00236
 - | 00213 | ペット専門店 | flag | d00238
 - | 00216 | #GroupGL | flag | d00241
 - | 00217 | @Label_GP_Welpark | flag | d00242
 - | 00220 | @Label_YP_Towoshiya | flag | d00243
 - | 00221 | @Label_GL_Towoshiya | flag | d00244
 - | 00222 | shufooアプリURL | text | d00245
 - | 00223 | shufooバナー画像URL（PC） | text | d00246
 - | 00224 | shufooバナー画像URL（SP） | text | d00247
 - | 00226 | @Label_GL_Yodoya | flag | d00249
 - | 00227 | GBP連携なし | flag | d00250
 x | 00228 | Uber Eats | flag | d00252
 - | 00229 | Uber Eats_URL | text | d00253
 x | 00230 | QUOカードPay | flag | d00254
 x | 00231 | AEON Pay | flag | d00255
 - | 00232 | 選定療養について | text | d00257
 - | 00233 | 明細書の発行について | text | d00258
 - | 00234 | 調剤基本料 | text | d00259
 - | 00235 | 調剤管理料・服薬管理指導料 | text | d00260
 - | 00236 | 保険外併用(療養の給付対象外) | text | d00261
 - | 00237 | かかりつけ薬剤師指導料及びかかりつけ薬剤師包括管理料 | flag | d00262
 - | 00238 | 地域支援体制加算 | text | d00263
 - | 00239 | 後発医薬品調剤体制加算 | text | d00264
 - | 00240 | 在宅薬学総合体制加算 | text | d00265
 - | 00241 | 連携強化加算 | flag | d00266
 - | 00242 | 特定薬剤管理指導加算２ | flag | d00267
 - | 00243 | 無菌製剤処理加算 | flag | d00268
 - | 00244 | 在宅中心静脈栄養法加算 | flag | d00269
 - | 00245 | 在宅患者医療用麻薬持続注射療法加算 | flag | d00270
 - | 00246 | 医療DX推進体制整備加算 | flag | d00271
 - | 00247 | 通常の事業の実施地域 | text | d00272
 - | 00248 | 薬剤師（常勤） | text | d00273
 - | 00249 | 薬剤師（非常勤） | text | d00274
 - | 00250 | 事務員（常勤） | text | d00275
 - | 00251 | 事務員（非常勤） | text | d00276
 - | 00252 | 指定（介護予防）居宅療養管理指導業者 運営規程 | text | d00277
 - | 00253 | マイナンバーカードについて | text | d00278
 - | 00254 | 【削除予定】NARCIS（ビジネス情報用） | flag | d00279
 x | 00255 | PiTaPa | flag | d00280
 - | 00256 | 在宅患者訪問薬剤管理指導料 | flag | d00281
 - | 00257 | GBP連携用コード | text | d00282
 - | 00259 | 開店日注記（店舗検索サイト表示用） | text | d00284
 ? | 00260 | 緊急避妊薬 | flag | d00285 | 緊急避妊薬取扱
 - | 00261 | 地域支援・医薬品供給対応体制加算 | text | d00286
 - | 00262 | バイオ後続品調剤体制加算 | flag | d00287
 - | 00263 | 電子的調剤情報連携体制整備加算 | flag | d00288
 - | 00264 | 服薬管理指導料の注１ | flag | d00289
 - | 00267 | ドラッグストア | flag | d00292
 - | 00268 | 薬局 | flag | d00293
 - | 00269 | 化粧品店 | flag | d00294
 - | 00270 | ペットショップ | flag | d00295
 - | 00271 | コインランドリー | flag | d00296
 - | 00272 | 連携対象(自動入力) | flag | d00297
 - | 00273 | 門前薬局等立地依存減算 | flag | d00298
 - | 00274 | 調剤ベースアップ評価料 | flag | d00299

**detailColumns sections**

The ``detailColumns`` array groups the above fields into display sections.

   | code | section name | contents
 - | 00001 | 基本情報 | text 00007 営業時間 (JSON string), 00040 Fax番号, 00041 事業ロゴ, 00005/00006 説明, 00037 ウェブサイトURL; flag 00039, 00208
 x | 00002 | 支払いオプション | payment flags 00010–00036
 - | 00003 | Google管理用 | text 00044 Googleロゴ, 00045 Pages URL
 - | 00004 | チラシ管理 | text 00046 shufoo_embed, 00047 shufoo_shopId, 00222–00224
 - | 00005 | 管理用 | flags 00267–00272 業態; text 00049 ブランド, 00145 ブランド名
 - | 00006 | 対応サービス_その他 | service flags 00050–00065, 00210, 00260
 - | 00007 | 対応サービス_店舗 | flags 00066 24時間営業, 00068 化粧品専門店
 - | 00008 | 対応サービス_調剤 | pharmacy flags 00070–00077, 00203
 x | 00009 | 対応サービス_電子マネー | e-money/payment flags 00078–00097, 00230, 00231
 x | 00010 | Meta情報 | text 00099, 00100
 x | 00011 | スポット状態 | flags 00101 店舗ページ生成, 00147 閉店
 x | 00012 | 店舗情報 | text 00105 店舗説明
 x | 00013 | 調剤薬局情報 | flag 00111 調剤薬局フラグ
 x | 00014 | 営業時間に関する追加テキスト | store opening-hours extra text
 - | 00015 | 祝日営業時間（店舗・調剤） | holiday hours
 x | 00016 | バナー | text 00136/00137 WelciaIDバナー
 x | 00017 | アプリ用 | text 00138/00139 DearOne
 x | 00018 | 業態 | (empty)
 x | 00019 | Yext | (empty)
 - | 00020 | 位置情報 | (empty)
 x | 00021 | AppleMap用 | (empty)
 x | 00022 | ラベル | brand/label flags 00169–00198, 00204/00205, 00217, 00220/00221, 00226
 x | 00023 | 配達サービス | (empty)
 x | 00024 | 調剤薬局情報（ウェブサイト記載事項） | pharmacy fee/staffing text 00232–00264
 x | 00025 | SNS | (empty)
 - | default | — | flags 00156 調剤併設店; text 00001 カテゴリ1, 00002 カテゴリ2, 00004 メイン電話番号, 00199 ISOリージョンコード

**Notes**
- some info is natural language (店舗説明 00105, 説明 00006, 対応サービス備考 00098) - not used by this spider.
- lastUpdate/today on the detail page are formatted YYYY/MM/DD HH:MM / YYYYMMDD (server local date), unlike the ISO timestamps in the list API.
"""

import json
from collections.abc import Iterable

from chompjs import parse_js_object

from locations.categories import Categories, Drink, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.geo import postal_regions
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

BRANDS = {
    "01": {
        "brand": "welcia",
        "brand_wikidata": "Q11288687",
        "name": "ウエルシア薬局",
        "branch_prefixes": ["ウエルシア", "薬局"],
        "ruby_prefixes": ["ウエルシア", "薬局"],
    },
    "02": {
        "brand": "ハックドラッグ",
        "brand_wikidata": "",
        "branch_prefixes": ["ハックドラッグ"],
        "ruby_prefixes": ["ハックドラッグ"],
    },
    "03": {
        "brand": "ダックス",
        "brand_wikidata": "",
        "branch_prefixes": ["薬局ダックス", "ダックス"],
        "ruby_prefixes": ["ダックス"],
    },
    "04": {
        "brand": "ハッピードラッグ",
        "brand_wikidata": "Q11368084",
        "branch_prefixes": ["ハッピー・ドラッグ", "ハッピー調剤薬局", "ハッピードラッグ"],
        "ruby_prefixes": ["ハッピードラッグ"],
    },
    "05": {
        "brand": "カラースタジオ",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["カラースタジオ"],
        "ruby_prefixes": ["カラースタジオ"],
    },
    "06": {
        "brand": "金光薬品",
        "brand_wikidata": "Q11646466",
        "branch_prefixes": ["金光薬品", "金光薬局"],
        "ruby_prefixes": ["カネミツヤッキョク"],
    },
    "07": {
        "brand": "マサヤ",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["マサヤ "],
    },
    "08": {
        "brand": "よどやドラッグ",
        "brand_wikidata": "Q11281187",
        "branch_prefixes": ["よどやドラッグ"],
    },
    "09": {
        "brand": "マルエドラッグ",
        "brand_wikidata": "Q11298666",
        "branch_prefixes": ["マルエドラッグ", "マルエ薬局"],
    },
    "10": {
        "brand": "アリエールLAUNDRY PRO",
        "brand_wikidata": "",
        "category": Categories.SHOP_COUNTRY_STORE,
        "branch_prefixes": ["アリエールLAUNDRY PRO "],
        "ruby_prefixes": ["アリエールランドリープロ"],
    },
    "11": {
        "brand": "ププレひまわり",
        "brand_wikidata": "Q119871972",
        "branch_prefixes": [
            "スーパードラッグひまわり",
            "フード＆ドラッグひまわり",
            "ププレひまわり薬局",
            "ププレひまわり",
        ],
    },
    "12": {
        "brand": "NARCIS",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["NARCIS"],
        "ruby_prefixes": ["ナルシス"],
    },
    "13": {
        "brand": "コクミン",
        "brand_wikidata": "Q11301923",
        "branch_prefixes": [
            "KoKuMiN",
            "コクミンドラッグ",
            "コクミン薬局",
            "コクミン",
            "FamilyMart+コクミンドラッグ",
            "AIRPORT＋DRUG",
            "AIRPORT+DRUG ",
            "CityDrug ",
            "KeiyoDrug ",
        ],
    },
    "14": {
        "brand": "アルビオンドレッサー",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["アルビオンドレッサー"],
    },
    "15": {
        "brand": "アトリエアルビオン",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["アトリエアルビオン"],
    },
    "16": {
        "brand": "ふく薬品",
        "brand_wikidata": "Q119380891",
        "branch_prefixes": ["ふく薬品", "ふく薬局"],
        "strip": True,
    },
    "18": {
        "brand": "Zoomore",
        "brand_wikidata": "",
        "category": Categories.SHOP_PET,
        "branch_prefixes": ["Zoomore"],
        "ruby_prefixes": ["ズーモア"],
    },
    "19": {
        "brand": "コスメテリア",
        "brand_wikidata": "",
        "category": Categories.SHOP_COSMETICS,
        "branch_prefixes": ["コスメテリア"],
    },
    "20": {
        "brand": "とをしや薬局",
        "brand_wikidata": "Q11273556",
        "branch_prefixes": ["とをしや"],
        "removesuffix": "とをしや薬局",
    },
    "21": {
        "brand": "ウェルパーク",
        "brand_wikidata": "Q11288610",
        "branch_prefixes": ["ウェルパーク", "薬局"],
        "ruby_prefixes": ["ウェルパーク", "薬局"],
    },
}

# flag code -> OSM payment tag
PAYMENT_METHODS = {
    "00010": PaymentMethods.ALIPAY,
    "00011": PaymentMethods.AMERICAN_EXPRESS,
    "00012": "payment:bank_pay",
    "00013": PaymentMethods.DINERS_CLUB,
    "00014": PaymentMethods.DISCOVER_CARD,
    "00016": "payment:icoca",
    "00017": PaymentMethods.JCB,
    "00018": "payment:j_coin_pay",
    "00019": "payment:kitaca",
    "00021": "payment:manaca",
    "00022": PaymentMethods.MASTER_CARD,
    "00023": PaymentMethods.MERPAY,
    "00024": "payment:pasmo",
    "00025": PaymentMethods.PAYPAY,
    "00026": PaymentMethods.QUICPAY,
    "00027": PaymentMethods.EDY,
    "00028": PaymentMethods.RAKUTEN_PAY,
    "00029": "payment:sugoca",
    "00030": "payment:suica",
    "00031": "payment:toica",
    "00032": PaymentMethods.UNIONPAY,
    "00033": PaymentMethods.VISA,
    "00034": PaymentMethods.WAON,
    "00035": PaymentMethods.WECHAT,
    "00036": PaymentMethods.D_BARAI,
    "00078": PaymentMethods.CREDIT_CARDS,
    "00079": PaymentMethods.WAON,
    "00080": PaymentMethods.EDY,
    "00081": PaymentMethods.UNIONPAY,
    "00082": "payment:icsf",
    "00083": PaymentMethods.QUICPAY,
    "00085": PaymentMethods.ALIPAY,
    "00086": PaymentMethods.D_BARAI,
    "00087": PaymentMethods.WECHAT,
    "00088": PaymentMethods.PAYPAY,
    "00089": "payment:au_pay",
    "00090": PaymentMethods.RAKUTEN_PAY,
    "00091": "payment:resona_wallet",
    "00092": "payment:yucho_pay",
    "00093": PaymentMethods.MERPAY,
    "00094": "payment:j_coin_pay",
    "00095": "payment:fami_pay",
    "00096": "payment:bank_pay",
    "00097": "payment:smart_code",
    "00230": "payment:quo_pay",
    "00231": "payment:aeon_pay",
    "00255": "payment:pitapa",
}

# service-flag / detail-field code -> OSM tag (partial; payment flags are in PAYMENT_METHODS above)
FLAG_CLOSED = "00147"  # 閉店 -> remove from dataset when true
FLAG_FAX = "00040"  # Fax番号 -> fax
FLAG_ATM_AEON = "00054"  # イオン銀行ATM
FLAG_COFFEE = "00055"  # ウエルカフェ
FLAG_ATM_OTHERS = "00059"  # その他 銀行ATM
FLAG_TOILETS_OSTOMY = "00056"  # オストメイトトイレ -> toilets:ostomy
FLAG_ALCOHOL = "00057"  # お酒 -> alcohol
FLAG_DUTY_FREE = "00062"  # 免税 -> duty_free
FLAG_PARKING = "00065"  # 駐車場 -> parking
FLAG_DISPENSING = "00076"  # 調剤受付 -> dispensing=yes
FLAG_DEDICATED_PHARMACY = "00077"  # 調剤専門店 -> amenity=pharmacy (when true)
FLAG_PHARMACY_PHONE = "00114"  # 調剤薬局電話番号 -> phone:pharmacy
FLAG_PHARMACY_FAX = "00110"  # 調剤薬局Fax番号 -> fax:pharmacy
FLAG_UBER_EATS = (
    "00228"  # Uber Eats デリバリー -> delivery=yes, delivery:partner=Uber Eats, delivery:partner:wikidata=Q21462723
)
FLAG_STORE_HOURS = "00007"  # 営業時間 -> opening_hours
FLAG_PHARMACY_HOURS = "00112"  # 調剤薬局営業時間 -> opening_hours:pharmacy


class WelciaJPSpider(LocationCloudSpider):
    name = "welcia_jp"
    api_endpoint = "https://store.welcia.co.jp/welcia/api/proxy2/shop/list"
    website_formatter = "https://store.welcia.co.jp/welcia/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        if phone := source_feature.get("phone"):
            item["phone"] = f"+81 {phone}"

        if postal_code := source_feature.get("postal_code"):
            self._apply_postal_address(item, postal_code)

        brand = BRANDS.get(source_feature["categories"][0]["code"])
        if brand is None:
            return

        if brand_name := brand.get("brand"):
            item["brand"] = brand_name
            if brand.get("name"):
                item["name"] = brand["name"]
            else:
                item["name"] = brand_name
        if "brand_wikidata" in brand:
            item["brand_wikidata"] = brand["brand_wikidata"]
        if category := brand.get("category"):
            apply_category(category, item)
        else:
            apply_category(Categories.SHOP_CHEMIST, item)

        self._apply_branch_and_ruby(item, source_feature, brand)

        if branch := item.get("branch"):
            item["branch"] = branch.removesuffix(" (調剤薬局)").removesuffix("(調剤薬局)").strip()

        yield item

    def _apply_postal_address(self, item: Feature, postal_code: str) -> None:
        if region := POSTAL_LOOKUP.get(postal_code):
            item["extras"]["addr:province"] = region["province:ja"]
            item["city"] = region["city:ja"]
            if quarter := region.get("quarter:ja"):
                item["extras"]["addr:quarter"] = quarter
            elif neighbourhood := region.get("neighbourhood:ja"):
                item["extras"]["addr:neighbourhood"] = neighbourhood

    def _apply_branch_and_ruby(self, item: Feature, source_feature: dict, brand: dict) -> None:
        if name := source_feature.get("name"):
            item["branch"] = name
            for prefix in brand.get("branch_prefixes", []):
                item["branch"] = item["branch"].removeprefix(prefix)
            if brand.get("strip"):
                item["branch"] = item["branch"].strip()
            if suffix := brand.get("removesuffix"):
                item["branch"] = item["branch"].removesuffix(suffix)
        if ruby := source_feature.get("ruby"):
            item["extras"]["branch:ja-Hira"] = ruby
            for prefix in brand.get("ruby_prefixes", []):
                item["extras"]["branch:ja-Hira"] = item["extras"]["branch:ja-Hira"].removeprefix(prefix)

    def parse_detail_page(self, response, item, source_feature):
        """Parse the detail page, extracting the embedded ``spotDetailBean`` object.

        ``spotDetailBean`` is a JS object server-rendered on the detail page
        containing all detail information. Top-level keys:

        - code | str | store code (== ref)
        - name | str | e.g. ウエルシア春日部一ノ割店
        - ruby | str | kana reading
        - phone | str | e.g. 048-735-4739
        - addressName | str | full address
        - postalCode / postalDisplayCode | str | e.g. 3440031 / 344-0031
        - prefectureCode | str | e.g. 11 (Saitama)
        - lat, lon | str | WGS84 (detail page; differs slightly from list API)
        - categoryCode, categoryImageName | str | brand code/alias, e.g. 01/ウエルシア
        - external_code | str | == code
        - lastUpdate, today | str | YYYY/MM/DD HH:MM / YYYYMMDD
        - detailAddress | obj | {code,name,coord,address,types,old}
        - flags | obj | map code -> {code,label,value,description?,description_link?,image_path?};
          only flags present for the store
        - detailColumns | array | sections, each {code, name, columns?} where
          columns = {flag:[...], text:[...]}

        flags object shape::
            "00065": {"code": "00065", "description": "", "description_link": "",
                      "label": "駐車場", "value": "true"}

        ``value`` is the string "true" / "false". Some entries add image_path
        or metainfo_text.
        """
        blob = response.xpath('//script[contains(text(), "var spotDetailBean")]/text()').get()
        if not blob:
            yield item
            return
        detail_json = parse_js_object(blob.split("var spotDetailBean = ", 1)[1])
        detail_fields = self.detail_fields(detail_json)

        if flag := detail_json["flags"].get(FLAG_CLOSED):
            if flag.get("value") == "true":
                return

        self._apply_payment_methods(item, detail_json)

        if fax := detail_fields.get(FLAG_FAX):
            if value := fax.get("value"):
                item["extras"]["fax"] = f"+81 {value}"

        if flag := detail_json["flags"].get(FLAG_ATM_AEON) or detail_json["flags"].get(FLAG_ATM_OTHERS):
            apply_yes_no(Extras.ATM, item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_COFFEE):
            apply_yes_no(Drink.COFFEE, item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_TOILETS_OSTOMY):
            apply_yes_no("toilets:ostomy", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_ALCOHOL):
            apply_yes_no("sells:alcohol", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_DUTY_FREE):
            apply_yes_no("duty_free", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_PARKING):
            apply_yes_no("parking", item, flag.get("value") == "true", apply_positive_only=False)

        self._apply_dispensing(item, detail_json, detail_fields)
        self._apply_other_services(item, detail_json)
        self._apply_opening_hours(item, detail_fields)

        yield item

    def _apply_dispensing(self, item: Feature, detail_json: dict, detail_fields: dict) -> None:
        if flag := detail_json["flags"].get(FLAG_DISPENSING):
            apply_yes_no("dispensing", item, flag.get("value") == "true", apply_positive_only=False)

        if flag := detail_json["flags"].get(FLAG_DEDICATED_PHARMACY):
            if flag.get("value") == "true":
                apply_category(Categories.PHARMACY, item)

        if pharmacy_phone := detail_fields.get(FLAG_PHARMACY_PHONE):
            if value := pharmacy_phone.get("value"):
                item["extras"]["phone:pharmacy"] = f"+81 {value}"

        if pharmacy_fax := detail_fields.get(FLAG_PHARMACY_FAX):
            if value := pharmacy_fax.get("value"):
                item["extras"]["fax:pharmacy"] = f"+81 {value}"

    def _apply_other_services(self, item: Feature, detail_json: dict) -> None:
        if flag := detail_json["flags"].get(FLAG_UBER_EATS):
            if flag.get("value") == "true":
                item["extras"]["delivery"] = "yes"
                item["extras"]["delivery:partner"] = "Uber Eats"
                item["extras"]["delivery:partner:wikidata"] = "Q21462723"

    def _apply_opening_hours(self, item: Feature, detail_fields: dict) -> None:
        for field_code, key in ((FLAG_STORE_HOURS, "opening_hours"), (FLAG_PHARMACY_HOURS, "opening_hours:pharmacy")):
            if entry := detail_fields.get(field_code):
                if value := entry.get("value"):
                    hours = self._parse_hours(value)
                    if hours:
                        if key == "opening_hours":
                            item["opening_hours"] = hours
                        else:
                            item["extras"][key] = hours

    def _parse_hours(self, value: str) -> str | None:
        """Parse the per-day opening hours JSON into an opening_hours value.

        The source is a JSON object keyed by lowercase day names (``sunday`` ..
        ``saturday``) plus ``holiday``. A value is a list of [open, close]
        ranges, the string ``"allday"`` (open 24h), or the string ``"closed"``
        (closed that day). Weekday ranges go through the OpeningHours helper.

        Example value::

            {"sunday":[["09:00","20:00"]], ..., "holiday":[]}

        - keys: sunday..saturday + holiday
        - values: list of [open, close] pairs, 24h "HH:MM"; empty list / empty
          holiday = closed
        - 調剤薬局営業時間 (00112) uses the same shape when the store has a pharmacy
        """
        try:
            day_hours = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(day_hours, dict):
            return None

        oh = OpeningHours()
        for day, ranges in day_hours.items():
            if day == "holiday":
                continue
            self._add_day_hours(oh, sanitise_day(day), ranges)

        result = oh.as_opening_hours()

        if holiday_ranges := day_hours.get("holiday"):
            result += self._holiday_suffix(holiday_ranges)

        return result or None

    @staticmethod
    def _add_day_hours(oh: OpeningHours, day_code: str | None, ranges) -> None:
        if ranges == "allday":
            oh.add_range(day_code, "00:00", "24:00")
        elif ranges == "closed":
            oh.set_closed(day_code)
        elif ranges:
            for open_time, close_time in ranges:
                oh.add_range(day_code, open_time, close_time)

    @staticmethod
    def _holiday_suffix(holiday_ranges) -> str:
        if holiday_ranges == "closed":
            return "; PH off"
        return "; PH " + ",".join(f"{open_time}-{close_time}" for open_time, close_time in holiday_ranges)

    @staticmethod
    def detail_fields(detail_json: dict) -> dict[str, dict]:
        """Flatten all detailColumns sections into a code -> entry lookup."""
        fields = {}
        for section in detail_json.get("detailColumns", []):
            for entries in section.get("columns", {}).values():
                for entry in entries:
                    if isinstance(entry, dict) and entry.get("code"):
                        fields[entry["code"]] = entry
        return fields

    def _apply_payment_methods(self, item: Feature, detail_json: dict) -> None:
        flags = detail_json["flags"]
        for code, payment in PAYMENT_METHODS.items():
            if flag := flags.get(code):
                apply_yes_no(payment, item, flag.get("value") == "true", apply_positive_only=False)


def _build_postal_lookup() -> dict[str, dict]:
    """Map each JP postcode to its region dict.

    Scans the 124K row JP postcode dataset only once at import time to avoid rescanning.
    """
    lookup = {}
    for region in postal_regions("JP"):
        lookup.setdefault(region["postal_region"], region)
    return lookup


POSTAL_LOOKUP = _build_postal_lookup()
