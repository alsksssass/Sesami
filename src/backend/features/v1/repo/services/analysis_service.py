from sqlalchemy.orm import Session
from fastapi import Depends

from uuid import UUID

from features.v1.repo.schemas import RepositoryAnalysisResponse
from features.v1.repo.models import RepositoryAnalysis
from config import settings

from datetime import datetime

class AnalysisService():
    def __init__(self, db: Session, batch_client):
        self.db = db
        self.client = batch_client

    def get_latest_job_definition(self, job_definition_name: str) -> str:
        """주어진 이름의 최신 ACTIVE Job Definition ARN을 가져옵니다"""
        response = self.client.describe_job_definitions(
            jobDefinitionName=job_definition_name,
            status='ACTIVE'
        )

        if not response.get('jobDefinitions'):
            raise ValueError(f"No ACTIVE job definition found for {job_definition_name}")

        # revision 기준으로 내림차순 정렬하여 최신 버전 가져오기
        latest = sorted(response['jobDefinitions'],
                       key=lambda x: x['revision'],
                       reverse=True)[0]

        return latest['jobDefinitionArn']

    def request_analysis(self, user_id: UUID, urls: list[str], analysis_id: UUID, repo_ids: list[UUID]):
        jobName = 'deep-agents-' + datetime.now().strftime("%Y%m%d-%H%M%S")

        # 최신 ACTIVE Job Definition 가져오기
        job_def_arn = self.get_latest_job_definition(settings.JOB_DEFINITION)

        response = self.client.submit_job(jobName=jobName, jobQueue='deep-agents-queue',
            jobDefinition=job_def_arn,
            containerOverrides={
                'environment': [
                    {
                        'name': 'GIT_URLS',
                        'value': ','.join(urls)
                    },
                    {
                        'name': 'USER_ID',
                        'value': str(user_id)
                    },
                    {
                        'name': 'MAIN_TASK_ID',
                        'value': str(analysis_id)
                    },
                    {
                        'name': 'TASK_IDS',
                        'value': ','.join(str(repo_id) for repo_id in repo_ids)
                    }
                ]
            }
        )

        return response