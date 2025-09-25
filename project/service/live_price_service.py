"""
Live Price Service

실시간 가격 데이터 수신 및 관리 서비스
WebSocket을 통해 KIS API에서 실시간 가격 정보를 받아 처리
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json
import pymongo
import yaml
from pathlib import Path

from ..interfaces.service_interfaces import ILivePriceService, BaseService
from ..models.trading_models import PriceData, MarketType


class LivePriceService(BaseService, ILivePriceService):
    """실시간 가격 서비스 구현"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

        # 가격 데이터 캐시
        self.price_cache: Dict[str, PriceData] = {}

        # 전날 종가 데이터 캐시 (기본값용)
        self.previous_day_data: Dict[str, float] = {}

        # 구독 관리
        self.subscriptions: Dict[str, bool] = {}
        self.callbacks: Dict[str, List[Callable]] = {}

        # WebSocket 관련 (나중에 WebSocketManager로 대체)
        self.websocket_connection = None
        self.is_connected = False

        # 업데이트 통계
        self.update_count = 0
        self.last_update_time = None

    async def start_service(self) -> bool:
        """서비스 시작"""
        try:
            self.logger.info("[LivePriceService] 서비스 시작")

            # WebSocket 연결 초기화 (시뮬레이션)
            await self._initialize_websocket()

            # 가격 업데이트 태스크 시작
            asyncio.create_task(self._price_update_loop())

            await self.initialize()
            self.logger.info("[LivePriceService] 서비스 시작 완료")
            return True

        except Exception as e:
            self.log_error(f"서비스 시작 실패: {e}")
            return False

    async def stop_service(self) -> bool:
        """서비스 중지"""
        try:
            self.logger.info("[LivePriceService] 서비스 중지")
            self.is_connected = False
            await self.cleanup()
            return True
        except Exception as e:
            self.log_error(f"서비스 중지 실패: {e}")
            return False

    async def get_current_price(self, symbol: str) -> Optional[float]:
        """현재 가격 조회"""
        try:
            if symbol in self.price_cache:
                return self.price_cache[symbol].price

            # 캐시에 없으면 API 직접 조회 (시뮬레이션)
            price = await self._fetch_price_from_api(symbol)
            return price

        except Exception as e:
            self.log_error(f"가격 조회 실패 ({symbol}): {e}")
            return None

    async def subscribe_price_updates(self, symbol: str, callback: Callable) -> bool:
        """가격 업데이트 구독"""
        try:
            if symbol not in self.callbacks:
                self.callbacks[symbol] = []

            self.callbacks[symbol].append(callback)
            self.subscriptions[symbol] = True

            # 해당 심볼의 전날 데이터 로드 (아직 없는 경우)
            if symbol not in self.previous_day_data:
                await self._load_previous_day_data([symbol])

            # 전날 데이터를 기본값으로 초기 PriceData 설정
            if symbol not in self.price_cache and symbol in self.previous_day_data:
                initial_price_data = PriceData(
                    symbol=symbol,
                    price=self.previous_day_data[symbol],
                    volume=0,
                    timestamp=datetime.now(),
                    change=0.0,
                    change_pct=0.0,  # change_percent -> change_pct로 수정
                    market=self._get_market_type(symbol)
                    # source 파라미터 제거
                )
                self.price_cache[symbol] = initial_price_data
                self.logger.info(f"{symbol} 초기값 설정: ${self.previous_day_data[symbol]:.2f} (전날 종가)")

            self.logger.info(f"[LivePriceService] {symbol} 가격 구독 추가")

            # WebSocket 구독 메시지 전송 (시뮬레이션)
            await self._subscribe_websocket(symbol)

            return True

        except Exception as e:
            self.log_error(f"구독 추가 실패 ({symbol}): {e}")
            return False

    async def unsubscribe_price_updates(self, symbol: str) -> bool:
        """가격 업데이트 구독 해제"""
        try:
            if symbol in self.subscriptions:
                del self.subscriptions[symbol]

            if symbol in self.callbacks:
                del self.callbacks[symbol]

            self.logger.info(f"[LivePriceService] {symbol} 구독 해제")
            return True

        except Exception as e:
            self.log_error(f"구독 해제 실패 ({symbol}): {e}")
            return False

    async def get_subscribed_symbols(self) -> List[str]:
        """구독 중인 심볼 목록"""
        return list(self.subscriptions.keys())

    async def _initialize_websocket(self) -> bool:
        """WebSocket 연결 초기화 (시뮬레이션)"""
        try:
            # 실제로는 KIS WebSocket에 연결
            await asyncio.sleep(0.1)  # 연결 시뮬레이션
            self.is_connected = True
            self.logger.info("[LivePriceService] WebSocket 연결 성공 (시뮬레이션)")
            return True

        except Exception as e:
            self.log_error(f"WebSocket 연결 실패: {e}")
            return False

    async def _subscribe_websocket(self, symbol: str) -> bool:
        """WebSocket 구독 (시뮬레이션)"""
        try:
            if not self.is_connected:
                return False

            # 실제로는 KIS WebSocket 구독 메시지 전송
            self.logger.debug(f"[LivePriceService] WebSocket 구독: {symbol}")
            return True

        except Exception as e:
            self.log_error(f"WebSocket 구독 실패 ({symbol}): {e}")
            return False

    async def _fetch_price_from_api(self, symbol: str) -> Optional[float]:
        """API에서 직접 가격 조회 (전날 데이터 기반 시뮬레이션)"""
        try:
            # 전날 데이터가 있으면 기본값으로 사용
            if symbol in self.previous_day_data:
                base_price = self.previous_day_data[symbol]
                # 작은 랜덤 변동 추가 (±1%)
                variation = random.uniform(-0.01, 0.01)
                price = base_price * (1 + variation)
                self.logger.debug(f"{symbol} 가격 업데이트: ${base_price:.2f} -> ${price:.2f}")
                return round(price, 2)
            else:
                # 전날 데이터가 없으면 기본 가격 사용 (실제 보유 종목 우선)
                base_prices = {
                    'GH': 59.72,
                    'IREN': 41.77,
                    'MEDP': 496.14,
                    'PRIM': 132.38,
                    'QID': 21.9,
                    'RBLX': 132.22,
                    # 기타 종목들
                    'AAPL': 174.25,
                    'MSFT': 338.92,
                    'GOOGL': 125.87,
                    'TSLA': 248.33,
                    'NVDA': 421.45,
                    'JPM': 145.67,
                    'KO': 58.23,
                    'DIS': 95.44
                }

                base_price = base_prices.get(symbol, 100.0)
                # 랜덤 변동 추가 (±2%)
                variation = random.uniform(-0.02, 0.02)
                price = base_price * (1 + variation)
                return round(price, 2)

        except Exception as e:
            self.log_error(f"API 가격 조회 실패 ({symbol}): {e}")
            return None

    async def _load_previous_day_data(self, symbols: List[str]) -> None:
        """전날 종가 데이터 로드"""
        try:
            # MongoDB에서 전날 데이터 로드
            previous_data = await self._fetch_previous_day_from_mongodb(symbols)

            if previous_data:
                self.previous_day_data.update(previous_data)
                self.logger.info(f"전날 데이터 로드 완료: {len(previous_data)}개 종목")
            else:
                # MongoDB 데이터가 없으면 기본값 설정
                await self._set_default_previous_data(symbols)

        except Exception as e:
            self.log_error(f"전날 데이터 로드 실패: {e}")
            await self._set_default_previous_data(symbols)

    async def _fetch_previous_day_from_mongodb(self, symbols: List[str]) -> Dict[str, float]:
        """MongoDB에서 전날 종가 데이터 조회"""
        try:
            # myStockInfo.yaml에서 MongoDB 설정 로드
            project_root = Path(__file__).parent.parent.parent
            stock_info_path = project_root / 'myStockInfo.yaml'

            with open(stock_info_path, 'r', encoding='utf-8') as f:
                stock_info = yaml.safe_load(f)

            # MongoDB 연결
            mongo_client = pymongo.MongoClient(
                host=stock_info["MONGODB_LOCAL"],
                port=stock_info["MONGODB_PORT"],
                username=stock_info["MONGODB_ID"],
                password=stock_info["MONGODB_PW"],
                serverSelectionTimeoutMS=5000
            )

            previous_data = {}
            # 전날 날짜 계산 (평일만)
            today = datetime.now()
            days_back = 1
            while days_back <= 7:  # 최대 7일 전까지 찾기
                check_date = today - timedelta(days=days_back)
                # 주말 제외
                if check_date.weekday() < 5:  # 월(0) ~ 금(4)
                    target_date = check_date.strftime("%Y-%m-%d")
                    break
                days_back += 1

            # 각 심볼별로 전날 데이터 조회
            for symbol in symbols:
                try:
                    # Nasdaq과 NYSE 데이터베이스 모두 확인
                    for db_name in ['NasDataBase_D', 'NysDataBase_D']:
                        db = mongo_client[db_name]
                        if symbol in db.list_collection_names():
                            collection = db[symbol]
                            # 가장 최근 데이터 조회
                            latest_data = collection.find().sort("date", -1).limit(1)
                            for doc in latest_data:
                                if 'Dclose' in doc:
                                    previous_data[symbol] = float(doc['Dclose'])
                                    break
                            break
                except Exception as symbol_error:
                    self.logger.warning(f"심볼 {symbol} 전날 데이터 조회 실패: {symbol_error}")
                    continue

            mongo_client.close()
            return previous_data

        except Exception as e:
            self.log_error(f"MongoDB 전날 데이터 조회 실패: {e}")
            return {}

    async def _set_default_previous_data(self, symbols: List[str]) -> None:
        """기본 전날 데이터 설정"""
        try:
            # 기본 가격 설정 (실제 보유 종목 중심)
            default_prices = {
                'GH': 59.72,
                'IREN': 41.77,
                'MEDP': 496.14,
                'PRIM': 132.38,
                'QID': 21.9,
                'RBLX': 132.22,
                # 기타 종목들
                'AAPL': 174.25,
                'MSFT': 338.92,
                'GOOGL': 125.87,
                'TSLA': 248.33,
                'NVDA': 421.45,
                'JPM': 145.67,
                'KO': 58.23,
                'DIS': 95.44
            }

            for symbol in symbols:
                if symbol not in self.previous_day_data:
                    self.previous_day_data[symbol] = default_prices.get(symbol, 100.0)

            self.logger.info(f"기본 전날 데이터 설정 완료: {len(symbols)}개 종목")

        except Exception as e:
            self.log_error(f"기본 전날 데이터 설정 실패: {e}")

    async def _price_update_loop(self):
        """가격 업데이트 루프 (시뮬레이션)"""
        while self.is_running and self.is_connected:
            try:
                # 구독된 모든 심볼에 대해 가격 업데이트
                for symbol in list(self.subscriptions.keys()):
                    await self._simulate_price_update(symbol)

                # 1초마다 업데이트
                await asyncio.sleep(1)

            except Exception as e:
                self.log_error(f"가격 업데이트 루프 오류: {e}")
                await asyncio.sleep(5)

    async def _simulate_price_update(self, symbol: str):
        """가격 업데이트 시뮬레이션 (마켓 시간 고려)"""
        try:
            # 마켓 시간 확인 (미국 시간 기준)
            is_market_open = self._is_market_open()

            if is_market_open:
                # 마켓이 열려있으면 새로운 가격 생성 (웹소켓 데이터 시뮬레이션)
                new_price = await self._fetch_price_from_api(symbol)
                if new_price is None:
                    return

                source = "websocket_simulation"
                self.logger.debug(f"[마켓 오픈] {symbol} 웹소켓 가격 업데이트: ${new_price:.2f}")
            else:
                # 마켓이 닫혀있으면 이전 값 유지 (전날 종가 기반)
                if symbol in self.price_cache:
                    # 기존 가격 유지, 단지 타임스탬프만 업데이트
                    current_data = self.price_cache[symbol]
                    new_price = current_data.price
                    source = "previous_value_held"
                    self.logger.debug(f"[마켓 마감] {symbol} 이전 가격 유지: ${new_price:.2f}")
                elif symbol in self.previous_day_data:
                    # 캐시에 없으면 전날 종가 사용
                    new_price = self.previous_day_data[symbol]
                    source = "previous_day_close"
                    self.logger.debug(f"[마켓 마감] {symbol} 전날 종가 사용: ${new_price:.2f}")
                else:
                    return

            # 이전 가격과 비교하여 변동률 계산
            old_price = None
            if symbol in self.price_cache:
                old_price = self.price_cache[symbol].price

            # 전날 종가 대비 변동률 계산
            previous_close = self.previous_day_data.get(symbol, new_price)
            change = new_price - previous_close
            change_pct = (change / previous_close) * 100 if previous_close > 0 else 0.0

            # PriceData 객체 생성
            price_data = PriceData(
                symbol=symbol,
                price=new_price,
                volume=random.randint(1000, 100000),  # 시뮬레이션 거래량
                timestamp=datetime.now(),
                change=change,
                change_pct=change_pct,  # change_percent -> change_pct로 수정
                market=self._get_market_type(symbol)
                # source 파라미터는 PriceData에 없으므로 제거
            )

            # 캐시 업데이트
            self.price_cache[symbol] = price_data

            # 콜백 함수 호출
            if symbol in self.callbacks:
                for callback in self.callbacks[symbol]:
                    try:
                        await callback(price_data)
                    except Exception as e:
                        self.log_error(f"콜백 실행 오류 ({symbol}): {e}")

            # 통계 업데이트
            self.update_count += 1
            self.last_update_time = datetime.now()

        except Exception as e:
            self.log_error(f"가격 업데이트 시뮬레이션 오류 ({symbol}): {e}")

    def _is_market_open(self) -> bool:
        """미국 마켓 오픈 시간 확인"""
        try:
            from datetime import timezone
            import pytz

            # 미국 동부 시간대
            est = pytz.timezone('US/Eastern')
            now_est = datetime.now(est)

            # 주말 확인
            if now_est.weekday() >= 5:  # 토(5), 일(6)
                return False

            # 마켓 시간: 오전 9:30 ~ 오후 4:00 (EST)
            market_open = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_est.replace(hour=16, minute=0, second=0, microsecond=0)

            return market_open <= now_est <= market_close

        except ImportError:
            # pytz가 없으면 간단한 로컬 시간 기반 체크
            now = datetime.now()
            # 간단히 평일 9:30-16:00 로컬 시간으로 체크
            if now.weekday() >= 5:
                return False

            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            return market_open <= now <= market_close

        except Exception as e:
            self.logger.warning(f"마켓 시간 확인 실패: {e}")
            # 에러 시 기본적으로 마켓이 열린 것으로 간주 (시뮬레이션 유지)
            return True

    def _get_market_type(self, symbol: str) -> MarketType:
        """심볼로 시장 유형 판단"""
        try:
            # 실제 보유 종목과 일반적인 Nasdaq 종목들
            nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX', 'AMZN', 'IREN', 'RBLX']
            if symbol in nasdaq_symbols:
                return MarketType.NASDAQ
            else:
                # 나머지는 NYSE로 처리
                return MarketType.NYSE
        except Exception:
            # 기본값으로 US 반환
            return MarketType.US

    def get_service_stats(self) -> Dict[str, Any]:
        """서비스 통계"""
        return {
            'subscribed_symbols': len(self.subscriptions),
            'cached_prices': len(self.price_cache),
            'update_count': self.update_count,
            'last_update_time': self.last_update_time.isoformat() if self.last_update_time else None,
            'is_connected': self.is_connected,
            **self.get_health_status()
        }

