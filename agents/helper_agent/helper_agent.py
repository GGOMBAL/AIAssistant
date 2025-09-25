# helper_agent.py
# Helper Agent - MongoDB 연결 및 외부 리소스 관리

import logging
from typing import Dict, Any, List, Optional
import yaml
import pymongo
from datetime import datetime
import os
import sys
from pathlib import Path

# 현재 파일의 디렉토리를 기준으로 프로젝트 루트 찾기
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

class HelperAgent:
    """
    Helper Agent - MongoDB 연결 및 외부 리소스 관리

    주요 역할:
    1. MongoDB 연결 관리
    2. 설정 파일 로드 및 관리
    3. 외부 API 연결 관리 (향후 확장)
    4. 시스템 리소스 모니터링
    5. 로깅 및 에러 처리
    """

    def __init__(self):
        self.logger = self._setup_logging()
        self.config = {}
        self.mongodb_client = None
        self.connections = {}

        # 설정 파일 로드
        self._load_configurations()

        # MongoDB 연결 초기화
        self._initialize_mongodb()

        self.logger.info("[성공] Helper Agent 초기화 완료")

    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger('HelperAgent')
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _load_configurations(self):
        """모든 설정 파일 로드"""
        config_dir = project_root / 'config'

        # 필수 설정 파일들
        config_files = [
            'api_credentials.yaml',
            'broker_config.yaml',
            'agent_model.yaml',
            'risk_management.yaml'
        ]

        for config_file in config_files:
            config_path = config_dir / config_file
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                        config_name = config_file.replace('.yaml', '')
                        self.config[config_name] = config_data
                        self.logger.info(f"[성공] {config_file} 로드 완료")
                else:
                    self.logger.warning(f"[경고] {config_file} 파일이 존재하지 않습니다")
                    # 기본 설정 생성
                    self._create_default_config(config_name, config_path)

            except Exception as e:
                self.logger.error(f"[실패] {config_file} 로드 실패: {str(e)}")
                self.config[config_file.replace('.yaml', '')] = {}

    def _create_default_config(self, config_name: str, config_path: Path):
        """기본 설정 파일 생성"""
        default_configs = {
            'api_credentials': {
                'mongodb': {
                    'host': 'localhost',
                    'port': 27017,
                    'username': '',
                    'password': '',
                    'auth_database': 'admin'
                },
                'brokers': {
                    'kis': {
                        'real_account': {
                            'app_key': '',
                            'app_secret': '',
                            'account_number': ''
                        },
                        'virtual_account': {
                            'app_key': '',
                            'app_secret': '',
                            'account_number': ''
                        }
                    }
                },
                'external_apis': {
                    'alpha_vantage': '',
                    'telegram_bot_token': ''
                }
            },
            'broker_config': {
                'trading_hours': {
                    'market_open': '09:00',
                    'market_close': '15:30',
                    'timezone': 'Asia/Seoul'
                },
                'supported_markets': ['NASDAQ', 'NYSE', 'KOSPI', 'KOSDAQ'],
                'order_types': ['market', 'limit', 'stop', 'stop_limit']
            },
            'agent_model': {
                'agents': {
                    'orchestrator': {
                        'primary_model': 'claude-3-opus-20240229',
                        'fallback_model': 'claude-3-sonnet-20240229'
                    },
                    'data_agent': {
                        'primary_model': 'claude-3-sonnet-20240229',
                        'fallback_model': 'gemini-pro'
                    },
                    'strategy_agent': {
                        'primary_model': 'claude-3-opus-20240229',
                        'fallback_model': 'gemini-pro'
                    },
                    'service_agent': {
                        'primary_model': 'claude-3-sonnet-20240229',
                        'fallback_model': 'claude-3-haiku-20240307'
                    },
                    'helper_agent': {
                        'primary_model': 'claude-3-haiku-20240307',
                        'fallback_model': 'gemini-pro'
                    }
                }
            },
            'risk_management': {
                'position_limits': {
                    'max_position_size': 0.1,  # 포트폴리오의 10%
                    'max_concentration': 0.2,  # 단일 종목 최대 20%
                    'max_sector_exposure': 0.3  # 단일 섹터 최대 30%
                },
                'risk_limits': {
                    'max_daily_loss': 0.02,  # 일일 최대 손실 2%
                    'max_monthly_loss': 0.1,  # 월간 최대 손실 10%
                    'max_drawdown': 0.15,  # 최대 드로우다운 15%
                },
                'order_limits': {
                    'max_orders_per_minute': 10,
                    'min_order_amount': 1000,  # 최소 주문 금액
                    'max_order_amount': 10000000  # 최대 주문 금액
                },
                'stop_loss': {
                    'default_stop_loss': 0.05,  # 기본 손절 5%
                    'max_stop_loss': 0.1,  # 최대 손절 10%
                    'trailing_stop': True
                }
            }
        }

        if config_name in default_configs:
            try:
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(default_configs[config_name], f,
                             default_flow_style=False, allow_unicode=True)

                self.config[config_name] = default_configs[config_name]
                self.logger.info(f"[성공] 기본 {config_name}.yaml 파일 생성")

            except Exception as e:
                self.logger.error(f"[실패] 기본 설정 파일 생성 실패: {str(e)}")

    def _initialize_mongodb(self):
        """MongoDB 연결 초기화"""
        try:
            # MongoDB 설정 가져오기
            mongodb_config = self.config.get('api_credentials', {}).get('mongodb', {})

            # 연결 문자열 구성
            if mongodb_config.get('username') and mongodb_config.get('password'):
                connection_string = (
                    f"mongodb://{mongodb_config['username']}:{mongodb_config['password']}"
                    f"@{mongodb_config.get('host', 'localhost')}:{mongodb_config.get('port', 27017)}"
                    f"/{mongodb_config.get('auth_database', 'admin')}"
                )
            else:
                connection_string = (
                    f"mongodb://{mongodb_config.get('host', 'localhost')}"
                    f":{mongodb_config.get('port', 27017)}"
                )

            # MongoDB 클라이언트 생성
            self.mongodb_client = pymongo.MongoClient(
                connection_string,
                serverSelectionTimeoutMS=5000  # 5초 타임아웃
            )

            # 연결 테스트
            self.mongodb_client.admin.command('ismaster')
            self.logger.info("[성공] MongoDB 연결 성공")

            # 사용 가능한 데이터베이스 확인
            self._check_available_databases()

        except Exception as e:
            self.logger.error(f"[실패] MongoDB 연결 실패: {str(e)}")
            self.mongodb_client = None

    def _check_available_databases(self):
        """사용 가능한 데이터베이스 확인"""
        if not self.mongodb_client:
            return

        try:
            database_names = self.mongodb_client.list_database_names()
            self.logger.info(f"[정보] 사용 가능한 데이터베이스: {database_names}")

            # 주요 데이터베이스 존재 확인
            required_databases = ['NasDataBase_D', 'NysDataBase_D']
            available_databases = []

            for db_name in required_databases:
                if db_name in database_names:
                    available_databases.append(db_name)
                    db = self.mongodb_client[db_name]
                    collections = db.list_collection_names()
                    self.logger.info(f"[정보] {db_name}: {len(collections)} 개 컬렉션")

            if available_databases:
                self.logger.info(f"[성공] 백테스트 가능한 데이터베이스: {available_databases}")
            else:
                self.logger.warning("[경고] 백테스트용 데이터베이스를 찾을 수 없습니다")

        except Exception as e:
            self.logger.error(f"[실패] 데이터베이스 확인 실패: {str(e)}")

    def get_mongodb_client(self) -> Optional[pymongo.MongoClient]:
        """MongoDB 클라이언트 반환"""
        return self.mongodb_client

    def get_config(self, config_name: str) -> Dict[str, Any]:
        """설정 정보 반환"""
        return self.config.get(config_name, {})

    def get_database_info(self) -> Dict[str, Any]:
        """데이터베이스 정보 반환"""
        if not self.mongodb_client:
            return {'status': 'disconnected', 'databases': []}

        try:
            database_names = self.mongodb_client.list_database_names()
            database_info = {}

            for db_name in database_names:
                if 'DataBase' in db_name:  # NasDataBase_D, NysDataBase_D 등
                    db = self.mongodb_client[db_name]
                    collections = db.list_collection_names()
                    database_info[db_name] = {
                        'collection_count': len(collections),
                        'sample_collections': collections[:5]  # 처음 5개만
                    }

            return {
                'status': 'connected',
                'total_databases': len(database_names),
                'trading_databases': database_info
            }

        except Exception as e:
            self.logger.error(f"[실패] 데이터베이스 정보 조회 실패: {str(e)}")
            return {'status': 'error', 'error': str(e)}

    def validate_system_health(self) -> Dict[str, Any]:
        """시스템 상태 검증"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'mongodb': {'status': 'unknown'},
            'configs': {'loaded': 0, 'total': 4},
            'overall': 'unknown'
        }

        # MongoDB 상태 확인
        try:
            if self.mongodb_client:
                self.mongodb_client.admin.command('ismaster')
                health_status['mongodb'] = {'status': 'healthy'}
            else:
                health_status['mongodb'] = {'status': 'disconnected'}
        except Exception as e:
            health_status['mongodb'] = {'status': 'error', 'error': str(e)}

        # 설정 파일 상태 확인
        required_configs = ['api_credentials', 'broker_config', 'agent_model', 'risk_management']
        loaded_configs = sum(1 for config in required_configs if config in self.config)
        health_status['configs'] = {
            'loaded': loaded_configs,
            'total': len(required_configs),
            'missing': [config for config in required_configs if config not in self.config]
        }

        # 전체 상태 결정
        if health_status['mongodb']['status'] == 'healthy' and loaded_configs == len(required_configs):
            health_status['overall'] = 'healthy'
        elif health_status['mongodb']['status'] == 'healthy' or loaded_configs > 0:
            health_status['overall'] = 'partial'
        else:
            health_status['overall'] = 'unhealthy'

        return health_status

    def get_risk_limits(self) -> Dict[str, Any]:
        """리스크 관리 설정 반환"""
        return self.get_config('risk_management')

    def get_broker_config(self) -> Dict[str, Any]:
        """브로커 설정 반환"""
        return self.get_config('broker_config')

    def get_model_config(self, agent_name: str) -> Dict[str, str]:
        """특정 에이전트의 모델 설정 반환"""
        agent_models = self.get_config('agent_model').get('agents', {})
        return agent_models.get(agent_name, {
            'primary_model': 'claude-3-sonnet-20240229',
            'fallback_model': 'claude-3-haiku-20240307'
        })

    def get_all_stock_symbols(self, limit_per_market: int = None) -> Dict[str, List[str]]:
        """MongoDB에서 모든 주식 심볼 조회"""
        if not self.mongodb_client:
            self.logger.error("[실패] MongoDB 연결이 없습니다")
            return {'NASDAQ': [], 'NYSE': []}

        try:
            result = {'NASDAQ': [], 'NYSE': []}

            # NasDataBase_D (NASDAQ) 심볼 조회
            try:
                nas_db = self.mongodb_client['NasDataBase_D']
                nas_collections = nas_db.list_collection_names()
                # 컬렉션 이름에서 심볼 추출 (일반적으로 컬렉션 이름이 심볼명)
                nasdaq_symbols = [col for col in nas_collections if col.replace('_', '').replace('-', '').isalnum()]

                if limit_per_market and len(nasdaq_symbols) > limit_per_market:
                    nasdaq_symbols = nasdaq_symbols[:limit_per_market]

                result['NASDAQ'] = nasdaq_symbols
                self.logger.info(f"[성공] NASDAQ 심볼 {len(nasdaq_symbols)}개 조회")

            except Exception as e:
                self.logger.warning(f"[경고] NASDAQ 데이터베이스 조회 실패: {str(e)}")

            # NysDataBase_D (NYSE) 심볼 조회
            try:
                nys_db = self.mongodb_client['NysDataBase_D']
                nys_collections = nys_db.list_collection_names()
                # 컬렉션 이름에서 심볼 추출
                nyse_symbols = [col for col in nys_collections if col.replace('_', '').replace('-', '').isalnum()]

                if limit_per_market and len(nyse_symbols) > limit_per_market:
                    nyse_symbols = nyse_symbols[:limit_per_market]

                result['NYSE'] = nyse_symbols
                self.logger.info(f"[성공] NYSE 심볼 {len(nyse_symbols)}개 조회")

            except Exception as e:
                self.logger.warning(f"[경고] NYSE 데이터베이스 조회 실패: {str(e)}")

            total_symbols = len(result['NASDAQ']) + len(result['NYSE'])
            self.logger.info(f"[성공] 총 {total_symbols}개 심볼 조회 완료")

            return result

        except Exception as e:
            self.logger.error(f"[실패] 주식 심볼 조회 실패: {str(e)}")
            return {'NASDAQ': [], 'NYSE': []}

    def log_agent_action(self, agent_name: str, action: str, details: Dict[str, Any] = None):
        """에이전트 작업 로깅"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': agent_name,
            'action': action,
            'details': details or {}
        }

        self.logger.info(f"[{agent_name}] {action}: {details}")

        # 향후 확장: 데이터베이스에 로그 저장
        # self._save_log_to_database(log_entry)

    def cleanup_connections(self):
        """연결 정리"""
        try:
            if self.mongodb_client:
                self.mongodb_client.close()
                self.logger.info("[성공] MongoDB 연결 정리 완료")
        except Exception as e:
            self.logger.error(f"[실패] 연결 정리 실패: {str(e)}")

    def __del__(self):
        """소멸자 - 연결 정리"""
        self.cleanup_connections()

