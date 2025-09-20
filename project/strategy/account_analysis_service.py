#!/usr/bin/env python3
"""
Account Analysis Service - Strategy Layer
Based on refer/SystemTrading/ChkAccount.py
Implements account analysis, portfolio evaluation, and risk assessment
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HoldingStatus(Enum):
    """보유 종목 상태"""
    HOLDING = "HOLDING"
    SELL_SIGNAL = "SELL_SIGNAL"
    LOSS_CUT = "LOSS_CUT"
    PROFIT_TAKING = "PROFIT_TAKING"

class AssetType(Enum):
    """자산 유형"""
    STOCK = "Stock"
    ETF = "ETF"
    CASH = "Cash"

@dataclass
class StockHolding:
    """보유 종목 정보"""
    ticker: str
    market: str = 'US'
    exchange: str = 'Stock'
    amount: float = 0.0
    avg_price: float = 0.0
    current_price: float = 0.0
    gain_percent: float = 0.0
    target_price: float = 0.0
    losscut_price: float = 0.0
    weight: float = 0.0

    # 기술적 지표
    rs_4w: float = 0.0
    sector_rs: float = 0.0
    industry_rs: float = 0.0

    # 펀더멘털 지표
    rev_yoy: float = 0.0
    eps_yoy: float = 0.0
    rev_growth: float = 0.0
    eps_growth: float = 0.0
    sector: str = 'Unknown'
    industry: str = 'Unknown'
    signal_type: str = 'Unknown'

    # 상태 정보
    status: HoldingStatus = HoldingStatus.HOLDING
    asset_type: AssetType = AssetType.STOCK

@dataclass
class AccountSummary:
    """계좌 요약 정보"""
    total_balance: float = 0.0
    cash_balance: float = 0.0
    stock_value: float = 0.0
    total_gain_percent: float = 0.0
    daily_gain_percent: float = 0.0
    num_holdings: int = 0
    num_stocks: int = 0
    num_etfs: int = 0

    # 리스크 지표
    portfolio_concentration: float = 0.0
    max_position_weight: float = 0.0
    sector_concentration: Dict[str, float] = field(default_factory=dict)

@dataclass
class SellRecommendation:
    """매도 추천 정보"""
    ticker: str
    reason: str
    urgency: str  # 'HIGH', 'MEDIUM', 'LOW'
    current_gain: float
    target_price: float
    losscut_price: float
    recommendation_type: str  # 'LOSS_CUT', 'PROFIT_TAKING', 'SIGNAL_SELL'

class AccountAnalysisService:
    """
    계좌 분석 및 포트폴리오 관리 서비스
    ChkAccount.py의 핵심 로직 구현
    """

    def __init__(self, area: str = 'US', std_risk: float = 0.05):
        self.area = area
        self.std_risk = std_risk
        self.min_loss_cut_percentage = 0.03

    def analyze_account(self,
                       holdings_data: List[Dict[str, Any]],
                       balance_data: Dict[str, Any],
                       market_data: Optional[Dict[str, pd.DataFrame]] = None) -> Dict[str, Any]:
        """
        종합 계좌 분석 (ChkAccount.py의 ChkStockinfo 로직 기반)

        Args:
            holdings_data: 보유 종목 데이터 리스트
            balance_data: 잔고 정보
            market_data: 시장 데이터 (선택)

        Returns:
            분석 결과 딕셔너리
        """
        try:
            # 1. 보유 종목 정보 분석
            holdings = self._analyze_holdings(holdings_data, market_data)

            # 2. 계좌 요약 정보 생성
            account_summary = self._create_account_summary(holdings, balance_data)

            # 3. 포트폴리오 리스크 분석
            risk_analysis = self._analyze_portfolio_risk(holdings, account_summary)

            # 4. 매도 추천 생성
            sell_recommendations = self._generate_sell_recommendations(holdings)

            # 5. 종합 분석 결과
            analysis_result = {
                'timestamp': datetime.now().isoformat(),
                'account_summary': account_summary,
                'holdings': holdings,
                'risk_analysis': risk_analysis,
                'sell_recommendations': sell_recommendations,
                'portfolio_metrics': self._calculate_portfolio_metrics(holdings, account_summary)
            }

            return analysis_result

        except Exception as e:
            logger.error(f"Error in account analysis: {e}")
            return self._get_default_analysis()

    def _analyze_holdings(self,
                         holdings_data: List[Dict[str, Any]],
                         market_data: Optional[Dict[str, pd.DataFrame]] = None) -> List[StockHolding]:
        """
        보유 종목 분석 (ChkAccount.py의 ChkStockinfo 로직)
        """
        try:
            holdings = []

            for holding_raw in holdings_data:
                holding = self._create_stock_holding(holding_raw, market_data)
                if holding:
                    holdings.append(holding)

            return holdings

        except Exception as e:
            logger.error(f"Error analyzing holdings: {e}")
            return []

    def _create_stock_holding(self,
                            holding_data: Dict[str, Any],
                            market_data: Optional[Dict[str, pd.DataFrame]] = None) -> Optional[StockHolding]:
        """
        개별 보유 종목 정보 생성
        """
        try:
            ticker = holding_data.get('StockCode', holding_data.get('ticker', ''))
            if not ticker:
                return None

            # 기본 정보
            holding = StockHolding(
                ticker=ticker,
                market=self._determine_market(ticker),
                amount=float(holding_data.get('StockAmt', holding_data.get('amount', 0))),
                avg_price=float(holding_data.get('StockAvgPrice', holding_data.get('avg_price', 0))),
                current_price=float(holding_data.get('CurrentPrice', holding_data.get('current_price', 0)))
            )

            # 자산 유형 결정
            holding.asset_type = self._determine_asset_type(ticker)
            holding.exchange = holding.asset_type.value

            # 수익률 계산
            if holding.avg_price > 0 and holding.current_price > 0:
                holding.gain_percent = round((holding.current_price - holding.avg_price) / holding.avg_price * 100, 2)

            # 시장 데이터에서 추가 정보 추출
            if market_data and ticker in market_data:
                self._enrich_with_market_data(holding, market_data[ticker])

            # 펀더멘털 데이터 보완
            self._enrich_with_fundamental_data(holding)

            # 타겟가격 및 손절가 계산
            self._calculate_target_and_losscut(holding)

            return holding

        except Exception as e:
            logger.error(f"Error creating stock holding for {ticker}: {e}")
            return None

    def _determine_market(self, ticker: str) -> str:
        """시장 구분 결정"""
        # 간단한 로직으로 구현 (실제로는 더 복잡한 로직 필요)
        if self.area == 'KR':
            return 'KR'
        elif len(ticker) <= 4 and ticker.isalpha():
            return 'US'
        else:
            return 'US'

    def _determine_asset_type(self, ticker: str) -> AssetType:
        """자산 유형 결정"""
        # ETF 판별 로직 (실제로는 외부 API 또는 데이터베이스 조회 필요)
        etf_patterns = ['SPY', 'QQQ', 'VTI', 'IWM', 'EFA', 'EEM']
        if any(pattern in ticker for pattern in etf_patterns):
            return AssetType.ETF
        return AssetType.STOCK

    def _enrich_with_market_data(self, holding: StockHolding, market_df: pd.DataFrame):
        """시장 데이터로 보유 종목 정보 보강"""
        try:
            if market_df.empty:
                return

            latest = market_df.iloc[-1]

            # 기술적 지표
            holding.rs_4w = round(float(latest.get('RS_4W', 0)), 2)
            holding.sector_rs = round(float(latest.get('SectorRS_4W', 0)), 2)
            holding.industry_rs = round(float(latest.get('IndustryRS_4W', 0)), 2)

            # 펀더멘털 지표
            if self.area == 'US':
                holding.rev_yoy = round(float(latest.get('REV_YOY', 0)), 3)
                holding.eps_yoy = round(float(latest.get('EPS_YOY', 0)), 3)
                holding.rev_growth = round(float(latest.get('Rev_Yoy_Growth', 0)), 3)
                holding.eps_growth = round(float(latest.get('Eps_Yoy_Growth', 0)), 3)
                holding.sector = str(latest.get('Sector', 'Unknown'))
                holding.industry = str(latest.get('Industry', 'Unknown'))

            holding.signal_type = str(latest.get('Type', 'Unknown'))

            # 현재가 업데이트 (시장 데이터가 더 정확할 수 있음)
            if latest.get('close', 0) > 0:
                holding.current_price = float(latest.get('close', 0))
                # 수익률 재계산
                if holding.avg_price > 0:
                    holding.gain_percent = round((holding.current_price - holding.avg_price) / holding.avg_price * 100, 2)

        except Exception as e:
            logger.error(f"Error enriching with market data for {holding.ticker}: {e}")

    def _enrich_with_fundamental_data(self, holding: StockHolding):
        """
        외부 데이터로 펀더멘털 정보 보강
        ChkAccount.py의 _get_fundamental_data_fallback 로직 참조
        """
        try:
            # 전략 A 신호 파일에서 데이터 가져오기
            signals_data = self._load_signals_data()
            if signals_data and holding.ticker in signals_data:
                signal_info = signals_data[holding.ticker]

                if holding.rs_4w == 0:
                    holding.rs_4w = round(float(signal_info.get('rs_4w', 0)), 2)
                if holding.sector == 'Unknown':
                    holding.sector = str(signal_info.get('sector', 'Unknown'))
                if holding.industry == 'Unknown':
                    holding.industry = str(signal_info.get('industry', 'Unknown'))
                if holding.rev_yoy == 0:
                    holding.rev_yoy = round(float(signal_info.get('rev_yoy', 0)), 3)
                if holding.eps_yoy == 0:
                    holding.eps_yoy = round(float(signal_info.get('eps_yoy', 0)), 3)

        except Exception as e:
            logger.error(f"Error enriching fundamental data for {holding.ticker}: {e}")

    def _load_signals_data(self) -> Optional[Dict[str, Any]]:
        """신호 데이터 파일 로드"""
        try:
            signals_path = Path("web/static/data/strategy_a_signals.json")
            if signals_path.exists():
                with open(signals_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('signals', {})
            return None
        except Exception as e:
            logger.error(f"Error loading signals data: {e}")
            return None

    def _calculate_target_and_losscut(self, holding: StockHolding):
        """타겟가격 및 손절가 계산"""
        try:
            # 타겟가격 계산 (간단한 로직)
            if holding.current_price > 0:
                # 기존 고점 대비 10% 상승을 타겟으로 설정 (실제로는 더 복잡한 로직)
                holding.target_price = round(holding.current_price * 1.10, 2)

            # 손절가 계산 (Position Sizing Service의 로직 활용)
            current_gain = 1 + (holding.gain_percent / 100)
            previous_losscut = holding.losscut_price if holding.losscut_price > 0 else holding.avg_price * 0.97

            holding.losscut_price = self._calculate_losscut_price(
                current_gain, previous_losscut, holding.avg_price
            )

        except Exception as e:
            logger.error(f"Error calculating target and losscut for {holding.ticker}: {e}")

    def _calculate_losscut_price(self, current_gain: float, previous_losscut: float, avg_price: float) -> float:
        """손절가 계산 (Position Sizing Service와 동일한 로직)"""
        try:
            if current_gain < (1 + self.std_risk):
                cut_line = (1 - self.std_risk)
                new_losscut = avg_price * cut_line
            else:
                cut_line = 1 - ((round((current_gain - 1) / self.std_risk, 0) - 1) * self.std_risk)
                new_losscut = avg_price * cut_line

            # 최소 손절 비율 적용
            min_cut_line = 1 - self.min_loss_cut_percentage
            min_losscut_price = avg_price * min_cut_line

            if new_losscut < min_losscut_price:
                new_losscut = min_losscut_price

            # 트레일링 스탑
            if new_losscut > previous_losscut:
                return round(new_losscut, 4)
            else:
                return round(previous_losscut, 4)

        except Exception as e:
            logger.error(f"Error calculating losscut price: {e}")
            return round(previous_losscut, 4)

    def _create_account_summary(self, holdings: List[StockHolding], balance_data: Dict[str, Any]) -> AccountSummary:
        """계좌 요약 정보 생성"""
        try:
            summary = AccountSummary()

            # 기본 잔고 정보
            summary.total_balance = float(balance_data.get('TotalMoney', balance_data.get('total_balance', 0)))
            summary.cash_balance = float(balance_data.get('CashMoney', balance_data.get('cash_balance', 0)))

            # 보유 종목 통계
            summary.num_holdings = len(holdings)
            summary.num_stocks = len([h for h in holdings if h.asset_type == AssetType.STOCK])
            summary.num_etfs = len([h for h in holdings if h.asset_type == AssetType.ETF])

            # 포지션 가치 계산
            total_stock_value = 0
            max_weight = 0

            for holding in holdings:
                position_value = holding.amount * holding.current_price
                total_stock_value += position_value

                # 비중 계산
                if summary.total_balance > 0:
                    holding.weight = round((position_value / summary.total_balance) * 100, 2)
                    max_weight = max(max_weight, holding.weight)

            summary.stock_value = total_stock_value
            summary.max_position_weight = max_weight

            # 수익률 계산
            if summary.total_balance > 0:
                total_cost = summary.total_balance - summary.cash_balance
                if total_cost > 0:
                    summary.total_gain_percent = round((total_stock_value - total_cost) / total_cost * 100, 2)

            # 집중도 계산
            summary.portfolio_concentration = self._calculate_concentration(holdings)
            summary.sector_concentration = self._calculate_sector_concentration(holdings)

            return summary

        except Exception as e:
            logger.error(f"Error creating account summary: {e}")
            return AccountSummary()

    def _calculate_concentration(self, holdings: List[StockHolding]) -> float:
        """포트폴리오 집중도 계산 (허핀달-허쉬만 지수)"""
        try:
            if not holdings:
                return 0.0

            weights = [h.weight / 100 for h in holdings if h.weight > 0]
            if not weights:
                return 0.0

            # HHI 계산
            hhi = sum(w ** 2 for w in weights)
            return round(hhi, 4)

        except Exception as e:
            logger.error(f"Error calculating concentration: {e}")
            return 0.0

    def _calculate_sector_concentration(self, holdings: List[StockHolding]) -> Dict[str, float]:
        """섹터별 집중도 계산"""
        try:
            sector_weights = {}

            for holding in holdings:
                sector = holding.sector if holding.sector != 'Unknown' else 'Other'
                if sector not in sector_weights:
                    sector_weights[sector] = 0.0
                sector_weights[sector] += holding.weight

            # 비중이 높은 섹터 순으로 정렬
            sorted_sectors = dict(sorted(sector_weights.items(), key=lambda x: x[1], reverse=True))

            return {k: round(v, 2) for k, v in sorted_sectors.items()}

        except Exception as e:
            logger.error(f"Error calculating sector concentration: {e}")
            return {}

    def _analyze_portfolio_risk(self, holdings: List[StockHolding], summary: AccountSummary) -> Dict[str, Any]:
        """포트폴리오 리스크 분석"""
        try:
            risk_analysis = {
                'overall_risk_level': 'MEDIUM',
                'concentration_risk': 'LOW',
                'sector_risk': 'LOW',
                'individual_risks': [],
                'recommendations': []
            }

            # 집중도 리스크
            if summary.portfolio_concentration > 0.3:
                risk_analysis['concentration_risk'] = 'HIGH'
                risk_analysis['recommendations'].append("포트폴리오가 과도하게 집중되어 있습니다. 분산투자를 고려하세요.")
            elif summary.portfolio_concentration > 0.2:
                risk_analysis['concentration_risk'] = 'MEDIUM'

            # 개별 종목 리스크
            for holding in holdings:
                if holding.weight > 40:  # 40% 이상 집중
                    risk_analysis['individual_risks'].append(f"{holding.ticker}: 과도한 집중 ({holding.weight:.1f}%)")
                elif holding.gain_percent < -15:  # 15% 이상 손실
                    risk_analysis['individual_risks'].append(f"{holding.ticker}: 큰 손실 ({holding.gain_percent:.1f}%)")

            # 섹터 리스크
            max_sector_weight = max(summary.sector_concentration.values()) if summary.sector_concentration else 0
            if max_sector_weight > 50:
                risk_analysis['sector_risk'] = 'HIGH'
                risk_analysis['recommendations'].append("특정 섹터에 과도하게 집중되어 있습니다.")
            elif max_sector_weight > 30:
                risk_analysis['sector_risk'] = 'MEDIUM'

            # 전체 리스크 레벨 결정
            risk_factors = [risk_analysis['concentration_risk'], risk_analysis['sector_risk']]
            if 'HIGH' in risk_factors:
                risk_analysis['overall_risk_level'] = 'HIGH'
            elif 'MEDIUM' in risk_factors:
                risk_analysis['overall_risk_level'] = 'MEDIUM'
            else:
                risk_analysis['overall_risk_level'] = 'LOW'

            return risk_analysis

        except Exception as e:
            logger.error(f"Error analyzing portfolio risk: {e}")
            return {'overall_risk_level': 'UNKNOWN'}

    def _generate_sell_recommendations(self, holdings: List[StockHolding]) -> List[SellRecommendation]:
        """매도 추천 생성 (ChkAccount.py의 ChkSellStocks 로직)"""
        try:
            recommendations = []

            for holding in holdings:
                # 손절 조건
                if holding.current_price > 0 and holding.losscut_price > 0:
                    if holding.current_price <= holding.losscut_price:
                        recommendations.append(SellRecommendation(
                            ticker=holding.ticker,
                            reason=f"손절가 도달: 현재가 ${holding.current_price:.2f} <= 손절가 ${holding.losscut_price:.2f}",
                            urgency='HIGH',
                            current_gain=holding.gain_percent,
                            target_price=holding.target_price,
                            losscut_price=holding.losscut_price,
                            recommendation_type='LOSS_CUT'
                        ))
                        continue

                # 큰 손실 경고
                if holding.gain_percent < -10:
                    recommendations.append(SellRecommendation(
                        ticker=holding.ticker,
                        reason=f"큰 손실 발생: {holding.gain_percent:.1f}%",
                        urgency='MEDIUM',
                        current_gain=holding.gain_percent,
                        target_price=holding.target_price,
                        losscut_price=holding.losscut_price,
                        recommendation_type='LOSS_CUT'
                    ))

                # 수익 실현 기회
                elif holding.gain_percent > 20:
                    recommendations.append(SellRecommendation(
                        ticker=holding.ticker,
                        reason=f"수익 실현 고려: {holding.gain_percent:.1f}% 수익",
                        urgency='LOW',
                        current_gain=holding.gain_percent,
                        target_price=holding.target_price,
                        losscut_price=holding.losscut_price,
                        recommendation_type='PROFIT_TAKING'
                    ))

            # 긴급도 순으로 정렬
            urgency_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            recommendations.sort(key=lambda x: urgency_order.get(x.urgency, 3))

            return recommendations

        except Exception as e:
            logger.error(f"Error generating sell recommendations: {e}")
            return []

    def _calculate_portfolio_metrics(self, holdings: List[StockHolding], summary: AccountSummary) -> Dict[str, Any]:
        """포트폴리오 성과 지표 계산"""
        try:
            metrics = {
                'total_return': summary.total_gain_percent,
                'num_profitable': len([h for h in holdings if h.gain_percent > 0]),
                'num_losing': len([h for h in holdings if h.gain_percent < 0]),
                'best_performer': None,
                'worst_performer': None,
                'avg_gain': 0.0,
                'volatility_estimate': 0.0
            }

            if holdings:
                # 최고/최악 종목
                best_holding = max(holdings, key=lambda h: h.gain_percent)
                worst_holding = min(holdings, key=lambda h: h.gain_percent)

                metrics['best_performer'] = {
                    'ticker': best_holding.ticker,
                    'gain': best_holding.gain_percent
                }
                metrics['worst_performer'] = {
                    'ticker': worst_holding.ticker,
                    'gain': worst_holding.gain_percent
                }

                # 평균 수익률
                gains = [h.gain_percent for h in holdings]
                metrics['avg_gain'] = round(np.mean(gains), 2)

                # 변동성 추정
                if len(gains) > 1:
                    metrics['volatility_estimate'] = round(np.std(gains), 2)

            return metrics

        except Exception as e:
            logger.error(f"Error calculating portfolio metrics: {e}")
            return {}

    def _get_default_analysis(self) -> Dict[str, Any]:
        """기본 분석 결과 반환"""
        return {
            'timestamp': datetime.now().isoformat(),
            'account_summary': AccountSummary(),
            'holdings': [],
            'risk_analysis': {'overall_risk_level': 'UNKNOWN'},
            'sell_recommendations': [],
            'portfolio_metrics': {}
        }

# 테스트 및 사용 예시
def create_sample_account_data():
    """테스트용 샘플 계좌 데이터 생성"""
    holdings_data = [
        {
            'StockCode': 'AAPL',
            'StockAmt': 100,
            'StockAvgPrice': 150.0,
            'CurrentPrice': 165.0,
            'Gain': 10.0
        },
        {
            'StockCode': 'MSFT',
            'StockAmt': 50,
            'StockAvgPrice': 300.0,
            'CurrentPrice': 285.0,
            'Gain': -5.0
        },
        {
            'StockCode': 'GOOGL',
            'StockAmt': 30,
            'StockAvgPrice': 120.0,
            'CurrentPrice': 140.0,
            'Gain': 16.67
        }
    ]

    balance_data = {
        'TotalMoney': 100000.0,
        'CashMoney': 20000.0
    }

    return holdings_data, balance_data

if __name__ == "__main__":
    # 테스트 실행
    service = AccountAnalysisService(area='US', std_risk=0.05)

    holdings_data, balance_data = create_sample_account_data()

    # 계좌 분석 실행
    analysis = service.analyze_account(holdings_data, balance_data)

    print("Account Analysis Service Test Results:")
    print(f"Total Holdings: {analysis['account_summary'].num_holdings}")
    print(f"Total Balance: ${analysis['account_summary'].total_balance:,.2f}")
    print(f"Stock Value: ${analysis['account_summary'].stock_value:,.2f}")
    print(f"Cash Balance: ${analysis['account_summary'].cash_balance:,.2f}")
    print(f"Total Gain: {analysis['account_summary'].total_gain_percent:.2f}%")
    print(f"Portfolio Concentration: {analysis['account_summary'].portfolio_concentration:.4f}")
    print(f"Overall Risk Level: {analysis['risk_analysis']['overall_risk_level']}")
    print(f"Sell Recommendations: {len(analysis['sell_recommendations'])}")

    # 매도 추천 출력
    for rec in analysis['sell_recommendations']:
        print(f"  - {rec.ticker}: {rec.reason} (Urgency: {rec.urgency})")

    print("\nAccount Analysis Service Test Completed Successfully!")