# 테스트 함수
async def test_live_price_service():
    """LivePriceService 테스트"""
    print("\n=== LivePriceService 테스트 시작 ===")

    config = {
        'websocket': {
            'url': 'ws://test',
            'reconnect_interval': 5
        }
    }

    service = LivePriceService(config)

    # 콜백 함수 정의
    async def price_callback(price_data: PriceData):
        print(f"[CALLBACK] {price_data.symbol}: ${price_data.price:.2f} "
              f"({price_data.change:+.2f}, {price_data.change_pct:+.2f}%)")

    try:
        # 서비스 시작
        success = await service.start_service()
        print(f"서비스 시작: {'성공' if success else '실패'}")

        # 가격 구독
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
        for symbol in symbols:
            await service.subscribe_price_updates(symbol, price_callback)

        print(f"구독된 심볼: {await service.get_subscribed_symbols()}")

        # 5초간 실시간 업데이트 관찰
        print("\n실시간 가격 업데이트 관찰 (5초)...")
        await asyncio.sleep(5)

        # 통계 출력
        stats = service.get_service_stats()
        print(f"\n서비스 통계: {stats}")

        # 개별 가격 조회 테스트
        for symbol in symbols:
            price = await service.get_current_price(symbol)
            print(f"{symbol} 현재 가격: ${price:.2f}")

        # 서비스 중지
        await service.stop_service()
        print("\n서비스 중지 완료")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    import random
    asyncio.run(test_live_price_service())