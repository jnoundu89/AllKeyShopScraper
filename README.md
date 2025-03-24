# AllKeyShopScraper

This is a simple scraper for AllKeyShop website

## License

This project is licensed under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html).

- You are free to use, modify, and distribute the code, but **commercial use is prohibited without explicit permission
  **.
- Any significant modifications or derived works must credit the original author, **`Yassine EL IDRISSI`**, and must
  also be distributed under the same license.

# Prerequisites:

Install the required packages in the requirements.txt file:

```bash
pip install -r requirements.txt
```

Don't forget to run the following command to install the required dependencies:

```bash
scrapling install
```

# How to use:

There is 2 arguments that you have to pass to the script:

- `--top50` : To scrape the current top 50 keys sold on the website
- `--key` : To scrape the key of a specific game or software

```bash
  python main.py --top50
```

```bash
  python main.py --key
```

Output will be saved in a csv file in the root directory of the project.

