"""
Documentation Manager

오케스트레이터 에이전트가 사용하는 계층적 문서 관리 시스템
모든 에이전트의 문서를 로드하고 검색할 수 있는 기능 제공

버전: 2.0
작성일: 2025-09-26
"""

import os
import yaml
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
import glob
import re


class DocumentationManager:
    """계층적 문서 관리 시스템"""

    def __init__(self, project_root: str = None):
        self.logger = logging.getLogger(__name__)

        # 프로젝트 루트 설정
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.docs_root = self.project_root / "docs"

        # 에이전트별 문서 디렉토리 매핑
        self.agent_docs_map = {
            "orchestrator": self.docs_root / "orchestrator",
            "data_agent": self.docs_root / "data_agent",
            "strategy_agent": self.docs_root / "strategy_agent",
            "service_agent": self.docs_root / "service_agent",
            "helper_agent": self.docs_root / "helper_agent"
        }

        # 캐시된 문서 내용
        self._docs_cache = {}
        self._cache_timestamp = {}

        # 문서 색인
        self._docs_index = {}

        self.logger.info(f"[DocumentationManager] 초기화 완료 - 문서 루트: {self.docs_root}")

    def load_all_documentation(self) -> Dict[str, Dict[str, str]]:
        """모든 문서 로드"""
        try:
            all_docs = {}

            # 루트 문서들 로드
            all_docs["system"] = self._load_directory_docs(self.docs_root, max_depth=1)

            # 에이전트별 문서 로드
            for agent_name, agent_docs_path in self.agent_docs_map.items():
                if agent_docs_path.exists():
                    all_docs[agent_name] = self._load_directory_docs(agent_docs_path)
                else:
                    self.logger.warning(f"[DocumentationManager] {agent_name} 문서 디렉토리 없음: {agent_docs_path}")
                    all_docs[agent_name] = {}

            # 배포 문서 로드
            deployment_path = self.docs_root / "deployment"
            if deployment_path.exists():
                all_docs["deployment"] = self._load_directory_docs(deployment_path)
            else:
                all_docs["deployment"] = {}

            self.logger.info(f"[DocumentationManager] 전체 문서 로드 완료: {len(all_docs)} 카테고리")
            return all_docs

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 전체 문서 로드 실패: {e}")
            return {}

    def load_agent_documentation(self, agent_name: str) -> Dict[str, str]:
        """특정 에이전트의 문서 로드"""
        try:
            if agent_name not in self.agent_docs_map:
                self.logger.error(f"[DocumentationManager] 알 수 없는 에이전트: {agent_name}")
                return {}

            agent_docs_path = self.agent_docs_map[agent_name]

            if not agent_docs_path.exists():
                self.logger.warning(f"[DocumentationManager] {agent_name} 문서 디렉토리 없음")
                return {}

            docs = self._load_directory_docs(agent_docs_path)
            self.logger.info(f"[DocumentationManager] {agent_name} 문서 로드 완료: {len(docs)} 파일")
            return docs

        except Exception as e:
            self.logger.error(f"[DocumentationManager] {agent_name} 문서 로드 실패: {e}")
            return {}

    def _load_directory_docs(self, directory: Path, max_depth: int = None) -> Dict[str, str]:
        """디렉토리 내 모든 마크다운 파일 로드"""
        docs = {}

        if not directory.exists():
            return docs

        # 패턴 설정
        if max_depth == 1:
            pattern = "*.md"
        else:
            pattern = "**/*.md"

        try:
            for md_file in directory.glob(pattern):
                if md_file.is_file():
                    # 상대 경로를 키로 사용
                    relative_path = md_file.relative_to(directory)
                    key = str(relative_path).replace('\\', '/').replace('.md', '')

                    # 파일 내용 읽기 (캐시 확인)
                    content = self._read_file_with_cache(md_file)
                    if content:
                        docs[key] = content

            return docs

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 디렉토리 문서 로드 실패 {directory}: {e}")
            return {}

    def _read_file_with_cache(self, file_path: Path) -> Optional[str]:
        """파일을 캐시와 함께 읽기"""
        try:
            file_key = str(file_path)
            file_mtime = file_path.stat().st_mtime

            # 캐시 확인
            if (file_key in self._docs_cache and
                file_key in self._cache_timestamp and
                self._cache_timestamp[file_key] >= file_mtime):
                return self._docs_cache[file_key]

            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 캐시 저장
            self._docs_cache[file_key] = content
            self._cache_timestamp[file_key] = file_mtime

            return content

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 파일 읽기 실패 {file_path}: {e}")
            return None

    def search_documentation(self, query: str, agent: str = None) -> List[Dict[str, Any]]:
        """문서 내용 검색"""
        try:
            results = []
            query_lower = query.lower()

            # 검색 대상 결정
            if agent:
                if agent in self.agent_docs_map:
                    docs_to_search = {agent: self.load_agent_documentation(agent)}
                else:
                    self.logger.warning(f"[DocumentationManager] 알 수 없는 에이전트: {agent}")
                    return []
            else:
                docs_to_search = self.load_all_documentation()

            # 검색 실행
            for category, docs in docs_to_search.items():
                for doc_name, content in docs.items():
                    # 제목에서 검색
                    title_match = query_lower in doc_name.lower()

                    # 내용에서 검색
                    content_matches = []
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if query_lower in line.lower():
                            content_matches.append({
                                'line_number': i + 1,
                                'line': line.strip(),
                                'context': self._get_context(lines, i)
                            })

                    if title_match or content_matches:
                        results.append({
                            'category': category,
                            'document': doc_name,
                            'title_match': title_match,
                            'content_matches': content_matches,
                            'file_path': f"docs/{category}/{doc_name}.md" if category != "system" else f"docs/{doc_name}.md"
                        })

            self.logger.info(f"[DocumentationManager] 검색 완료 '{query}': {len(results)} 결과")
            return results

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 문서 검색 실패: {e}")
            return []

    def _get_context(self, lines: List[str], line_index: int, context_size: int = 2) -> List[str]:
        """검색된 라인의 앞뒤 컨텍스트 가져오기"""
        start = max(0, line_index - context_size)
        end = min(len(lines), line_index + context_size + 1)
        return lines[start:end]

    def get_document_metadata(self, doc_path: str) -> Dict[str, Any]:
        """문서 메타데이터 추출"""
        try:
            # 파일 경로 구성
            if doc_path.startswith('docs/'):
                full_path = self.project_root / doc_path
            else:
                full_path = self.docs_root / doc_path

            if not full_path.exists():
                return {}

            content = self._read_file_with_cache(full_path)
            if not content:
                return {}

            # 헤더에서 메타데이터 추출
            metadata = {}
            lines = content.split('\n')

            for line in lines[:20]:  # 첫 20줄만 확인
                if line.startswith('**Version**:'):
                    metadata['version'] = line.split(':', 1)[1].strip()
                elif line.startswith('**Last Updated**:'):
                    metadata['last_updated'] = line.split(':', 1)[1].strip()
                elif line.startswith('**Managed by**:'):
                    metadata['managed_by'] = line.split(':', 1)[1].strip()

            # 파일 정보 추가
            file_stat = full_path.stat()
            metadata.update({
                'file_size': file_stat.st_size,
                'modified_time': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                'file_path': str(full_path.relative_to(self.project_root))
            })

            return metadata

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 메타데이터 추출 실패 {doc_path}: {e}")
            return {}

    def validate_document_links(self) -> Dict[str, Any]:
        """문서 간 링크 유효성 검사"""
        try:
            validation_results = {
                'valid_links': 0,
                'broken_links': 0,
                'broken_link_details': []
            }

            all_docs = self.load_all_documentation()

            # 마크다운 링크 패턴
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'

            for category, docs in all_docs.items():
                for doc_name, content in docs.items():
                    matches = re.findall(link_pattern, content)

                    for link_text, link_url in matches:
                        # 상대 링크만 검사 (http로 시작하지 않는 것)
                        if not link_url.startswith('http'):
                            # 링크 경로 해석
                            if category == "system":
                                base_path = self.docs_root
                            else:
                                base_path = self.agent_docs_map[category]

                            target_path = (base_path / link_url).resolve()

                            if target_path.exists():
                                validation_results['valid_links'] += 1
                            else:
                                validation_results['broken_links'] += 1
                                validation_results['broken_link_details'].append({
                                    'source_doc': f"{category}/{doc_name}",
                                    'link_text': link_text,
                                    'link_url': link_url,
                                    'resolved_path': str(target_path)
                                })

            self.logger.info(f"[DocumentationManager] 링크 검증 완료 - 유효: {validation_results['valid_links']}, 깨진: {validation_results['broken_links']}")
            return validation_results

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 링크 검증 실패: {e}")
            return {'valid_links': 0, 'broken_links': 0, 'broken_link_details': []}

    def get_documentation_structure(self) -> Dict[str, Any]:
        """문서 구조 트리 생성"""
        try:
            structure = {
                'root': str(self.docs_root),
                'categories': {}
            }

            # 시스템 문서 (루트 레벨)
            system_files = list(self.docs_root.glob('*.md'))
            structure['categories']['system'] = {
                'path': str(self.docs_root),
                'files': [f.name for f in system_files]
            }

            # 에이전트별 문서
            for agent_name, agent_path in self.agent_docs_map.items():
                if agent_path.exists():
                    files = list(agent_path.glob('**/*.md'))
                    structure['categories'][agent_name] = {
                        'path': str(agent_path),
                        'files': [str(f.relative_to(agent_path)) for f in files]
                    }
                else:
                    structure['categories'][agent_name] = {
                        'path': str(agent_path),
                        'files': [],
                        'status': 'not_exists'
                    }

            # 배포 문서
            deployment_path = self.docs_root / "deployment"
            if deployment_path.exists():
                files = list(deployment_path.glob('**/*.md'))
                structure['categories']['deployment'] = {
                    'path': str(deployment_path),
                    'files': [str(f.relative_to(deployment_path)) for f in files]
                }

            return structure

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 구조 생성 실패: {e}")
            return {}

    def update_document(self, doc_path: str, content: str, agent: str) -> bool:
        """문서 내용 업데이트 (권한 확인 포함)"""
        try:
            # 권한 확인
            if not self._check_write_permission(doc_path, agent):
                self.logger.error(f"[DocumentationManager] 쓰기 권한 없음 - 에이전트: {agent}, 문서: {doc_path}")
                return False

            # 파일 경로 구성
            if doc_path.startswith('docs/'):
                full_path = self.project_root / doc_path
            else:
                full_path = self.docs_root / doc_path

            # 디렉토리 생성
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # 백업 생성
            if full_path.exists():
                backup_path = full_path.with_suffix('.md.bak')
                import shutil
                shutil.copy2(full_path, backup_path)

            # 파일 쓰기
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 캐시 무효화
            file_key = str(full_path)
            if file_key in self._docs_cache:
                del self._docs_cache[file_key]
            if file_key in self._cache_timestamp:
                del self._cache_timestamp[file_key]

            self.logger.info(f"[DocumentationManager] 문서 업데이트 완료: {doc_path}")
            return True

        except Exception as e:
            self.logger.error(f"[DocumentationManager] 문서 업데이트 실패 {doc_path}: {e}")
            return False

    def _check_write_permission(self, doc_path: str, agent: str) -> bool:
        """문서 쓰기 권한 확인"""
        # 권한 규칙 (FILE_PERMISSIONS.md 기반)
        permission_rules = {
            "orchestrator": [
                "docs/",
                "docs/orchestrator/",
                "docs/deployment/"
            ],
            "data_agent": [
                "docs/data_agent/"
            ],
            "strategy_agent": [
                "docs/strategy_agent/"
            ],
            "service_agent": [
                "docs/service_agent/"
            ],
            "helper_agent": [
                "docs/helper_agent/"
            ]
        }

        if agent not in permission_rules:
            return False

        allowed_paths = permission_rules[agent]

        for allowed_path in allowed_paths:
            if doc_path.startswith(allowed_path):
                return True

        return False

    def clear_cache(self):
        """문서 캐시 정리"""
        self._docs_cache.clear()
        self._cache_timestamp.clear()
        self.logger.info("[DocumentationManager] 문서 캐시 정리 완료")


# 사용 예제
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # DocumentationManager 초기화
    doc_manager = DocumentationManager()

    # 전체 문서 구조 출력
    print("=== 문서 구조 ===")
    structure = doc_manager.get_documentation_structure()
    print(json.dumps(structure, indent=2, ensure_ascii=False))

    # 특정 에이전트 문서 로드
    print("\n=== Orchestrator 문서 ===")
    orchestrator_docs = doc_manager.load_agent_documentation("orchestrator")
    for doc_name in orchestrator_docs.keys():
        print(f"- {doc_name}")

    # 문서 검색
    print("\n=== 'WebSocket' 검색 결과 ===")
    search_results = doc_manager.search_documentation("WebSocket")
    for result in search_results:
        print(f"- {result['category']}/{result['document']}: {len(result['content_matches'])} 매치")

    # 링크 유효성 검사
    print("\n=== 링크 검증 ===")
    validation = doc_manager.validate_document_links()
    print(f"유효한 링크: {validation['valid_links']}")
    print(f"깨진 링크: {validation['broken_links']}")