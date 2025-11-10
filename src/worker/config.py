"""
Worker Configuration Module

환경변수 기반 자동 provider 선택 및 설정 관리
PDD v4.0 - AWS Bedrock 우선 사용
"""
import os
from typing import Dict, Any, Optional


class EmbeddingConfig:
    """임베딩 생성 설정

    환경변수 USE_BEDROCK에 따라 자동으로 provider 선택:
    - USE_BEDROCK=true → AWS Bedrock Titan Embeddings
    - USE_BEDROCK=false → OpenAI Embeddings (Fallback)
    """

    @staticmethod
    def get_provider() -> Dict[str, Any]:
        """환경변수 기반 provider 선택

        Returns:
            {
                'provider': 'bedrock' | 'openai',
                'model_id': str,
                'region': str (Bedrock 전용),
                'api_key': str (OpenAI 전용)
            }
        """
        use_bedrock = os.environ.get('USE_BEDROCK', 'false').lower() == 'true'

        if use_bedrock:
            return {
                'provider': 'bedrock',
                'model_id': os.environ.get(
                    'BEDROCK_EMBEDDING_MODEL_ID',
                    'amazon.titan-embed-text-v1'
                ),
                'region': os.environ.get('AWS_REGION', 'us-east-1'),
                's3_cache_bucket': os.environ.get('S3_EMBEDDING_CACHE_BUCKET')
            }
        else:
            return {
                'provider': 'openai',
                'api_key': os.environ.get('OPENAI_API_KEY'),
                'model': os.environ.get('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
            }

    @staticmethod
    def is_bedrock_enabled() -> bool:
        """Bedrock 사용 여부 확인"""
        return os.environ.get('USE_BEDROCK', 'false').lower() == 'true'


class LLMConfig:
    """LLM 호출 설정

    환경변수 USE_BEDROCK에 따라 자동으로 provider 선택:
    - USE_BEDROCK=true → AWS Bedrock Claude 3.5 Sonnet
    - USE_BEDROCK=false → OpenAI GPT-4o (Fallback)
    """

    @staticmethod
    def get_provider() -> Dict[str, Any]:
        """환경변수 기반 LLM provider 선택

        Returns:
            {
                'provider': 'bedrock' | 'openai',
                'model_id': str,
                'region': str (Bedrock 전용),
                'max_tokens': int,
                'temperature': float,
                'api_key': str (OpenAI 전용)
            }
        """
        use_bedrock = os.environ.get('USE_BEDROCK', 'false').lower() == 'true'

        if use_bedrock:
            return {
                'provider': 'bedrock',
                'model_id': os.environ.get(
                    'BEDROCK_LLM_MODEL_ID',
                    'anthropic.claude-3-5-sonnet-20241022-v2:0'
                ),
                'region': os.environ.get('AWS_REGION', 'us-east-1'),
                'max_tokens': int(os.environ.get('LLM_MAX_TOKENS', 4096)),
                'temperature': float(os.environ.get('LLM_TEMPERATURE', 0.0))
            }
        else:
            return {
                'provider': 'openai',
                'api_key': os.environ.get('OPENAI_API_KEY'),
                'model': os.environ.get('OPENAI_LLM_MODEL', 'gpt-4o'),
                'max_tokens': int(os.environ.get('LLM_MAX_TOKENS', 4096)),
                'temperature': float(os.environ.get('LLM_TEMPERATURE', 0.0))
            }

    @staticmethod
    def is_bedrock_enabled() -> bool:
        """Bedrock 사용 여부 확인"""
        return os.environ.get('USE_BEDROCK', 'false').lower() == 'true'


class AWSConfig:
    """AWS 서비스 공통 설정"""

    @staticmethod
    def get_region() -> str:
        """AWS 리전 반환"""
        return os.environ.get('AWS_REGION', 'us-east-1')

    @staticmethod
    def get_credentials() -> Optional[Dict[str, str]]:
        """AWS 자격 증명 반환

        환경변수에 명시적으로 설정된 경우에만 반환.
        없으면 None → boto3가 IAM Role 또는 ~/.aws/credentials 사용
        """
        access_key = os.environ.get('AWS_ACCESS_KEY_ID')
        secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY')

        if access_key and secret_key:
            return {
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key
            }

        return None

    @staticmethod
    def validate_credentials() -> bool:
        """AWS 자격 증명 유효성 검증"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # STS GetCallerIdentity로 자격 증명 확인
            sts = boto3.client('sts', region_name=AWSConfig.get_region())
            response = sts.get_caller_identity()

            print(f"✅ AWS 인증 성공: Account={response['Account']}, ARN={response['Arn']}")
            return True

        except (ClientError, NoCredentialsError) as e:
            print(f"❌ AWS 인증 실패: {e}")
            return False
        except ImportError:
            print("⚠️  boto3가 설치되지 않음")
            return False


# 전역 설정 객체 (편의성)
embedding_config = EmbeddingConfig()
llm_config = LLMConfig()
aws_config = AWSConfig()
