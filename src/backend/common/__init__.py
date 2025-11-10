"""
Backend Common Module

Worker 환경에서는 backend_config.py를 config로 alias하여 사용
"""
import sys
import os

# Worker 환경 감지: backend_config.py가 존재하면 Worker 컨테이너
if os.path.exists('/app/backend_config.py'):
    # Worker 환경: backend_config를 config로 alias
    import backend_config
    sys.modules['config'] = backend_config
    
    # 기존 config.py가 있다면 worker_config로 백업
    try:
        import config as worker_config
        sys.modules['worker_config'] = worker_config
    except ImportError:
        pass
