import re
from datetime import datetime

import pandas as pd

from request_utils import make_request_with_retries


# Abstract GameDataFrameBuilder
class GameDataFrameBuilder:
    def __init__(self) -> None:
        self.df = pd.DataFrame()
        self.today_date = datetime.now()

    async def fetch_game_data(self, game_name):
        raise NotImplementedError

    def build(self):
        self.df['date_insertion'] = self.today_date.strftime("%Y-%m-%d")
        self.df = self.df[
            ['product_name', 'price', 'platform', 'edition', 'region',
             'merchant_name', 'merchant_review_score_upon_5', 'merchant_review_count',
             'voucher_percentage', 'voucher_code',
             'price_with_voucher', 'price_before_voucher', 'price_with_paypal_fees', 'price_with_cb_fees',
             'paypal_fee', 'card_fee', 'price_currency', 'url', 'date_insertion']]
        return self.df

    def __repr__(self) -> str:
        return self.df.to_string()


class AllKeyShopGameDataFrameBuilder(GameDataFrameBuilder):
    async def fetch_game_data(self, game_name):
        _input_url = game_name.replace(" ", "+").lower()
        search_url = f"https://www.allkeyshop.com/blog/products/?search_name={_input_url}&pagenum=1"
        response_first_result = await make_request_with_retries(search_url)
        data = response_first_result.find_all("div", {
            "class": "grid grid-rows-[auto_1fr_auto] gap-1 hover:shadow-lg relative rounded-[5px] group hover:bg-[#242A3A] bg-[#202533]"})
        product_name = str(data.first.find("a").attrib["aria-label"])
        url_first_game = str(data.first.find("a").attrib["href"])
        response = await make_request_with_retries(url_first_game)
        if response.status == 200:
            self._process_game_data(response, product_name)

    def _process_game_data(self, response, product_name):
        data = response.find("div", {"class": "offers-table x-offers"}).find_all("div",
                                                                                 {"class": "offers-table-row x-offer"})
        for item in data:
            row = self._extract_row_data(item, product_name)
            self.df = pd.concat([self.df, pd.DataFrame(row)])

    def _extract_row_data(self, item, product_name):
        merchant = item.find("div", {
            "class": "offers-table-row-cell offers-table-row-cell-first offers-table-row-cell-merchant"})
        region = item.find("div", {
            "class": "x-offer-region offers-table-row-cell text-center x-popover d-none d-md-table-cell offers-table-row-cell-region"})
        edition = item.find("div", {
            "class": "x-offer-edition offers-table-row-cell text-center d-none d-md-table-cell offers-table-row-cell-edition"})
        old_price = item.find("div", {
            "class": "offers-table-row-cell text-right d-none d-md-table-cell offers-table-row-cell-old-price"})
        voucher = item.find("div", {"class": "offers-table-row-cell text-center offers-table-row-cell-coupon"})
        price = item.find("div", {"class": "offers-table-row-cell buy-btn-cell"})

        merchant_name = merchant.find("span", {"class": "x-offer-merchant-name offers-merchant-name"}).text
        merchant_review_score_upon_5 = merchant.find("span", {"class": "x-offer-merchant-review-score"}).text
        merchant_review_count = merchant.find("span", {"class": "x-offer-merchant-review-count"}).text

        region_type = region.find("div", {
            "class": "x-offer-region-name offers-edition-region text-truncate text-capitalize"}).text
        platform = region.find("div", {"class": "offers-edition-logo"}).find("span").attrib["class"]
        platform_name = re.search(r'(?<=sprite-30-)([a-zA-Z]+(?:-[a-zA-Z]+)*)', platform).group().replace("-",
                                                                                                          " ").capitalize()

        edition_type = edition.find("a", {"class": "x-offer-edition-name d-inline-block"}).text

        prices = self._extract_prices(old_price)
        paypal_fee = self._extract_text(old_price, "div", {"class": "fees-value x-offer-fee-paypal"})
        card_fee = self._extract_text(old_price, "div", {"class": "fees-value x-offer-fee-card"})
        voucher_percentage, voucher_code = self._extract_voucher(voucher)

        url = price.find('a').attrib["href"]
        price_value = float(
            price.find("span", {"class": "x-offer-buy-btn-in-stock"}).text.replace("€", "").replace(",", "."))
        price_currency = "EUR"

        return {
            'product_name': [product_name],
            'merchant_name': [merchant_name],
            'merchant_review_score_upon_5': [merchant_review_score_upon_5],
            'merchant_review_count': [merchant_review_count],
            'region': [region_type],
            'platform': [platform_name],
            'edition': [edition_type],
            'price_with_voucher': [prices['price_with_voucher']],
            'price_with_paypal_fees': [prices['price_with_paypal_fees']],
            'price_with_cb_fees': [prices['price_with_cb_fees']],
            'price_before_voucher': [prices['price_before_voucher']],
            'paypal_fee': [paypal_fee],
            'card_fee': [card_fee],
            'voucher_percentage': [voucher_percentage],
            'voucher_code': [voucher_code],
            'url': [url],
            'price': [price_value],
            'price_currency': [price_currency]
        }

    @staticmethod
    def _extract_prices(old_price):
        try:
            prices = old_price.find("span", {
                "class": "x-offer-is-not-cashback x-offers-price-info price-without-coupon"}).attrib[
                "data-bs-original-title"]
            prices = prices.replace("\n                    ", "").replace("~", "").replace("<p>", "").replace(
                '<span class="price">', "").replace("</span></p>", " | ").strip()
            return {
                'price_with_voucher': re.search(r'(?<=Price with voucher: )\d+.\d+', prices).group() if re.search(
                    r'(?<=Price with voucher: )\d+.\d+', prices) else "",
                'price_with_paypal_fees': re.search(r'(?<=Price with Paypal Fees: )\d+.\d+',
                                                    prices).group() if re.search(
                    r'(?<=Price with Paypal Fees: )\d+.\d+', prices) else "",
                'price_with_cb_fees': re.search(r'(?<=Price with Card Fees: )\d+.\d+', prices).group() if re.search(
                    r'(?<=Price with Card Fees: )\d+.\d+', prices) else "",
                'price_before_voucher': re.search(r'(?<=Price before voucher: )\d+.\d+', prices).group() if re.search(
                    r'(?<=Price before voucher: )\d+.\d+', prices) else ""
            }
        except AttributeError:
            return {
                'price_with_voucher': "",
                'price_with_paypal_fees': "",
                'price_with_cb_fees': "",
                'price_before_voucher': ""
            }

    @staticmethod
    def _extract_text(element, tag, attrs):
        try:
            return element.find(tag, attrs).text
        except AttributeError:
            return ""

    @staticmethod
    def _extract_voucher(voucher):
        try:
            voucher_percentage = voucher.find("span", {
                "class": "x-offer-coupon-value coupon-value text-truncate text-center"}).text
            voucher_code = voucher.find("span", {"class": "x-offer-coupon-code coupon-code text-truncate"}).text
            return voucher_percentage, voucher_code
        except AttributeError:
            return "", ""