def test_helper_agent():
    """Helper Agent 테스트"""
    print("\n=== Helper Agent 테스트 시작 ===")

    try:
        # Helper Agent 인스턴스 생성
        helper = HelperAgent()

        # 시스템 상태 확인
        print("\n1. 시스템 상태 확인:")
        health = helper.validate_system_health()
        print(f"   전체 상태: {health['overall']}")
        print(f"   MongoDB: {health['mongodb']['status']}")
        print(f"   설정 파일: {health['configs']['loaded']}/{health['configs']['total']}")

        # 데이터베이스 정보 확인
        print("\n2. 데이터베이스 정보:")
        db_info = helper.get_database_info()
        print(f"   상태: {db_info['status']}")
        if 'trading_databases' in db_info:
            for db_name, info in db_info['trading_databases'].items():
                print(f"   {db_name}: {info['collection_count']} 컬렉션")

        # 설정 정보 확인
        print("\n3. 설정 정보 확인:")
        risk_config = helper.get_risk_limits()
        if risk_config:
            print("   리스크 관리 설정 로드됨")

        model_config = helper.get_model_config('orchestrator')
        print(f"   오케스트레이터 모델: {model_config.get('primary_model', 'N/A')}")

        # 작업 로깅 테스트
        print("\n4. 로깅 테스트:")
        helper.log_agent_action('test_agent', 'system_check', {'status': 'completed'})

        print("\n=== Helper Agent 테스트 완료 ===")

    except Exception as e:
        print(f"[실패] Helper Agent 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_helper_agent()