"""
Service Layer Trade Recording and Management

거래 기록 관리 서비스
백테스트 및 실제 거래 기록을 저장, 조회, 분석하는 기능 제공

버전: 1.0
작성일: 2025-09-21
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import json
import sqlite3
import pickle
from enum import Enum


class TradeType(Enum):
    """거래 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HALF_SELL = "HALF_SELL"
    WHIPSAW = "WHIPSAW"
    PYRAMID = "PYRAMID"


class TradeReason(Enum):
    """거래 사유"""
    SIGNAL = "SIGNAL"
    LOSSCUT = "LOSSCUT"
    PROFIT_TAKING = "PROFIT_TAKING"
    WHIPSAW_EXIT = "WHIPSAW_EXIT"
    REBALANCING = "REBALANCING"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"


@dataclass
class TradeRecord:
    """거래 기록"""
    trade_id: str
    strategy_name: str
    ticker: str
    trade_type: TradeType
    quantity: float
    price: float
    timestamp: pd.Timestamp
    reason: TradeReason
    pnl: float = 0.0
    commission: float = 0.0
    slippage: float = 0.0
    position_size: float = 0.0
    risk_level: float = 0.0
    duration: Optional[int] = None
    related_trade_id: Optional[str] = None  # 매수/매도 쌍 연결
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PortfolioSnapshot:
    """포트폴리오 스냅샷"""
    timestamp: pd.Timestamp
    strategy_name: str
    cash: float
    positions: Dict[str, Dict[str, float]]  # {ticker: {quantity, value, avg_price}}
    total_value: float
    unrealized_pnl: float
    realized_pnl: float
    daily_pnl: float = 0.0
    exposure: float = 0.0  # 시장 노출도


