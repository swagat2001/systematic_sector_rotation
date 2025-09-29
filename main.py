import asyncio
import sys
from config import Config
from utils.logger import setup_logger
from data.data_collector import DataCollector
from strategy.sector_rotation import SectorRotationEngine
from strategy.stock_selection import StockSelectionEngine
from strategy.portfolio_manager import PortfolioManager
from execution.paper_trading import PaperTradingEngine

logger = setup_logger()

class SystematicSectorRotation:
    def __init__(self):
        self.data_collector = DataCollector()
        self.sector_rotation = SectorRotationEngine()
        self.stock_selection = StockSelectionEngine()
        self.portfolio_manager = PortfolioManager()
        self.paper_trader = PaperTradingEngine()

        self.last_rebalance_date = None
        self.current_positions = {}

    async def initialize(self):
        logger.info("Initializing data sources...")
        await self.data_collector.load_all_data()
        logger.info("Initialization complete.")

    async def run_monthly_rebalance(self):
        logger.info("Starting monthly rebalance...")
        sectors = await self.sector_rotation.rank_sectors()
        stocks = await self.stock_selection.select_stocks(sectors)
        weights = await self.portfolio_manager.get_weights(sectors, stocks)
        result = await self.paper_trader.rebalance_portfolio(weights)
        self.current_positions = weights
        logger.info(f"Rebalance complete. Portfolio Value: {await self.paper_trader.get_portfolio_value():.2f}")
        return result

async def main():
    system = SystematicSectorRotation()
    await system.initialize()
    await system.run_monthly_rebalance()

if __name__ == "__main__":
    asyncio.run(main())