class Top50GameDataFrameBuilder(GameDataFrameBuilder):
    async def fetch_game_data(self, game_name=None):
        url = "https://www.goclecd.fr"
        response = await make_request_with_retries(url)
        int_ranking = 1
        if response.status == 200:
            data = response.find("div", {"class": "content-box topclick"}).find_all("a")
            for item in data:
                url = item.attrib["href"]
                name = item.find("div", {"class": "topclick-list-element-game-title"}).text
                merchant = item.find("div", {"class": "topclick-list-element-game-merchant"}).text
                price = item.find("span", {"class": "topclick-list-element-priceWrapper-price"}).text
                self.df = pd.concat([self.df, pd.DataFrame({
                    'name': [name],
                    'price': [price],
                    'merchant': [merchant],
                    'url': [url],
                    'ranking': [int_ranking]
                })])
                int_ranking += 1

    def build(self):
        self.df["currency"] = self.df['price'].apply(lambda x: re.search(r'[^\d.,]', x).group())
        self.df['price'] = self.df['price'].apply(lambda x: float(x.replace("€", "").replace(",", ".")))
        # self.df = self.df.sort_values(by='price', ascending=True)
        self.df['date_insertion'] = self.today_date.strftime("%Y-%m-%d")
        self.df = self.df[['ranking', 'name', 'price', 'currency', 'merchant', 'url', 'date_insertion']]
        return self.df


async def construct_game_data_frame(builder_cls, *args):
    builder = builder_cls()
    await builder.fetch_game_data(*args)
    return builder.build()