@dataclass
class TradingSession:
    """거래 세션"""
    session_id: str
    strategy_name: str
    start_time: pd.Timestamp
    end_time: Optional[pd.Timestamp]
    initial_capital: float
    final_capital: Optional[float]
    total_trades: int = 0
    total_pnl: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TradeRecorder:
    """
    거래 기록 관리 서비스

    백테스트 및 실제 거래의 모든 기록을 관리하고
    분석을 위한 데이터를 제공
    """

    def __init__(self, storage_path: str = "trade_records", storage_type: str = "sqlite"):
        """
        거래 기록기 초기화

        Args:
            storage_path: 저장 경로
            storage_type: 저장 방식 ('sqlite', 'csv', 'json')
        """
        self.storage_path = Path(storage_path)
        self.storage_type = storage_type
        self.storage_path.mkdir(exist_ok=True)

        # 메모리 캐시
        self.trade_cache: List[TradeRecord] = []
        self.portfolio_cache: List[PortfolioSnapshot] = []
        self.session_cache: Dict[str, TradingSession] = {}

        # 데이터베이스 초기화
        if storage_type == "sqlite":
            self._init_database()

    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        db_path = self.storage_path / "trades.db"

        with sqlite3.connect(db_path) as conn:
            # 거래 기록 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    strategy_name TEXT,
                    ticker TEXT,
                    trade_type TEXT,
                    quantity REAL,
                    price REAL,
                    timestamp TEXT,
                    reason TEXT,
                    pnl REAL,
                    commission REAL,
                    slippage REAL,
                    position_size REAL,
                    risk_level REAL,
                    duration INTEGER,
                    related_trade_id TEXT,
                    metadata TEXT
                )
            ''')

            # 포트폴리오 스냅샷 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    strategy_name TEXT,
                    cash REAL,
                    positions TEXT,
                    total_value REAL,
                    unrealized_pnl REAL,
                    realized_pnl REAL,
                    daily_pnl REAL,
                    exposure REAL
                )
            ''')

            # 거래 세션 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    session_id TEXT PRIMARY KEY,
                    strategy_name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    initial_capital REAL,
                    final_capital REAL,
                    total_trades INTEGER,
                    total_pnl REAL,
                    metadata TEXT
                )
            ''')

    def start_session(self, strategy_name: str, initial_capital: float,
                     session_id: Optional[str] = None) -> str:
        """
        거래 세션 시작

        Args:
            strategy_name: 전략명
            initial_capital: 초기 자본
            session_id: 세션 ID (선택사항)

        Returns:
            str: 세션 ID
        """
        if session_id is None:
            session_id = f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = TradingSession(
            session_id=session_id,
            strategy_name=strategy_name,
            start_time=pd.Timestamp.now(),
            end_time=None,
            initial_capital=initial_capital,
            final_capital=None
        )

        self.session_cache[session_id] = session
        return session_id

    def end_session(self, session_id: str, final_capital: float):
        """
        거래 세션 종료

        Args:
            session_id: 세션 ID
            final_capital: 최종 자본
        """
        if session_id in self.session_cache:
            session = self.session_cache[session_id]
            session.end_time = pd.Timestamp.now()
            session.final_capital = final_capital
            session.total_trades = len([t for t in self.trade_cache if t.strategy_name == session.strategy_name])
            session.total_pnl = final_capital - session.initial_capital

            self._save_session(session)

    def record_trade(self, trade: TradeRecord) -> str:
        """
        거래 기록

        Args:
            trade: 거래 기록

        Returns:
            str: 거래 ID
        """
        # 거래 ID 생성 (없는 경우)
        if not trade.trade_id:
            trade.trade_id = self._generate_trade_id(trade)

        # 캐시에 추가
        self.trade_cache.append(trade)

        # 영구 저장
        self._save_trade(trade)

        return trade.trade_id

    def record_portfolio_snapshot(self, snapshot: PortfolioSnapshot):
        """
        포트폴리오 스냅샷 기록

        Args:
            snapshot: 포트폴리오 스냅샷
        """
        self.portfolio_cache.append(snapshot)
        self._save_portfolio_snapshot(snapshot)

    def get_trades(self, strategy_name: Optional[str] = None,
                  ticker: Optional[str] = None,
                  start_date: Optional[pd.Timestamp] = None,
                  end_date: Optional[pd.Timestamp] = None) -> List[TradeRecord]:
        """
        거래 기록 조회

        Args:
            strategy_name: 전략명 필터
            ticker: 종목 필터
            start_date: 시작일 필터
            end_date: 종료일 필터

        Returns:
            List[TradeRecord]: 필터링된 거래 기록
        """
        trades = self.trade_cache.copy()

        # 필터 적용
        if strategy_name:
            trades = [t for t in trades if t.strategy_name == strategy_name]
        if ticker:
            trades = [t for t in trades if t.ticker == ticker]
        if start_date:
            trades = [t for t in trades if t.timestamp >= start_date]
        if end_date:
            trades = [t for t in trades if t.timestamp <= end_date]

        return trades

    def get_portfolio_history(self, strategy_name: str,
                            start_date: Optional[pd.Timestamp] = None,
                            end_date: Optional[pd.Timestamp] = None) -> List[PortfolioSnapshot]:
        """
        포트폴리오 히스토리 조회

        Args:
            strategy_name: 전략명
            start_date: 시작일
            end_date: 종료일

        Returns:
            List[PortfolioSnapshot]: 포트폴리오 히스토리
        """
        snapshots = [s for s in self.portfolio_cache if s.strategy_name == strategy_name]

        if start_date:
            snapshots = [s for s in snapshots if s.timestamp >= start_date]
        if end_date:
            snapshots = [s for s in snapshots if s.timestamp <= end_date]

        return sorted(snapshots, key=lambda x: x.timestamp)

    def get_trade_summary(self, strategy_name: str) -> Dict[str, Any]:
        """
        거래 요약 통계

        Args:
            strategy_name: 전략명

        Returns:
            Dict[str, Any]: 거래 요약 통계
        """
        trades = self.get_trades(strategy_name=strategy_name)

        if not trades:
            return {}

        total_trades = len(trades)
        buy_trades = [t for t in trades if t.trade_type == TradeType.BUY]
        sell_trades = [t for t in trades if t.trade_type in [TradeType.SELL, TradeType.HALF_SELL]]

        total_pnl = sum(t.pnl for t in trades)
        total_commission = sum(t.commission for t in trades)

        winning_trades = [t for t in sell_trades if t.pnl > 0]
        losing_trades = [t for t in sell_trades if t.pnl < 0]

        win_rate = len(winning_trades) / len(sell_trades) if sell_trades else 0
        avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.pnl for t in losing_trades]) if losing_trades else 0

        return {
            'total_trades': total_trades,
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_pnl': total_pnl,
            'total_commission': total_commission,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            'most_traded_ticker': self._get_most_traded_ticker(trades),
            'trading_frequency': self._calculate_trading_frequency(trades)
        }

    def export_trades_to_csv(self, strategy_name: str, file_path: Optional[str] = None) -> str:
        """
        거래 기록을 CSV로 내보내기

        Args:
            strategy_name: 전략명
            file_path: 파일 경로 (선택사항)

        Returns:
            str: 저장된 파일 경로
        """
        trades = self.get_trades(strategy_name=strategy_name)

        if not trades:
            raise ValueError(f"No trades found for strategy: {strategy_name}")

        if file_path is None:
            file_path = self.storage_path / f"{strategy_name}_trades.csv"

        # DataFrame으로 변환
        trade_data = []
        for trade in trades:
            trade_dict = asdict(trade)
            trade_dict['trade_type'] = trade_dict['trade_type'].value
            trade_dict['reason'] = trade_dict['reason'].value
            trade_dict['metadata'] = json.dumps(trade_dict['metadata'])
            trade_data.append(trade_dict)

        df = pd.DataFrame(trade_data)
        df.to_csv(file_path, index=False)

        return str(file_path)

    def import_trades_from_csv(self, file_path: str) -> int:
        """
        CSV에서 거래 기록 가져오기

        Args:
            file_path: CSV 파일 경로

        Returns:
            int: 가져온 거래 수
        """
        df = pd.read_csv(file_path)
        imported_count = 0

        for _, row in df.iterrows():
            try:
                trade = TradeRecord(
                    trade_id=row['trade_id'],
                    strategy_name=row['strategy_name'],
                    ticker=row['ticker'],
                    trade_type=TradeType(row['trade_type']),
                    quantity=row['quantity'],
                    price=row['price'],
                    timestamp=pd.Timestamp(row['timestamp']),
                    reason=TradeReason(row['reason']),
                    pnl=row.get('pnl', 0.0),
                    commission=row.get('commission', 0.0),
                    slippage=row.get('slippage', 0.0),
                    position_size=row.get('position_size', 0.0),
                    risk_level=row.get('risk_level', 0.0),
                    duration=row.get('duration'),
                    related_trade_id=row.get('related_trade_id'),
                    metadata=json.loads(row.get('metadata', '{}'))
                )
                self.record_trade(trade)
                imported_count += 1
            except Exception as e:
                print(f"Error importing trade: {e}")

        return imported_count

    def clear_cache(self):
        """캐시 클리어"""
        self.trade_cache.clear()
        self.portfolio_cache.clear()
        self.session_cache.clear()

    def backup_data(self, backup_path: Optional[str] = None) -> str:
        """
        데이터 백업

        Args:
            backup_path: 백업 경로 (선택사항)

        Returns:
            str: 백업 파일 경로
        """
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.storage_path / f"backup_{timestamp}.pkl"

        backup_data = {
            'trades': self.trade_cache,
            'portfolios': self.portfolio_cache,
            'sessions': self.session_cache,
            'timestamp': datetime.now()
        }

        with open(backup_path, 'wb') as f:
            pickle.dump(backup_data, f)

        return str(backup_path)

    def restore_data(self, backup_path: str):
        """
        데이터 복원

        Args:
            backup_path: 백업 파일 경로
        """
        with open(backup_path, 'rb') as f:
            backup_data = pickle.load(f)

        self.trade_cache = backup_data.get('trades', [])
        self.portfolio_cache = backup_data.get('portfolios', [])
        self.session_cache = backup_data.get('sessions', {})

    def _generate_trade_id(self, trade: TradeRecord) -> str:
        """거래 ID 생성"""
        timestamp_str = trade.timestamp.strftime('%Y%m%d_%H%M%S_%f')
        return f"{trade.strategy_name}_{trade.ticker}_{trade.trade_type.value}_{timestamp_str}"

    def _save_trade(self, trade: TradeRecord):
        """거래 기록 저장"""
        if self.storage_type == "sqlite":
            self._save_trade_to_db(trade)
        elif self.storage_type == "csv":
            self._save_trade_to_csv(trade)
        elif self.storage_type == "json":
            self._save_trade_to_json(trade)

    def _save_trade_to_db(self, trade: TradeRecord):
        """SQLite에 거래 기록 저장"""
        db_path = self.storage_path / "trades.db"

        with sqlite3.connect(db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.trade_id,
                trade.strategy_name,
                trade.ticker,
                trade.trade_type.value,
                trade.quantity,
                trade.price,
                trade.timestamp.isoformat(),
                trade.reason.value,
                trade.pnl,
                trade.commission,
                trade.slippage,
                trade.position_size,
                trade.risk_level,
                trade.duration,
                trade.related_trade_id,
                json.dumps(trade.metadata)
            ))

    def _save_portfolio_snapshot(self, snapshot: PortfolioSnapshot):
        """포트폴리오 스냅샷 저장"""
        if self.storage_type == "sqlite":
            db_path = self.storage_path / "trades.db"

            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                    INSERT INTO portfolio_snapshots
                    (timestamp, strategy_name, cash, positions, total_value, unrealized_pnl, realized_pnl, daily_pnl, exposure)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    snapshot.timestamp.isoformat(),
                    snapshot.strategy_name,
                    snapshot.cash,
                    json.dumps(snapshot.positions),
                    snapshot.total_value,
                    snapshot.unrealized_pnl,
                    snapshot.realized_pnl,
                    snapshot.daily_pnl,
                    snapshot.exposure
                ))

    def _save_session(self, session: TradingSession):
        """거래 세션 저장"""
        if self.storage_type == "sqlite":
            db_path = self.storage_path / "trades.db"

            with sqlite3.connect(db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO trading_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    session.session_id,
                    session.strategy_name,
                    session.start_time.isoformat(),
                    session.end_time.isoformat() if session.end_time else None,
                    session.initial_capital,
                    session.final_capital,
                    session.total_trades,
                    session.total_pnl,
                    json.dumps(session.metadata)
                ))

    def _get_most_traded_ticker(self, trades: List[TradeRecord]) -> str:
        """가장 많이 거래된 종목"""
        if not trades:
            return ""

        ticker_counts = {}
        for trade in trades:
            ticker_counts[trade.ticker] = ticker_counts.get(trade.ticker, 0) + 1

        return max(ticker_counts, key=ticker_counts.get)

    def _calculate_trading_frequency(self, trades: List[TradeRecord]) -> float:
        """거래 빈도 계산 (일 평균 거래 수)"""
        if not trades:
            return 0

        if len(trades) < 2:
            return 1

        start_date = min(t.timestamp for t in trades)
        end_date = max(t.timestamp for t in trades)
        days = (end_date - start_date).days + 1

        return len(trades) / days if days > 0 else 0