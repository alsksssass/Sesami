"""
GitHub 분석 기능 데이터베이스 모델
공통 모델은 shared.models에서 import
"""

# Shared 모듈에서 공통 모델 import
from shared.models import Analysis, AnalysisState

# 모듈 외부에서 import 가능하도록 export
__all__ = ["Analysis", "AnalysisState"]
