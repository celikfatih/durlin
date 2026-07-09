import logging
import typing
from jira import JIRA
from jira.exceptions import JIRAError
from src.domain.ports.jira import JiraProvider
from src.core.exceptions import JiraConnectionError

logger = logging.getLogger(__name__)

class JiraAPIClient(JiraProvider):
    def __init__(self, server_url: str, user_email: str, api_token: str):
        try:
            self.client = JIRA(
                server=server_url,
                basic_auth=(user_email, api_token)
            )
            self.server_url = server_url.rstrip("/")
            self.dev_status_detail_url = f"{self.server_url}/rest/dev-status/1.0/issue/detail"
            self.dev_status_summary_url = f"{self.server_url}/rest/dev-status/1.0/issue/summary"
        except Exception as e:
            raise JiraConnectionError(f"Failed to initialize Jira client: {str(e)}") from e

    def get_issue_title(self, issue_key: str) -> str:
        try:
            issue = self.client.issue(issue_key, fields="summary")
            return issue.fields.summary # type: ignore
        except JIRAError as e:
            raise JiraConnectionError(f"Failed to fetch issue {issue_key}: {e.text}") from e
        except Exception as e:
            raise JiraConnectionError(f"Unexpected error fetching issue {issue_key}: {str(e)}") from e

    def get_issue(self, issue_key: str) -> dict:
        try:
            issue = self.client.issue(issue_key, fields="summary")
            return {
                "id": issue.id,
                "summary": getattr(issue.fields, "summary", "")
            }
        except JIRAError as e:
            raise JiraConnectionError(f"Failed to fetch issue {issue_key}: {e.text}") from e
        except Exception as e:
            raise JiraConnectionError(f"Unexpected error fetching issue {issue_key}: {str(e)}") from e

    def get_development_links(self, issue_id: str) -> dict:
        result: typing.Dict[str, typing.Any] = {
            'commits': {'errors': [], 'detail': []},
            'pullrequests': {'errors': [], 'detail': []},
            'branches': {'errors': [], 'detail': []}
        }
        data_types = [
            ('repository', 'commits'),
            ('pullrequest', 'pullrequests'), 
            ('branch', 'branches')           
        ]

        # 1. Discover active applicationType / instanceType keys via Dev Status Summary API
        app_types: typing.Set[str] = set()
        try:
            summary_resp = self.client._session.get(self.dev_status_summary_url, params={'issueId': issue_id}) # type: ignore
            if summary_resp.status_code == 200:
                summary_data = summary_resp.json().get('summary', {})
                for dt_val in summary_data.values():
                    if isinstance(dt_val, dict):
                        by_instance = dt_val.get('byInstanceType', {})
                        if isinstance(by_instance, dict):
                            for key in by_instance.keys():
                                app_types.add(key)
        except Exception as e:
            logger.debug(f"Could not fetch dev-status summary for issue {issue_id}: {e}")

        # 2. Fall back to standard application types if summary yielded no types
        if not app_types:
            app_types = {
                'oAuth-com.github.integration.production',
                'GitHub',
                'github',
                'fecru',
                'bitbucket',
                'gitlab'
            }

        logger.debug(f"Querying Jira Dev-Status details for issue {issue_id} using applicationTypes: {app_types}")

        # 3. Fetch details across all discovered application types
        for data_type, result_key in data_types:
            for app_type in app_types:
                params = {'issueId': issue_id, 'applicationType': app_type, 'dataType': data_type}
                try:
                    response = self.client._session.get(self.dev_status_detail_url, params=params) # type: ignore
                    response.raise_for_status()
                    data = response.json()
                    details = data.get('detail', [])
                    if details:
                        result[result_key]['detail'].extend(details)
                except Exception as e:
                    logger.debug(f"Could not fetch {data_type} for applicationType {app_type}: {e}")
                
        return result

    def _md_to_jira(self, md: str) -> str:
        """Convert Markdown to Jira Wiki Markup."""
        import re
        lines = md.split("\n")
        output = []
        for line in lines:
            # Headings: ## -> h2. ### -> h3.
            line = re.sub(r'^######\s+', 'h6. ', line)
            line = re.sub(r'^#####\s+', 'h5. ', line)
            line = re.sub(r'^####\s+', 'h4. ', line)
            line = re.sub(r'^###\s+', 'h3. ', line)
            line = re.sub(r'^##\s+', 'h2. ', line)
            line = re.sub(r'^#\s+', 'h1. ', line)
            # Horizontal rule
            line = re.sub(r'^---+$', '----', line)
            # Bold: **text** -> *text*
            line = re.sub(r'\*\*(.+?)\*\*', r'*\1*', line)
            # Italic: _text_ or *text* -> _text_
            line = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', line)
            # Inline code: `code` -> {{code}}
            line = re.sub(r'`([^`]+)`', r'{{\1}}', line)
            # Unordered list: - item or * item -> * item (Jira uses *)
            line = re.sub(r'^\s*[-*]\s+', '* ', line)
            # Numbered list: 1. item -> # item
            line = re.sub(r'^\s*\d+\.\s+', '# ', line)
            # Sub-list items (indented): keep as-is (Jira auto-nests with ** or ##)
            output.append(line)
        return "\n".join(output)

    def add_comment(self, issue_key: str, comment: str) -> None:
        try:
            jira_markup = self._md_to_jira(comment)
            self.client.add_comment(issue_key, jira_markup)
        except JIRAError as e:
            raise JiraConnectionError(f"Failed to add comment to {issue_key}: {e.text}") from e
        except Exception as e:
            raise JiraConnectionError(f"Unexpected error adding comment to {issue_key}: {str(e)}") from e
