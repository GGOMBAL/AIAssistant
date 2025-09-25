"""
WebSocket Manager

KIS WebSocket API와의 연결을 관리하고 실시간 데이터를 처리하는 모듈
refer/WebSocket/WebSocket_Main.py의 KisWebSocket 클래스를 참고하여 구현
"""

import asyncio
import json
import logging
from typing import Dict, Callable, List, Optional, Any
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from ..models.trading_models import PriceData, MarketType


class WebSocketManager:
    """KIS WebSocket 연결 관리자"""

    def __init__(self, kis_config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)

        # KIS API 설정
        self.app_key = kis_config.get('app_key')
        self.secret_key = kis_config.get('secret_key')
        self.ws_url = kis_config.get('ws_url')
        self.approval_key = kis_config.get('approval_key')

        # WebSocket 연결
        self.websocket = None
        self.is_connected = False
        self.is_running = False

        # 구독 관리
        self.subscriptions: Dict[str, Dict] = {}  # symbol -> subscription_info
        self.callbacks: Dict[str, List[Callable]] = {}  # symbol -> list of callbacks

        # 재연결 설정
        self.max_reconnects = 10
        self.reconnect_count = 0
        self.base_delay = 5
        self.max_delay = 120

        # 통계
        self.messages_received = 0
        self.last_message_time = None
        self.connection_start_time = None

    async def connect(self) -> bool:
        """WebSocket 연결"""
        try:
            self.logger.info("[WebSocketManager] KIS WebSocket 연결 시도")

            if not self._validate_config():
                return False

            # WebSocket 연결
            headers = self._prepare_headers()

            self.websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )

            self.is_connected = True
            self.is_running = True
            self.connection_start_time = datetime.now()
            self.reconnect_count = 0

            self.logger.info("[WebSocketManager] WebSocket 연결 성공")

            # 메시지 수신 태스크 시작
            asyncio.create_task(self._message_listener())

            # 연결 상태 모니터링 태스크 시작
            asyncio.create_task(self._connection_monitor())

            return True

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 연결 실패: {e}")
            self.is_connected = False
            return False

    async def disconnect(self) -> bool:
        """WebSocket 연결 해제"""
        try:
            self.logger.info("[WebSocketManager] WebSocket 연결 해제")

            self.is_running = False
            self.is_connected = False

            if self.websocket:
                await self.websocket.close()
                self.websocket = None

            # 구독 정보 초기화
            self.subscriptions.clear()

            return True

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 연결 해제 실패: {e}")
            return False

    async def subscribe_price_data(self, symbol: str, callback: Callable) -> bool:
        """실시간 가격 데이터 구독"""
        try:
            if not self.is_connected:
                self.logger.warning(f"[WebSocketManager] WebSocket 연결되지 않음 ({symbol})")
                return False

            # 콜백 등록
            if symbol not in self.callbacks:
                self.callbacks[symbol] = []
            self.callbacks[symbol].append(callback)

            # 이미 구독 중이면 콜백만 추가
            if symbol in self.subscriptions:
                self.logger.info(f"[WebSocketManager] {symbol} 이미 구독 중 - 콜백 추가")
                return True

            # 구독 메시지 생성 (KIS WebSocket 프로토콜 기반)
            subscribe_message = self._create_subscribe_message(symbol)

            # 구독 메시지 전송
            await self.websocket.send(json.dumps(subscribe_message))

            # 구독 정보 저장
            self.subscriptions[symbol] = {
                'tr_id': 'HDFSCNT0',  # 해외주식 실시간 체결가
                'tr_key': symbol,
                'subscribed_at': datetime.now()
            }

            self.logger.info(f"[WebSocketManager] {symbol} 실시간 가격 구독 완료")
            return True

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 구독 실패 ({symbol}): {e}")
            return False

    async def unsubscribe_price_data(self, symbol: str) -> bool:
        """실시간 가격 데이터 구독 해제"""
        try:
            if symbol not in self.subscriptions:
                self.logger.warning(f"[WebSocketManager] {symbol} 구독되지 않음")
                return False

            # 구독 해제 메시지 생성
            unsubscribe_message = self._create_unsubscribe_message(symbol)

            # 구독 해제 메시지 전송
            if self.websocket and self.is_connected:
                await self.websocket.send(json.dumps(unsubscribe_message))

            # 구독 정보 제거
            del self.subscriptions[symbol]
            if symbol in self.callbacks:
                del self.callbacks[symbol]

            self.logger.info(f"[WebSocketManager] {symbol} 구독 해제 완료")
            return True

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 구독 해제 실패 ({symbol}): {e}")
            return False

    async def _message_listener(self):
        """WebSocket 메시지 수신 루프"""
        try:
            self.logger.info("[WebSocketManager] 메시지 수신 시작")

            async for message in self.websocket:
                try:
                    await self._process_message(message)
                    self.messages_received += 1
                    self.last_message_time = datetime.now()

                except Exception as e:
                    self.logger.error(f"[WebSocketManager] 메시지 처리 오류: {e}")

        except ConnectionClosed:
            self.logger.warning("[WebSocketManager] WebSocket 연결 종료됨")
            self.is_connected = False

            # 자동 재연결 시도
            if self.is_running:
                await self._attempt_reconnect()

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 메시지 수신 오류: {e}")
            self.is_connected = False

    async def _process_message(self, message: str):
        """수신된 메시지 처리"""
        try:
            # JSON 파싱
            data = json.loads(message)

            # KIS WebSocket 응답 구조에 따라 처리
            if 'header' in data and 'body' in data:
                header = data['header']
                body = data['body']

                # 실시간 체결가 데이터 처리
                if header.get('tr_id') == 'HDFSCNT0':
                    await self._process_price_data(body)

                # 시스템 메시지 처리
                elif 'rt_cd' in header:
                    await self._process_system_message(header, body)

            else:
                self.logger.debug(f"[WebSocketManager] 알 수 없는 메시지 형식: {message[:100]}")

        except json.JSONDecodeError as e:
            self.logger.error(f"[WebSocketManager] JSON 파싱 오류: {e}")
        except Exception as e:
            self.logger.error(f"[WebSocketManager] 메시지 처리 오류: {e}")

    async def _process_price_data(self, body: Dict):
        """가격 데이터 처리"""
        try:
            if 'output' not in body:
                return

            output = body['output']

            # KIS WebSocket 응답에서 필드 추출
            symbol = output.get('SYMB', '')
            price = float(output.get('LAST', 0))
            volume = int(output.get('VOLM', 0))

            # 추가 정보
            bid_price = output.get('BIDP')
            ask_price = output.get('ASKP')
            change = output.get('PRDY_VRSS')
            change_pct = output.get('PRDY_CTRT')

            if not symbol or price <= 0:
                return

            # PriceData 객체 생성
            price_data = PriceData(
                symbol=symbol,
                price=price,
                volume=volume,
                timestamp=datetime.now(),
                bid_price=float(bid_price) if bid_price else None,
                ask_price=float(ask_price) if ask_price else None,
                change=float(change) if change else None,
                change_pct=float(change_pct) if change_pct else None,
                market=self._determine_market(symbol)
            )

            # 등록된 콜백 함수들 호출
            if symbol in self.callbacks:
                for callback in self.callbacks[symbol]:
                    try:
                        await callback(price_data)
                    except Exception as e:
                        self.logger.error(f"[WebSocketManager] 콜백 실행 오류 ({symbol}): {e}")

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 가격 데이터 처리 오류: {e}")

    async def _process_system_message(self, header: Dict, body: Dict):
        """시스템 메시지 처리"""
        try:
            rt_cd = header.get('rt_cd')
            msg = header.get('msg1', '')

            if rt_cd == '0':
                self.logger.debug(f"[WebSocketManager] 시스템 응답: {msg}")
            else:
                self.logger.warning(f"[WebSocketManager] 시스템 오류 ({rt_cd}): {msg}")

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 시스템 메시지 처리 오류: {e}")

    async def _connection_monitor(self):
        """연결 상태 모니터링"""
        while self.is_running:
            try:
                # 연결 상태 확인
                if not self.is_connected:
                    self.logger.warning("[WebSocketManager] 연결 끊어짐 감지")
                    await self._attempt_reconnect()

                # 30초마다 핑 확인 (websockets 라이브러리가 자동 처리하지만 추가 검증)
                if self.websocket:
                    try:
                        await self.websocket.ping()
                    except Exception:
                        self.logger.warning("[WebSocketManager] 핑 실패 - 연결 문제 감지")
                        self.is_connected = False

                await asyncio.sleep(30)

            except Exception as e:
                self.logger.error(f"[WebSocketManager] 연결 모니터링 오류: {e}")
                await asyncio.sleep(10)

    async def _attempt_reconnect(self):
        """재연결 시도"""
        if self.reconnect_count >= self.max_reconnects:
            self.logger.error("[WebSocketManager] 최대 재연결 시도 횟수 초과")
            return False

        self.reconnect_count += 1
        delay = min(self.base_delay * (2 ** (self.reconnect_count - 1)), self.max_delay)

        self.logger.info(f"[WebSocketManager] 재연결 시도 {self.reconnect_count}/{self.max_reconnects} "
                        f"({delay}초 후)")

        await asyncio.sleep(delay)

        # 기존 연결 정리
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            self.websocket = None

        # 재연결
        success = await self.connect()

        if success:
            # 기존 구독 복원
            await self._restore_subscriptions()

        return success

    async def _restore_subscriptions(self):
        """기존 구독 복원"""
        try:
            subscriptions_to_restore = list(self.subscriptions.keys())
            self.subscriptions.clear()

            for symbol in subscriptions_to_restore:
                if symbol in self.callbacks:
                    # 첫 번째 콜백만 사용해서 재구독 (다른 콜백들은 이미 등록됨)
                    callback = self.callbacks[symbol][0]
                    await self.subscribe_price_data(symbol, callback)

            self.logger.info(f"[WebSocketManager] {len(subscriptions_to_restore)}개 구독 복원 완료")

        except Exception as e:
            self.logger.error(f"[WebSocketManager] 구독 복원 오류: {e}")

    def _validate_config(self) -> bool:
        """설정 검증"""
        if not self.app_key or not self.secret_key:
            self.logger.error("[WebSocketManager] API 키 정보 누락")
            return False

        if not self.ws_url:
            self.logger.error("[WebSocketManager] WebSocket URL 누락")
            return False

        return True

    def _prepare_headers(self) -> Dict[str, str]:
        """WebSocket 연결 헤더 준비"""
        return {
            'approval_key': self.approval_key or '',
            'custtype': 'P',
            'tr_type': '1',
            'content-type': 'utf-8'
        }

    def _create_subscribe_message(self, symbol: str) -> Dict:
        """구독 메시지 생성"""
        return {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "1",
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "HDFSCNT0",  # 해외주식 실시간 체결가
                    "tr_key": symbol
                }
            }
        }

    def _create_unsubscribe_message(self, symbol: str) -> Dict:
        """구독 해제 메시지 생성"""
        return {
            "header": {
                "approval_key": self.approval_key,
                "custtype": "P",
                "tr_type": "2",  # 구독 해제
                "content-type": "utf-8"
            },
            "body": {
                "input": {
                    "tr_id": "HDFSCNT0",
                    "tr_key": symbol
                }
            }
        }

    def _determine_market(self, symbol: str) -> MarketType:
        """심볼로 시장 유형 결정"""
        # 일반적인 NASDAQ 종목들
        nasdaq_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']

        if symbol in nasdaq_symbols:
            return MarketType.NASDAQ
        else:
            return MarketType.NYSE

    def get_connection_status(self) -> Dict[str, Any]:
        """연결 상태 정보"""
        uptime = None
        if self.connection_start_time:
            uptime = (datetime.now() - self.connection_start_time).total_seconds()

        return {
            'is_connected': self.is_connected,
            'is_running': self.is_running,
            'subscriptions_count': len(self.subscriptions),
            'messages_received': self.messages_received,
            'last_message_time': self.last_message_time.isoformat() if self.last_message_time else None,
            'reconnect_count': self.reconnect_count,
            'uptime_seconds': uptime,
            'subscribed_symbols': list(self.subscriptions.keys())
        }

    def set_price_callback(self, callback: Callable[[PriceData], None]) -> None:
        """가격 데이터 콜백 설정 (전체 심볼에 대해)"""
        try:
            self.global_price_callback = callback
            self.logger.info("[WebSocketManager] 글로벌 가격 콜백 설정 완료")
        except Exception as e:
            self.logger.error(f"[WebSocketManager] 가격 콜백 설정 실패: {e}")

    async def set_price_callback_async(self, callback: Callable[[PriceData], None]) -> bool:
        """비동기 가격 데이터 콜백 설정"""
        try:
            self.set_price_callback(callback)
            return True
        except Exception as e:
            self.logger.error(f"[WebSocketManager] 비동기 가격 콜백 설정 실패: {e}")
            return False


