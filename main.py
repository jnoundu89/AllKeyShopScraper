import argparse
import asyncio
import os
from datetime import datetime

from game_data import construct_game_data_frame, Top50GameDataFrameBuilder, AllKeyShopGameDataFrameBuilder
from logging_utils import LoggerManager

# Initialize the logger
s_script_name = os.path.basename(os.path.dirname(__file__))
LoggerManager(log_level='INFO', process_name=s_script_name)

o_logger = LoggerManager.get_logger(__name__)  # Factory Method for getting the logger


async def main():
    parser = argparse.ArgumentParser(description="Scrape game data")
    parser.add_argument('--top50', action='store_true', help="Run the Top 50 scraper")
    parser.add_argument('--key', type=str, help="Game name for AllKeyShop scraper")
    args = parser.parse_args()

    if args.top50:
        df = await construct_game_data_frame(Top50GameDataFrameBuilder)
        df.to_csv(f"goclecd_top50_{datetime.now().strftime('%Y_%m_%d')}.csv", index=False)
    elif args.key:
        df = await construct_game_data_frame(AllKeyShopGameDataFrameBuilder, args.key)
        product_name = args.key.replace(" ", "_").replace("-", "_").lower()
        df.to_csv(f"goclecd_{product_name}_{datetime.now().strftime('%Y_%m_%d')}.csv", index=False)
    else:
        print("Please provide either --top50 or --key 'game name' argument")


if __name__ == '__main__':
    asyncio.run(main())
