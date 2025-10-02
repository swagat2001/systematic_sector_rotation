"""
Data Storage Module for Systematic Sector Rotation Strategy

This module handles:
1. Database schema design and creation
2. CRUD operations for stocks, sectors, prices, fundamentals
3. Data versioning and updates
4. Efficient querying methods
5. Data persistence and caching
"""

import pandas as pd
import numpy as np
import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Dict, List, Optional, Any
import json

from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

Base = declarative_base()


class Sector(Base):
    """Sector information table"""
    __tablename__ = 'sectors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    ticker = Column(String(50), unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    stocks = relationship("Stock", back_populates="sector")
    prices = relationship("SectorPrice", back_populates="sector")


class Stock(Base):
    """Stock information table"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200))
    sector_id = Column(Integer, ForeignKey('sectors.id'))
    industry = Column(String(100))
    market_cap = Column(Float)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    sector = relationship("Sector", back_populates="stocks")
    prices = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    fundamentals = relationship("Fundamental", back_populates="stock", cascade="all, delete-orphan")


class StockPrice(Base):
    """Stock OHLCV data table"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    adj_close = Column(Float)
    
    # Relationships
    stock = relationship("Stock", back_populates="prices")
    
    # Composite index for efficient queries
    __table_args__ = (Index('idx_stock_date', 'stock_id', 'date'),)


class SectorPrice(Base):
    """Sector index OHLCV data table"""
    __tablename__ = 'sector_prices'
    
    id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
    # Relationships
    sector = relationship("Sector", back_populates="prices")
    
    # Composite index
    __table_args__ = (Index('idx_sector_date', 'sector_id', 'date'),)


class Fundamental(Base):
    """Fundamental data table"""
    __tablename__ = 'fundamentals'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    
    # Quality metrics
    roe = Column(Float)
    roce = Column(Float)
    gross_margin = Column(Float)
    operating_margin = Column(Float)
    net_margin = Column(Float)
    
    # Growth metrics
    eps = Column(Float)
    revenue = Column(Float)
    revenue_growth = Column(Float)
    earnings_growth = Column(Float)
    eps_growth_3y = Column(Float)
    sales_growth_3y = Column(Float)
    
    # Valuation metrics
    pe_ratio = Column(Float)
    forward_pe = Column(Float)
    pb_ratio = Column(Float)
    ev_ebitda = Column(Float)
    price_to_sales = Column(Float)
    fcf_yield = Column(Float)
    
    # Balance sheet metrics
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    interest_coverage = Column(Float)
    total_debt = Column(Float)
    total_cash = Column(Float)
    working_capital = Column(Float)
    
    # Other
    beta = Column(Float)
    dividend_yield = Column(Float)
    
    # Relationships
    stock = relationship("Stock", back_populates="fundamentals")
    
    __table_args__ = (Index('idx_stock_fund_date', 'stock_id', 'date'),)


