"""
AWS Batch + Step Functions 기반 TaskService 구현

Phase 3에서 AWS 인프라 구축 후 활성화
현재는 인터페이스만 제공
"""
import os
import json
from typing import Optional
from uuid import UUID

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from .base import ITaskService


class AwsBatchTaskService(ITaskService):
    """
    AWS Batch + Step Functions를 사용한 분석 작업 실행

    Environment Variables:
        - AWS_REGION: AWS 리전 (default: us-east-1)
        - STEP_FUNCTIONS_ARN: Step Functions State Machine ARN
        - SQS_QUEUE_URL: SQS Queue URL
        - AWS_BATCH_JOB_QUEUE: Batch Job Queue 이름
        - AWS_BATCH_JOB_DEFINITION: Batch Job Definition 이름
    """

    def __init__(self):
        if not AWS_AVAILABLE:
            raise RuntimeError(
                "AWS SDK (boto3) not installed. "
                "Install with: pip install boto3"
            )

        self.region = os.environ.get('AWS_REGION', 'us-east-1')
        self.sfn_arn = os.environ.get('STEP_FUNCTIONS_ARN')
        self.sqs_url = os.environ.get('SQS_QUEUE_URL')
        self.batch_queue = os.environ.get('AWS_BATCH_JOB_QUEUE')
        self.batch_job_def = os.environ.get('AWS_BATCH_JOB_DEFINITION')

        # AWS 클라이언트 초기화
        self.sfn_client = boto3.client('stepfunctions', region_name=self.region)
        self.sqs_client = boto3.client('sqs', region_name=self.region)
        self.batch_client = boto3.client('batch', region_name=self.region)

        # 환경변수 검증
        self._validate_config()

    def _validate_config(self):
        """필수 환경변수 검증"""
        missing = []
        if not self.sfn_arn:
            missing.append('STEP_FUNCTIONS_ARN')
        if not self.sqs_url:
            missing.append('SQS_QUEUE_URL')
        if not self.batch_queue:
            missing.append('AWS_BATCH_JOB_QUEUE')
        if not self.batch_job_def:
            missing.append('AWS_BATCH_JOB_DEFINITION')

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

    async def enqueue_analysis(
        self,
        analysis_id: UUID,
        repo_url: str,
        target_user: str,
        access_token: Optional[str] = None,
        branch: str = "main"
    ) -> str:
        """
        Step Functions 실행 시작

        Args:
            analysis_id: 분석 작업 ID
            repo_url: GitHub 저장소 URL
            target_user: 분석 대상 사용자
            access_token: GitHub Personal Access Token (암호화됨)
            branch: 분석 대상 브랜치

        Returns:
            Step Functions execution ARN
        """
        payload = {
            'analysis_id': str(analysis_id),
            'repo_url': repo_url,
            'target_user': target_user,
            'access_token': access_token,
            'branch': branch,
            'batch_job_queue': self.batch_queue,
            'batch_job_definition': self.batch_job_def
        }

        try:
            # Step Functions 실행 시작
            response = self.sfn_client.start_execution(
                stateMachineArn=self.sfn_arn,
                name=f"analysis-{analysis_id}",
                input=json.dumps(payload)
            )

            execution_arn = response['executionArn']
            print(f"✅ Step Functions execution started: {execution_arn}")
            return execution_arn

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            raise RuntimeError(
                f"Failed to start Step Functions execution: {error_code} - {error_msg}"
            )

    async def get_status(self, task_id: str) -> dict:
        """
        Step Functions 실행 상태 조회

        Args:
            task_id: Step Functions execution ARN

        Returns:
            {
                'status': 'RUNNING' | 'SUCCEEDED' | 'FAILED' | 'TIMED_OUT',
                'output': {...},  # SUCCEEDED 시
                'error': '...'    # FAILED 시
            }
        """
        try:
            response = self.sfn_client.describe_execution(
                executionArn=task_id
            )

            status = response['status']
            result = {'status': status}

            if status == 'SUCCEEDED' and 'output' in response:
                result['output'] = json.loads(response['output'])

            if status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
                result['error'] = response.get('error', 'Unknown error')
                if 'cause' in response:
                    result['cause'] = response['cause']

            return result

        except ClientError as e:
            raise RuntimeError(
                f"Failed to get execution status: {e.response['Error']['Message']}"
            )

    async def cancel_task(self, task_id: str) -> bool:
        """
        Step Functions 실행 중단

        Args:
            task_id: Step Functions execution ARN

        Returns:
            성공 여부
        """
        try:
            self.sfn_client.stop_execution(
                executionArn=task_id,
                error='UserCancelled',
                cause='User requested cancellation'
            )
            print(f"✅ Execution cancelled: {task_id}")
            return True

        except ClientError as e:
            print(f"❌ Failed to cancel execution: {e.response['Error']['Message']}")
            return False

    def health_check(self) -> bool:
        """
        AWS 서비스 연결 상태 확인

        Returns:
            모든 서비스 정상 여부
        """
        try:
            # Step Functions 상태 확인
            self.sfn_client.describe_state_machine(
                stateMachineArn=self.sfn_arn
            )

            # SQS Queue 상태 확인
            self.sqs_client.get_queue_attributes(
                QueueUrl=self.sqs_url,
                AttributeNames=['ApproximateNumberOfMessages']
            )

            # Batch Job Queue 상태 확인
            self.batch_client.describe_job_queues(
                jobQueues=[self.batch_queue]
            )

            return True

        except ClientError as e:
            print(f"❌ AWS health check failed: {e.response['Error']['Message']}")
            return False
