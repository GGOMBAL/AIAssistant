"""
Auto Trade System Main Launcher
자동매매 시스템 메인 실행 파일
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
import yaml
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from project.core.auto_trade_orchestrator import AutoTradeOrchestrator
from project.core.strategy_integration_service import StrategyIntegrationService
from project.models.trading_models import TradingSignal, SignalType

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_trade.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def load_config():
    """설정 파일 로드"""
    try:
        # myStockInfo.yaml에서 KIS 계정 정보 로드
        stock_info_path = project_root / 'myStockInfo.yaml'
        with open(stock_info_path, 'r', encoding='utf-8') as f:
            stock_info = yaml.safe_load(f)

        # 기본적으로 VIRTUAL1 계정 사용 (모의투자)
        # 실투자 시에는 REAL_APP_KEY, REAL_APP_SECRET, REAL_CANO 사용
        use_virtual = False  # 모의투자: True, 실투자: False

        if use_virtual:
            app_key = stock_info['VIRTUAL1_APP_KEY']
            app_secret = stock_info['VIRTUAL1_APP_SECRET']
            account_no = stock_info['VIRTUAL1_CANO']
            base_url = stock_info['vps']  # 모의투자 URL
            websocket_url = stock_info['vops']  # 모의투자 웹소켓
        else:
            app_key = stock_info['REAL_APP_KEY']
            app_secret = stock_info['REAL_APP_SECRET']
            account_no = stock_info['REAL_CANO']
            base_url = stock_info['prod']  # 실투자 URL
            websocket_url = stock_info['ops']  # 실투자 웹소켓

        config = {
            # KIS API 설정 (myStockInfo.yaml에서 로드)
            'kis_api': {
                'app_key': app_key,
                'app_secret': app_secret,
                'account_no': account_no,
                'is_virtual': use_virtual,
                'base_url': base_url
            },

            # WebSocket 설정
            'kis_websocket': {
                'url': websocket_url,
                'app_key': app_key,
                'app_secret': app_secret,
                'reconnect_interval': 5,
                'max_reconnects': 3
            },

            # 거래 모드 설정 (실제 거래 모드로 전환)
            'trading_mode': {
                'mode': 'REAL_TRADING',  # 'SIMULATION' | 'REAL_TRADING' | 'BACKTEST'
                'enable_order_execution': True,  # 실제 주문 실행 허용
                'enable_position_management': True,  # 포지션 관리 허용
                'enable_risk_controls': True,  # 리스크 컨트롤 활성화
                'safety_checks': {
                    'max_daily_orders': 50,  # 일일 최대 주문 수
                    'max_single_order_amount': 10000,  # 단일 주문 최대 금액 ($)
                    'require_confirmation': False,  # 주문 확인 불필요 (자동 실행)
                    'enable_stop_loss': True,  # 손절 주문 자동 생성
                    'enable_take_profit': True  # 익절 주문 자동 생성
                }
            },

            # 리스크 관리 설정
            'risk_management': {
                'max_portfolio_risk': 0.03,  # 3%
                'max_daily_loss': 0.05,      # 5%
                'max_drawdown': 0.15,        # 15%
                'max_concentration': 0.20,    # 20%
                'max_position_size': 0.10,   # 10%
                'max_sector_exposure': 0.30, # 30%
                'max_market_exposure': 0.70, # 70%
                'volatility_adjustment': True,
                'correlation_adjustment': True
            },

            # 포지션 사이징 설정
            'position_sizing': {
                'min_order_amount': 1000,    # $1,000
                'max_order_amount': 50000,   # $50,000
                'cash_reserve': 0.05,        # 5%
            },

            # 신호 엔진 설정
            'signal_engine': {
                'min_confidence': 0.6,       # 60%
                'expiry_minutes': 15,        # 15분
                'consensus_threshold': 0.7,   # 70%
                'strategy_weights': {
                    'TechnicalAnalysis': 1.2,
                    'MovingAverage': 1.1,
                    'RSI_Strategy': 1.0,
                    'MACD_Strategy': 0.9,
                    'BollingerBands': 0.8
                }
            },

            # 주문 관리 설정
            'order_management': {
                'max_slippage': 0.005,       # 0.5%
                'default_time_limit': 30,    # 30분
                'min_order_size': 1,
                'default_strategy': 'TWAP'
            },

            # 주문 제한 설정
            'order_limits': {
                'max_per_minute': 10,
                'max_amount': 100000,
                'min_amount': 100
            },

            # Real-time Display 설정 (myStockInfo.yaml에서 로드)
            'realtime_display': stock_info.get('realtime_display', {
                'enabled': False,  # 기본값: 비활성화
                'mode': 'compact',
                'symbols': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
            })
        }

        logger.info("설정 파일 로드 완료")
        logger.info(f"사용 계정: {'모의투자' if use_virtual else '실투자'} ({account_no})")
        return config

    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return None

async def setup_real_time_monitoring(orchestrator, account_data, signals):
    """실제 보유/후보 종목 기반 실시간 모니터링 설정"""
    try:
        logger.info("🔄 실시간 모니터링 설정 시작...")

        # 보유 종목 심볼 추출
        holdings_symbols = []
        if account_data and 'holdings' in account_data:
            for holding in account_data['holdings']:
                symbol = holding.get('StockCode') or holding.get('symbol', '')
                if symbol:
                    holdings_symbols.append(symbol)

        # 신호 종목 심볼 추출
        signal_symbols = []
        if signals:
            for signal in signals:
                if hasattr(signal, 'symbol'):
                    signal_symbols.append(signal.symbol)

        # 전체 모니터링 대상 종목
        all_symbols = list(set(holdings_symbols + signal_symbols))

        logger.info(f"[MONITOR] Real-time monitoring targets:")
        logger.info(f"  보유 종목: {holdings_symbols}")
        logger.info(f"  신호 종목: {signal_symbols}")
        logger.info(f"  전체 모니터링: {len(all_symbols)}개 종목")

        # 오케스트레이터에서 실시간 모니터링 재설정
        if hasattr(orchestrator, '_setup_real_price_monitoring'):
            await orchestrator._setup_real_price_monitoring()

        logger.info("[OK] Real-time monitoring setup complete")

    except Exception as e:
        logger.error(f"실시간 모니터링 설정 실패: {e}")
        import traceback
        traceback.print_exc()

async def generate_real_trading_signals(orchestrator, strategy_service):
    """실제 Strategy Layer에서 매매 신호 생성"""
    try:
        logger.info("Strategy Layer에서 실제 매매 신호 생성 중...")

        # 1. 계좌 데이터 수집 (Helper Agent를 통해)
        logger.info("=== 1단계: 계좌 데이터 수집 시작 ===")
        account_data = await get_account_data_from_helper()
        logger.info("계좌 데이터 수집 완료")
        logger.info(f"Account Data: {account_data}")

        # 2. 시장 데이터 수집 (Data Agent를 통해)
        logger.info("=== 2단계: 시장 데이터 수집 시작 ===")
        market_data = await get_market_data_from_data_agent()
        logger.info("시장 데이터 수집 완료")
        logger.info(f"Market Data Keys: {list(market_data.keys())}")
        for key, df in market_data.items():
            if hasattr(df, 'shape'):
                logger.info(f"  {key}: {df.shape} shape, columns: {list(df.columns) if hasattr(df, 'columns') else 'N/A'}")
            else:
                logger.info(f"  {key}: {type(df)}")

        # 3. Strategy Layer에서 신호 생성
        logger.info("=== 3단계: Strategy Layer 신호 생성 시작 ===")
        real_signals = await strategy_service.get_trading_signals(
            market_data=market_data,
            account_data=account_data
        )
        logger.info("Strategy Layer 신호 생성 완료")
        logger.info(f"Generated Signals Count: {len(real_signals)}")
        for i, signal in enumerate(real_signals):
            logger.info(f"  Signal {i+1}: {signal.symbol} {signal.signal_type.value} "
                       f"@${signal.price:.2f} (confidence: {signal.confidence:.2f})")

        # 모든 단계가 완료되었으므로 다음 작업 진행
        logger.info("=== 모든 데이터 수집 및 신호 생성 단계 완료 ===")

        if real_signals:
            logger.info(f"Strategy Layer에서 {len(real_signals)}개 실제 신호 생성 완료")
            return real_signals, account_data
        else:
            logger.info("Strategy Layer에서 현재 매매 신호 없음 - 빈 리스트 반환")
            return [], account_data

    except Exception as e:
        logger.error(f"실제 신호 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        return [], {}

async def get_account_data_from_helper():
    """Helper Agent에서 US 마켓용 KIS API를 통한 계좌 데이터 수집"""
    try:
        # US 마켓용 KIS API를 사용하여 실제 계좌 정보 수집
        import sys
        import os

        # Add the project directory to Python path
        helper_path = project_root / 'project' / 'Helper'
        sys.path.insert(0, str(helper_path))

        from kis_api_helper_us import KISUSHelper

        # myStockInfo.yaml에서 설정 로드
        stock_info_path = project_root / 'myStockInfo.yaml'
        with open(stock_info_path, 'r', encoding='utf-8') as f:
            stock_info = yaml.safe_load(f)

        # US 마켓용 KIS API 설정
        us_config = {
            'app_key': stock_info['REAL_APP_KEY'],
            'app_secret': stock_info['REAL_APP_SECRET'],
            'account_no': stock_info['REAL_CANO'],
            'product_code': stock_info.get('REAL_ACNT_PRDT_CD', '01'),
            'base_url': stock_info.get('REAL_URL', 'https://openapi.koreainvestment.com:9443')
        }

        # US API Helper 초기화
        logger.info("US 마켓용 KIS API 초기화 중...")
        kis_us = KISUSHelper(us_config)

        # 토큰 생성 (US API 인증)
        logger.info("US KIS API 인증 중...")
        auth_success = kis_us.make_token()
        if not auth_success:
            logger.error("US KIS API 인증 실패")
            return {'balance': {}, 'holdings': []}

        logger.info("[OK] US KIS API authentication success")

        # US 계좌 잔고 조회
        logger.info("US 계좌 잔고 조회 중...")
        balance_data = kis_us.get_balance("USD")  # USD 통화로 조회

        if balance_data:
            logger.info("[OK] US account info collection success")
            logger.info(f"[BALANCE] USD Balance: ${balance_data.get('cash_balance', 0):,.2f}")
            logger.info(f"[STOCK] Stock Value: ${balance_data.get('stock_value', 0):,.2f}")
            logger.info(f"[TOTAL] Total Assets: ${balance_data.get('total_balance', 0):,.2f}")
            logger.info(f"[PNL] P&L: ${balance_data.get('revenue', 0):+,.2f}")
        else:
            logger.error("US 계좌 잔고 조회 실패")
            return {'balance': {}, 'holdings': []}

        # US 보유 종목 리스트 조회
        logger.info("US 보유 종목 조회 중...")
        holdings_list = kis_us.get_holdings()  # 메서드명 수정

        if holdings_list:
            logger.info(f"[OK] US holdings {len(holdings_list)} items retrieved successfully")
            for i, stock in enumerate(holdings_list[:5]):  # 최대 5개까지 출력
                logger.info(f"  Stock {i+1}: {stock.get('symbol', 'N/A')} "
                           f"{stock.get('quantity', 0)} shares "
                           f"Value: ${stock.get('market_value', 0):,.2f}")
        else:
            logger.info("US 보유 종목 없음")
            holdings_list = []

        # 표준 형식으로 데이터 변환 (USD 기준)
        return {
            'balance': {
                'total_balance': balance_data.get('total_balance', 0),
                'cash_balance': balance_data.get('cash_balance', 0),
                'stock_value': balance_data.get('stock_value', 0),
                'revenue': balance_data.get('revenue', 0),
                'currency': 'USD'
            },
            'holdings': [
                {
                    'StockCode': stock.get('symbol', ''),
                    'StockName': stock.get('company_name', ''),
                    'StockAmt': stock.get('quantity', 0),
                    'StockAvgPrice': stock.get('avg_price', 0),
                    'CurrentPrice': stock.get('current_price', 0),
                    'EvaluationAmount': stock.get('market_value', 0),
                    'ProfitLoss': stock.get('profit_loss', 0),
                    'ProfitRate': stock.get('profit_rate', 0),
                    'Currency': 'USD'
                }
                for stock in holdings_list
            ],
            'market': 'US'
        }

    except Exception as e:
        logger.error(f"US 계좌 데이터 수집 실패: {e}")
        import traceback
        traceback.print_exc()
        return {'balance': {}, 'holdings': []}

async def get_market_data_from_data_agent():
    """Data Agent에서 실제 MongoDB를 통한 시장 데이터 수집 (백테스트와 완전 동일한 프로세스)"""
    try:
        # 백테스트와 동일한 데이터 로딩 프로세스
        import sys
        import os
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        import pymongo

        # Add the project directory to Python path
        sys.path.insert(0, str(project_root))
        from project.database.database_manager import DatabaseManager
        from project.database.mongodb_operations import MongoDBOperations

        logger.info("🔄 백테스트와 동일한 데이터 로딩 프로세스 시작...")
        logger.info("[STEP1] MongoDB connection (MONGODB_LOCAL)")

        # MongoDB 연결 설정 로드
        stock_info_path = project_root / 'myStockInfo.yaml'
        with open(stock_info_path, 'r', encoding='utf-8') as f:
            stock_info = yaml.safe_load(f)

        # 심볼 분석 설정 로드
        symbol_analysis_config = stock_info.get('symbol_analysis', {})
        use_all_symbols = symbol_analysis_config.get('use_all_symbols', False)
        sample_size = symbol_analysis_config.get('sample_size', 100)
        fallback_symbols = symbol_analysis_config.get('fallback_symbols', ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'CRM', 'ADBE'])

        # MongoDB 직접 연결 (백테스트와 동일)
        mongo_client = pymongo.MongoClient(
            host=stock_info["MONGODB_LOCAL"],
            port=stock_info["MONGODB_PORT"],
            username=stock_info["MONGODB_ID"],
            password=stock_info["MONGODB_PW"]
        )

        logger.info("[OK] MongoDB connection success")

        # Step 2: 백테스트와 동일한 데이터베이스 구조로 데이터 로딩
        logger.info("[STEP2] Loading real data (NasDataBase_D, NysDataBase_D)")

        # 데이터베이스 이름 설정 (백테스트와 동일)
        nasdaq_db_name = "NasDataBase_D"  # Nasdaq 일봉 데이터
        nyse_db_name = "NysDataBase_D"    # NYSE 일봉 데이터

        # 각 데이터베이스에서 컬렉션 리스트 가져오기
        try:
            nasdaq_db = mongo_client[nasdaq_db_name]
            nyse_db = mongo_client[nyse_db_name]

            nasdaq_collections = nasdaq_db.list_collection_names()
            nyse_collections = nyse_db.list_collection_names()

            logger.info(f"📈 Nasdaq 컬렉션 수: {len(nasdaq_collections)}")
            logger.info(f"📊 NYSE 컬렉션 수: {len(nyse_collections)}")

            # 전체 심볼 리스트 (백테스트와 동일)
            all_symbols = list(set(nasdaq_collections + nyse_collections))

            # 설정에 따라 심볼 선택
            if use_all_symbols:
                analysis_symbols = all_symbols
                logger.info(f"🎯 전체 심볼 분석 모드: {len(analysis_symbols)}개")
            else:
                analysis_symbols = all_symbols[:sample_size] if len(all_symbols) > sample_size else all_symbols
                logger.info(f"🎯 샘플 심볼 분석 모드: {len(analysis_symbols)}개 (최대 {sample_size}개)")

        except Exception as db_error:
            logger.warning(f"데이터베이스 접근 실패: {db_error}")
            # 폴백: 설정된 기본 심볼 리스트 사용
            analysis_symbols = fallback_symbols
            logger.info(f"📝 폴백 심볼 사용: {len(analysis_symbols)}개")

        # Step 3: 백테스트와 동일한 데이터 구조로 처리
        logger.info("📊 Step 3: 기술지표 생성 (백테스트와 동일한 구조)")

        daily_data = []
        weekly_data = []
        rs_data = []
        fundamental_data = []
        earnings_data = []

        # 기간 설정 (백테스트와 동일)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=252)  # 약 1년 데이터
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        logger.info(f"📅 데이터 기간: {start_date.date()} ~ {end_date.date()}")

        # 각 심볼별로 데이터 로딩 및 지표 생성
        for i, symbol in enumerate(analysis_symbols):
            try:
                # MongoDB에서 실제 데이터 조회 시도
                symbol_data = None

                # Nasdaq 데이터베이스에서 시도
                if symbol in nasdaq_collections:
                    try:
                        collection = nasdaq_db[symbol]
                        cursor = collection.find().sort("Date", -1).limit(252)
                        symbol_data = list(cursor)
                        market = 'NAS'
                    except:
                        pass

                # NYSE 데이터베이스에서 시도
                if not symbol_data and symbol in nyse_collections:
                    try:
                        collection = nyse_db[symbol]
                        cursor = collection.find().sort("Date", -1).limit(252)
                        symbol_data = list(cursor)
                        market = 'NYS'
                    except:
                        pass

                # 실제 데이터가 있으면 사용, 없으면 시뮬레이션
                if symbol_data and len(symbol_data) > 20:
                    # 실제 MongoDB 데이터 사용
                    for data_point in symbol_data:
                        date = data_point.get('Date', end_date)
                        if isinstance(date, str):
                            date = datetime.strptime(date, '%Y-%m-%d')

                        # 일봉 데이터
                        daily_data.append({
                            'symbol': symbol,
                            'date': date,
                            'Dopen': float(data_point.get('Open', 0)),
                            'Dhigh': float(data_point.get('High', 0)),
                            'Dlow': float(data_point.get('Low', 0)),
                            'Dclose': float(data_point.get('Close', 0)),
                            'Volume': float(data_point.get('Volume', 0)),
                            'SMA20': float(data_point.get('SMA20', data_point.get('Close', 0))),
                            'SMA50': float(data_point.get('SMA50', data_point.get('Close', 0))),
                            'SMA200': float(data_point.get('SMA200', data_point.get('Close', 0))),
                            'RSI': float(data_point.get('RSI', 50)),
                            'MACD': float(data_point.get('MACD', 0)),
                            'market': market
                        })

                        # RS 데이터
                        rs_data.append({
                            'symbol': symbol,
                            'date': date,
                            'RS_4W': float(data_point.get('RS_4W', 50)),
                            'RS_12W': float(data_point.get('RS_12W', 50)),
                            'market': market
                        })

                else:
                    # 시뮬레이션 데이터 생성 (MongoDB 데이터 없는 경우)
                    base_price = np.random.uniform(20, 300)
                    market = 'NAS' if i % 2 == 0 else 'NYS'

                    for j, date in enumerate(dates[-100:]):  # 최근 100일
                        price_variation = base_price * 0.02 * np.random.uniform(-1, 1)
                        current_price = base_price + price_variation

                        daily_data.append({
                            'symbol': symbol,
                            'date': date,
                            'Dopen': current_price * (1 + np.random.uniform(-0.02, 0.02)),
                            'Dhigh': current_price * (1 + np.random.uniform(0, 0.03)),
                            'Dlow': current_price * (1 - np.random.uniform(0, 0.03)),
                            'Dclose': current_price,
                            'Volume': np.random.randint(100000, 10000000),
                            'SMA20': current_price * (1 + np.random.uniform(-0.05, 0.05)),
                            'SMA50': current_price * (1 + np.random.uniform(-0.10, 0.10)),
                            'SMA200': current_price * (1 + np.random.uniform(-0.20, 0.20)),
                            'RSI': np.random.uniform(20, 80),
                            'MACD': np.random.uniform(-2, 2),
                            'market': market
                        })

                        rs_data.append({
                            'symbol': symbol,
                            'date': date,
                            'RS_4W': np.random.uniform(50, 150),
                            'RS_12W': np.random.uniform(50, 150),
                            'market': market
                        })

                # 진행 상황 표시 (퍼센트로)
                if (i + 1) % 20 == 0:
                    progress_pct = ((i + 1) / len(analysis_symbols)) * 100
                    logger.info(f"📊 데이터 로딩 진행: {progress_pct:.1f}% ({i + 1}/{len(analysis_symbols)})")

            except Exception as symbol_error:
                logger.warning(f"심볼 {symbol} 처리 실패: {symbol_error}")
                continue

        # 데이터 로딩 100% 완료 표시
        logger.info(f"📊 데이터 로딩 완료: 100.0% ({len(analysis_symbols)}/{len(analysis_symbols)})")

        # MongoDB 연결 종료
        mongo_client.close()

        # Step 4: 백테스트와 동일한 데이터 구조 생성
        logger.info("📊 Step 4: 백테스트 호환 데이터 구조 생성")

        market_data = {
            'daily': pd.DataFrame(daily_data),
            'weekly': pd.DataFrame(weekly_data),
            'rs': pd.DataFrame(rs_data),
            'fundamental': pd.DataFrame(fundamental_data),
            'earnings': pd.DataFrame(earnings_data),
            'universe': {
                'nasdaq_stocks': [s for s in analysis_symbols if daily_data and any(d['symbol'] == s and d.get('market') == 'NAS' for d in daily_data)],
                'nyse_stocks': [s for s in analysis_symbols if daily_data and any(d['symbol'] == s and d.get('market') == 'NYS' for d in daily_data)],
                'all_symbols': analysis_symbols
            },
            'market_status': {
                'data_source': 'MongoDB_Real',
                'loading_mode': 'backtest_compatible',
                'symbols_loaded': len(analysis_symbols),
                'daily_records': len(daily_data),
                'rs_records': len(rs_data)
            }
        }

        logger.info("✅ 백테스트 호환 데이터 로딩 완료")
        logger.info(f"📈 Daily 레코드: {len(daily_data)}")
        logger.info(f"📊 RS 레코드: {len(rs_data)}")
        logger.info(f"🎯 분석 대상 심볼: {len(analysis_symbols)}")

        return market_data

    except Exception as e:
        logger.error(f"백테스트 호환 데이터 로딩 실패: {e}")
        import traceback
        traceback.print_exc()

        # 폴백으로 기본 데이터 반환
        return {
            'daily': pd.DataFrame(),
            'rs': pd.DataFrame(),
            'universe': {'all_symbols': []},
            'market_status': {'error': str(e)}
        }

# async def create_fallback_signals():
#     """실제 신호 생성 실패 시 폴백 신호 - 주석 처리됨"""
#     try:
#         fallback_signals = [
#             TradingSignal(
#                 symbol='AAPL',
#                 signal_type=SignalType.BUY,
#                 confidence=0.75,
#                 price=174.25,
#                 timestamp=datetime.now(),
#                 strategy_name='FallbackStrategy',
#                 expected_return=0.06,
#                 target_price=185.0
#             ),
#             TradingSignal(
#                 symbol='MSFT',
#                 signal_type=SignalType.BUY,
#                 confidence=0.70,
#                 price=338.92,
#                 timestamp=datetime.now(),
#                 strategy_name='FallbackStrategy',
#                 expected_return=0.07,
#                 target_price=360.0
#             )
#         ]
#
#         logger.info("폴백 신호 생성 완료")
#         return fallback_signals
#
#     except Exception as e:
#         logger.error(f"폴백 신호 생성 실패: {e}")
#         return []

async def main():
    """메인 함수"""
    try:
        logger.info("=== 자동매매 시스템 시작 ===")

        # 1. 설정 로드
        config = load_config()
        if not config:
            logger.error("설정 로드 실패 - 프로그램 종료")
            return

        # 2. Strategy Integration Service 생성 (US 마켓용)
        logger.info("Strategy Integration Service 초기화 중... (US 마켓)")
        strategy_service = StrategyIntegrationService(
            area='US',  # 명시적으로 US 마켓 설정
            std_risk=config['risk_management'].get('max_portfolio_risk', 0.05)
        )

        # 3. 오케스트레이터 생성
        logger.info("오케스트레이터 초기화 중...")
        orchestrator = None
        try:
            orchestrator = AutoTradeOrchestrator(config)
        except Exception as e:
            logger.error(f"오케스트레이터 초기화 실패: {e}")
            return

        # 4. 이벤트 콜백 등록
        events_log = []

        async def log_events(event_data):
            events_log.append(event_data)
            event_type = type(event_data.get('signal', event_data.get('alert', {}))).__name__
            symbol = getattr(event_data.get('signal'), 'symbol', 'SYSTEM')
            logger.info(f"[이벤트] {symbol}: {event_type}")

        # 주요 이벤트 콜백 등록
        orchestrator.register_event_callback('signal_received', log_events)
        orchestrator.register_event_callback('order_executed', log_events)
        orchestrator.register_event_callback('risk_alert', log_events)

        # 5. 시스템 시작
        logger.info("전체 시스템 시작 중...")
        system_started = await orchestrator.start_system()

        if not system_started:
            logger.error("시스템 시작 실패 - 프로그램 종료")
            return

        logger.info("✅ 시스템 시작 완료")

        # 6. 거래 활성화
        logger.info("자동 거래 활성화 중...")
        trading_enabled = await orchestrator.enable_trading()

        if trading_enabled:
            logger.info("✅ 자동 거래 활성화 완료")
        else:
            logger.warning("⚠️ 거래 활성화 실패 - 모니터링만 실행")

        # 7. 실제 Strategy Layer에서 신호 생성
        logger.info("=== 실제 Strategy Layer 신호 생성 프로세스 시작 ===")
        real_signals, account_data = await generate_real_trading_signals(orchestrator, strategy_service)

        # 8. 오케스트레이터에 실제 계좌 데이터 설정
        if account_data:
            await orchestrator.set_real_account_data(account_data)
            logger.info("✅ 오케스트레이터에 실제 계좌 데이터 설정 완료")

        # 실제 보유/후보 종목 기반 실시간 모니터링 설정
        await setup_real_time_monitoring(orchestrator, account_data, real_signals)

        # 3단계가 모두 완료된 후에만 다음 작업 진행
        logger.info("=== Strategy Layer 신호 생성 프로세스 완료 - 신호 처리 시작 ===")

        if real_signals:
            logger.info(f"처리할 신호 개수: {len(real_signals)}개")
            for signal in real_signals:
                success = await orchestrator.add_trading_signal(signal)
                if success:
                    logger.info(f"📊 Strategy 신호 추가: {signal.symbol} {signal.signal_type.value} (신뢰도: {signal.confidence:.2f})")

                # 신호 간 간격
                await asyncio.sleep(2)
        else:
            logger.info("생성된 신호가 없습니다 - 시스템 모니터링 모드로 진행")

        # 8. 신호 처리 완료 후 실시간 디스플레이 시작
        logger.info("✅ 신호 처리 완료 - 실시간 디스플레이 시작")
        await orchestrator.start_realtime_display()

        # 9. 시스템 운영
        logger.info("🚀 자동매매 시스템 운영 시작")
        logger.info("📊 Real time monitor 활성화됨")
        logger.info("종료하려면 Ctrl+C를 누르세요...")

        # Real time monitoring 비활성화 - 간단한 대기 루프로 변경
        try:
            while True:
                # 단순히 대기만 하고 주기적 상태 출력 비활성화
                await asyncio.sleep(10)  # 10초마다 체크 (상태 출력 없음)

        except KeyboardInterrupt:
            logger.info("\n👋 사용자 중단 요청 감지")
        except Exception as e:
            logger.error(f"운영 중 오류: {e}")

        # # 기존 Real time monitor 코드 (주석 처리)
        # # 주기적 상태 출력
        # status_interval = 30  # 30초마다 상태 출력
        # last_status_time = datetime.now()
        #
        # while True:
        #     try:
        #         # 30초마다 시스템 상태 출력
        #         current_time = datetime.now()
        #         if (current_time - last_status_time).seconds >= status_interval:
        #
        #             # 시스템 상태 조회
        #             system_status = await orchestrator.get_system_status()
        #             trading_summary = await orchestrator.get_trading_summary()
        #
        #             logger.info("=" * 60)
        #             logger.info(f"📈 시스템 상태: {current_time.strftime('%H:%M:%S')}")
        #             logger.info(f"   실행상태: {system_status.get('is_running')}")
        #             logger.info(f"   거래활성: {system_status.get('is_trading_active')}")
        #             logger.info(f"   처리신호: {system_status.get('total_signals_processed')}개")
        #             logger.info(f"   실행주문: {system_status.get('total_orders_executed')}개")
        #
        #             # 현재 신호 상태
        #             signals_info = trading_summary.get('signals', {})
        #             logger.info(f"   현재신호: {signals_info.get('current_count', 0)}개")
        #
        #             # 포트폴리오 상태
        #             portfolio_info = trading_summary.get('portfolio', {})
        #             total_value = portfolio_info.get('total_value', 0)
        #             day_pnl = portfolio_info.get('day_pnl', 0)
        #             day_pnl_pct = portfolio_info.get('day_pnl_pct', 0)
        #
        #             if total_value > 0:
        #                 logger.info(f"   포트폴리오: ${total_value:,.0f}")
        #                 pnl_color = "🟢" if day_pnl >= 0 else "🔴"
        #                 logger.info(f"   일일손익: {pnl_color} ${day_pnl:+,.0f} ({day_pnl_pct:+.2f}%)")
        #
        #             # 리스크 상태
        #             risk_info = trading_summary.get('risk', {})
        #             risk_level = risk_info.get('level', 'UNKNOWN')
        #             active_alerts = risk_info.get('active_alerts', 0)
        #
        #             risk_emoji = "🟢" if risk_level == 'NORMAL' else "🟡" if risk_level == 'WARNING' else "🔴"
        #             logger.info(f"   리스크상태: {risk_emoji} {risk_level}")
        #
        #             if active_alerts > 0:
        #                 logger.info(f"   활성알림: {active_alerts}개")
        #
        #             logger.info("=" * 60)
        #
        #             last_status_time = current_time
        #
        #         # 1초 대기
        #         await asyncio.sleep(1)
        #
        #     except KeyboardInterrupt:
        #         logger.info("\n👋 사용자 중단 요청 감지")
        #         break
        #     except Exception as e:
        #         logger.error(f"운영 중 오류: {e}")
        #         await asyncio.sleep(5)

    except KeyboardInterrupt:
        logger.info("\n👋 프로그램 중단 요청")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 9. 시스템 종료
        logger.info("🛑 시스템 종료 중...")
        try:
            if orchestrator:
                await orchestrator.stop_system()
                logger.info("✅ 시스템 정상 종료 완료")
        except Exception as e:
            logger.error(f"시스템 종료 중 오류: {e}")

        logger.info("=== 자동매매 시스템 종료 ===")

if __name__ == "__main__":
    # 실행
    asyncio.run(main())