class DataStorage:
    """
    Handles all database operations for the strategy
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file (default: database/strategy.db)
        """
        if db_path is None:
            db_path = Config.DATABASE_DIR / "strategy.db"
        
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        logger.info(f"Database initialized: {db_path}")
    
    def close(self):
        """Close database connection"""
        self.session.close()
        logger.info("Database connection closed")
    
    # ==================== SECTOR OPERATIONS ====================
    
    def add_sector(self, name: str, ticker: str, description: str = None) -> int:
        """Add a new sector"""
        sector = Sector(name=name, ticker=ticker, description=description)
        self.session.add(sector)
        self.session.commit()
        logger.info(f"Added sector: {name}")
        return sector.id
    
    def get_sector_by_name(self, name: str) -> Optional[Sector]:
        """Get sector by name"""
        return self.session.query(Sector).filter_by(name=name).first()
    
    def get_all_sectors(self) -> List[Sector]:
        """Get all sectors"""
        return self.session.query(Sector).all()
    
    # ==================== STOCK OPERATIONS ====================
    
    def add_stock(self, symbol: str, name: str = None, sector_name: str = None,
                  industry: str = None, market_cap: float = None) -> int:
        """Add a new stock"""
        sector_id = None
        if sector_name:
            sector = self.get_sector_by_name(sector_name)
            if sector:
                sector_id = sector.id
        
        stock = Stock(
            symbol=symbol,
            name=name,
            sector_id=sector_id,
            industry=industry,
            market_cap=market_cap
        )
        self.session.add(stock)
        self.session.commit()
        logger.info(f"Added stock: {symbol}")
        return stock.id
    
    def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol"""
        return self.session.query(Stock).filter_by(symbol=symbol).first()
    
    def get_all_stocks(self, active_only: bool = True) -> List[Stock]:
        """Get all stocks"""
        query = self.session.query(Stock)
        if active_only:
            query = query.filter_by(is_active=1)
        return query.all()
    
    def get_stocks_by_sector(self, sector_name: str) -> List[Stock]:
        """Get all stocks in a sector"""
        sector = self.get_sector_by_name(sector_name)
        if not sector:
            return []
        return self.session.query(Stock).filter_by(sector_id=sector.id).all()
    
    # ==================== PRICE OPERATIONS ====================
    
    def save_stock_prices(self, symbol: str, df: pd.DataFrame) -> int:
        """Save stock price data from DataFrame"""
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            logger.warning(f"Stock {symbol} not found, creating entry")
            stock_id = self.add_stock(symbol)
            stock = self.get_stock_by_symbol(symbol)
        
        records = []
        for date, row in df.iterrows():
            price = StockPrice(
                stock_id=stock.id,
                date=date,
                open=row.get('Open'),
                high=row.get('High'),
                low=row.get('Low'),
                close=row.get('Close'),
                volume=row.get('Volume'),
                adj_close=row.get('Adj Close', row.get('Close'))
            )
            records.append(price)
        
        self.session.bulk_save_objects(records)
        self.session.commit()
        
        logger.info(f"Saved {len(records)} price records for {symbol}")
        return len(records)
    
    def get_stock_prices(self, symbol: str, start_date: datetime = None,
                        end_date: datetime = None) -> pd.DataFrame:
        """Get stock price data as DataFrame"""
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            logger.warning(f"Stock {symbol} not found")
            return pd.DataFrame()
        
        query = self.session.query(StockPrice).filter_by(stock_id=stock.id)
        
        if start_date:
            query = query.filter(StockPrice.date >= start_date)
        if end_date:
            query = query.filter(StockPrice.date <= end_date)
        
        query = query.order_by(StockPrice.date)
        
        prices = query.all()
        if not prices:
            return pd.DataFrame()
        
        data = {
            'Open': [p.open for p in prices],
            'High': [p.high for p in prices],
            'Low': [p.low for p in prices],
            'Close': [p.close for p in prices],
            'Volume': [p.volume for p in prices],
            'Adj Close': [p.adj_close for p in prices]
        }
        
        df = pd.DataFrame(data, index=[p.date for p in prices])
        return df
    
    def save_sector_prices(self, sector_name: str, df: pd.DataFrame) -> int:
        """Save sector index price data"""
        sector = self.get_sector_by_name(sector_name)
        if not sector:
            logger.warning(f"Sector {sector_name} not found")
            return 0
        
        records = []
        for date, row in df.iterrows():
            price = SectorPrice(
                sector_id=sector.id,
                date=date,
                open=row.get('Open'),
                high=row.get('High'),
                low=row.get('Low'),
                close=row.get('Close'),
                volume=row.get('Volume')
            )
            records.append(price)
        
        self.session.bulk_save_objects(records)
        self.session.commit()
        
        logger.info(f"Saved {len(records)} price records for sector {sector_name}")
        return len(records)
    
    def get_sector_prices(self, sector_name: str, start_date: datetime = None,
                         end_date: datetime = None) -> pd.DataFrame:
        """Get sector index price data as DataFrame"""
        sector = self.get_sector_by_name(sector_name)
        if not sector:
            return pd.DataFrame()
        
        query = self.session.query(SectorPrice).filter_by(sector_id=sector.id)
        
        if start_date:
            query = query.filter(SectorPrice.date >= start_date)
        if end_date:
            query = query.filter(SectorPrice.date <= end_date)
        
        query = query.order_by(SectorPrice.date)
        
        prices = query.all()
        if not prices:
            return pd.DataFrame()
        
        data = {
            'Open': [p.open for p in prices],
            'High': [p.high for p in prices],
            'Low': [p.low for p in prices],
            'Close': [p.close for p in prices],
            'Volume': [p.volume for p in prices]
        }
        
        df = pd.DataFrame(data, index=[p.date for p in prices])
        return df
    
    # ==================== FUNDAMENTAL OPERATIONS ====================
    
    def save_fundamental_data(self, symbol: str, fundamentals: Dict[str, Any],
                             date: datetime = None) -> int:
        """Save fundamental data for a stock"""
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            logger.warning(f"Stock {symbol} not found")
            return 0
        
        if date is None:
            date = datetime.now()
        
        fund = Fundamental(
            stock_id=stock.id,
            date=date,
            roe=fundamentals.get('roe'),
            roce=fundamentals.get('roce'),
            gross_margin=fundamentals.get('gross_margin'),
            operating_margin=fundamentals.get('operating_margin'),
            net_margin=fundamentals.get('net_margin'),
            eps=fundamentals.get('eps'),
            revenue=fundamentals.get('revenue'),
            revenue_growth=fundamentals.get('revenue_growth'),
            earnings_growth=fundamentals.get('earnings_growth'),
            eps_growth_3y=fundamentals.get('eps_growth_3y'),
            sales_growth_3y=fundamentals.get('sales_growth_3y'),
            pe_ratio=fundamentals.get('pe_ratio'),
            forward_pe=fundamentals.get('forward_pe'),
            pb_ratio=fundamentals.get('pb_ratio'),
            ev_ebitda=fundamentals.get('ev_ebitda'),
            price_to_sales=fundamentals.get('price_to_sales'),
            fcf_yield=fundamentals.get('fcf_yield'),
            debt_to_equity=fundamentals.get('debt_to_equity'),
            current_ratio=fundamentals.get('current_ratio'),
            quick_ratio=fundamentals.get('quick_ratio'),
            interest_coverage=fundamentals.get('interest_coverage'),
            total_debt=fundamentals.get('total_debt'),
            total_cash=fundamentals.get('total_cash'),
            working_capital=fundamentals.get('working_capital'),
            beta=fundamentals.get('beta'),
            dividend_yield=fundamentals.get('dividend_yield')
        )
        
        self.session.add(fund)
        self.session.commit()
        
        logger.info(f"Saved fundamental data for {symbol}")
        return fund.id
    
    def get_latest_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get most recent fundamental data for a stock"""
        stock = self.get_stock_by_symbol(symbol)
        if not stock:
            return None
        
        fund = self.session.query(Fundamental).filter_by(
            stock_id=stock.id
        ).order_by(Fundamental.date.desc()).first()
        
        if not fund:
            return None
        
        return {
            'date': fund.date,
            'roe': fund.roe,
            'roce': fund.roce,
            'gross_margin': fund.gross_margin,
            'operating_margin': fund.operating_margin,
            'net_margin': fund.net_margin,
            'eps': fund.eps,
            'revenue': fund.revenue,
            'revenue_growth': fund.revenue_growth,
            'earnings_growth': fund.earnings_growth,
            'eps_growth_3y': fund.eps_growth_3y,
            'sales_growth_3y': fund.sales_growth_3y,
            'pe_ratio': fund.pe_ratio,
            'forward_pe': fund.forward_pe,
            'pb_ratio': fund.pb_ratio,
            'ev_ebitda': fund.ev_ebitda,
            'price_to_sales': fund.price_to_sales,
            'fcf_yield': fund.fcf_yield,
            'debt_to_equity': fund.debt_to_equity,
            'current_ratio': fund.current_ratio,
            'quick_ratio': fund.quick_ratio,
            'interest_coverage': fund.interest_coverage,
            'total_debt': fund.total_debt,
            'total_cash': fund.total_cash,
            'working_capital': fund.working_capital,
            'beta': fund.beta,
            'dividend_yield': fund.dividend_yield
        }
    
    # ==================== BULK OPERATIONS ====================
    
    def bulk_load_sectors(self, sectors_dict: Dict[str, str]):
        """Load multiple sectors at once"""
        for name, ticker in sectors_dict.items():
            existing = self.get_sector_by_name(name)
            if not existing:
                self.add_sector(name, ticker)
        
        logger.info(f"Bulk loaded {len(sectors_dict)} sectors")
    
    def bulk_load_stocks(self, stocks_list: List[Dict[str, Any]]):
        """Load multiple stocks at once"""
        for stock_info in stocks_list:
            symbol = stock_info.get('symbol')
            if not symbol:
                continue
            
            existing = self.get_stock_by_symbol(symbol)
            if not existing:
                self.add_stock(
                    symbol=symbol,
                    name=stock_info.get('name'),
                    sector_name=stock_info.get('sector'),
                    industry=stock_info.get('industry'),
                    market_cap=stock_info.get('market_cap')
                )
        
        logger.info(f"Bulk loaded {len(stocks_list)} stocks")
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary statistics of database contents"""
        summary = {
            'sectors': self.session.query(Sector).count(),
            'stocks': self.session.query(Stock).filter_by(is_active=1).count(),
            'stock_price_records': self.session.query(StockPrice).count(),
            'sector_price_records': self.session.query(SectorPrice).count(),
            'fundamental_records': self.session.query(Fundamental).count()
        }
        
        latest_stock_price = self.session.query(StockPrice).order_by(
            StockPrice.date.desc()
        ).first()
        
        if latest_stock_price:
            summary['latest_price_date'] = latest_stock_price.date
        
        return summary
    
    def vacuum_database(self):
        """Optimize database by running VACUUM"""
        self.session.execute('VACUUM')
        self.session.commit()
        logger.info("Database vacuumed and optimized")


if __name__ == "__main__":
    # Test the storage
    storage = DataStorage()
    
    # Load sectors from config
    from config import NSESectors
    storage.bulk_load_sectors(NSESectors.SECTOR_TICKERS)
    
    # Get summary
    summary = storage.get_data_summary()
    print("\nDatabase Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    storage.close()
