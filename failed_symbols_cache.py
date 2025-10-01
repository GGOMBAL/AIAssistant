"""
실패한 종목 캐시 시스템

unlisted 또는 데이터가 없는 종목들을 캐시하여
재시도를 방지하고 로딩 성능을 향상시킵니다.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Set, List
import logging

logger = logging.getLogger(__name__)

class FailedSymbolsCache:
    """실패한 종목 캐시 관리"""

    def __init__(self, cache_file: str = "failed_symbols_cache.json", cache_days: int = 30):
        self.cache_file = cache_file
        self.cache_days = cache_days
        self.failed_symbols: dict = {}
        self.load_cache()

    def load_cache(self) -> None:
        """캐시 파일 로드"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.failed_symbols = data.get('failed_symbols', {})

                # 오래된 캐시 정리
                self._cleanup_old_cache()
                logger.info(f"[CACHE] 실패한 종목 캐시 로드: {len(self.failed_symbols)}개")
            else:
                self.failed_symbols = {}
                logger.info("[CACHE] 새로운 실패한 종목 캐시 생성")

        except Exception as e:
            logger.warning(f"[CACHE] 캐시 로드 실패: {e}")
            self.failed_symbols = {}

    def save_cache(self) -> None:
        """캐시 파일 저장"""
        try:
            cache_data = {
                'failed_symbols': self.failed_symbols,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            logger.debug(f"[CACHE] 실패한 종목 캐시 저장: {len(self.failed_symbols)}개")

        except Exception as e:
            logger.error(f"[CACHE] 캐시 저장 실패: {e}")

    def _cleanup_old_cache(self) -> None:
        """오래된 캐시 항목 정리"""
        cutoff_date = datetime.now() - timedelta(days=self.cache_days)
        cutoff_str = cutoff_date.isoformat()

        old_count = len(self.failed_symbols)
        self.failed_symbols = {
            symbol: fail_date for symbol, fail_date in self.failed_symbols.items()
            if fail_date > cutoff_str
        }

        cleaned_count = old_count - len(self.failed_symbols)
        if cleaned_count > 0:
            logger.info(f"[CACHE] 오래된 캐시 정리: {cleaned_count}개 제거")

    def is_failed_symbol(self, symbol: str) -> bool:
        """종목이 실패 목록에 있는지 확인"""
        return symbol in self.failed_symbols

    def add_failed_symbol(self, symbol: str, reason: str = "unlisted") -> None:
        """실패한 종목 추가"""
        self.failed_symbols[symbol] = datetime.now().isoformat()
        logger.debug(f"[CACHE] 실패한 종목 추가: {symbol} ({reason})")

    def remove_failed_symbol(self, symbol: str) -> None:
        """실패한 종목 제거 (복구된 경우)"""
        if symbol in self.failed_symbols:
            del self.failed_symbols[symbol]
            logger.info(f"[CACHE] 실패한 종목 제거: {symbol}")

    def get_failed_symbols(self) -> Set[str]:
        """실패한 종목 목록 반환"""
        return set(self.failed_symbols.keys())

    def filter_symbols(self, symbols: List[str]) -> List[str]:
        """실패한 종목을 제외한 필터링된 종목 목록 반환"""
        filtered = [symbol for symbol in symbols if not self.is_failed_symbol(symbol)]
        skipped_count = len(symbols) - len(filtered)

        if skipped_count > 0:
            logger.info(f"[CACHE] 실패한 종목 제외: {skipped_count}개 스킵, {len(filtered)}개 로딩 예정")

        return filtered

    def get_cache_stats(self) -> dict:
        """캐시 통계 정보"""
        return {
            'total_failed_symbols': len(self.failed_symbols),
            'cache_file': self.cache_file,
            'cache_days': self.cache_days,
            'oldest_entry': min(self.failed_symbols.values()) if self.failed_symbols else None,
            'newest_entry': max(self.failed_symbols.values()) if self.failed_symbols else None
        }


# 전역 캐시 인스턴스
_failed_cache = None

def get_failed_symbols_cache() -> FailedSymbolsCache:
    """전역 실패한 종목 캐시 인스턴스 반환"""
    global _failed_cache
    if _failed_cache is None:
        _failed_cache = FailedSymbolsCache()
    return _failed_cache

def cleanup_cache_on_exit():
    """프로그램 종료시 캐시 저장"""
    global _failed_cache
    if _failed_cache is not None:
        _failed_cache.save_cache()

# 프로그램 종료시 자동 저장 등록
import atexit
atexit.register(cleanup_cache_on_exit)