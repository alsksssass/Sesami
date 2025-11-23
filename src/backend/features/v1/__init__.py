"""
API v1 Features

이 디렉토리의 모든 feature는 FeatureRouter를 통해 자동으로 등록됩니다.
"""

# 모든 feature를 import하여 FeatureRouter에 자동 등록
from . import auth
from . import github_analysis
from . import webhooks
from . import repo
from . import user

__all__ = ['auth', 'github_analysis', 'webhooks', 'repo', 'user']