# 테스트 함수
async def test_websocket_manager():
    """WebSocketManager 테스트"""
    print("\n=== WebSocketManager 테스트 시작 ===")

    # 테스트 설정
    config = {
        'app_key': 'test_app_key',
        'secret_key': 'test_secret_key',
        'ws_url': 'ws://test.websocket.url',
        'approval_key': 'test_approval_key'
    }

    manager = WebSocketManager(config)

    # 콜백 함수 정의
    async def price_callback(price_data: PriceData):
        print(f"[CALLBACK] {price_data.symbol}: ${price_data.price:.2f} "
              f"Vol: {price_data.volume:,} "
              f"({price_data.change_pct:+.2f}%)")

    try:
        # 연결 테스트 (실제 연결은 실패하지만 로직 검증)
        print("1. 연결 테스트...")
        connected = await manager.connect()
        print(f"   연결 결과: {'성공' if connected else '실패 (예상됨)'}")

        # 구독 테스트
        print("\n2. 구독 테스트...")
        symbols = ['AAPL', 'MSFT', 'GOOGL']
        for symbol in symbols:
            success = await manager.subscribe_price_data(symbol, price_callback)
            print(f"   {symbol} 구독: {'성공' if success else '실패'}")

        # 상태 확인
        print("\n3. 연결 상태 확인...")
        status = manager.get_connection_status()
        print(f"   상태: {status}")

        # 연결 해제
        print("\n4. 연결 해제 테스트...")
        disconnected = await manager.disconnect()
        print(f"   해제 결과: {'성공' if disconnected else '실패'}")

    except Exception as e:
        print(f"테스트 실패: {e}")
        import traceback
        traceback.print_exc()

    print("\n=== WebSocketManager 테스트 완료 ===")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_websocket_manager())