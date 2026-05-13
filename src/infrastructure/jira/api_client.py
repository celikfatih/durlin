from jira import JIRA
from jira.exceptions import JIRAError
from src.domain.ports.jira import JiraProvider
from src.core.exceptions import JiraConnectionError
import typing

class JiraAPIClient(JiraProvider):
    def __init__(self, server_url: str, user_email: str, api_token: str):
        try:
            self.client = JIRA(
                server=server_url,
                basic_auth=(user_email, api_token)
            )
            self.dev_status_detail_url = f"{server_url}/rest/dev-status/1.0/issue/detail"
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
        result: typing.Dict[str, typing.Any] = {'commits': [], 'pullrequests': [], 'branches': []}
        data_types = [
            ('repository', 'commits'),
            ('pullrequest', 'pullrequests'), 
            ('branch', 'branches')           
        ]
        
        for data_type, result_key in data_types:
            params = {'issueId': issue_id, 'applicationType': 'GitHub', 'dataType': data_type}
            try:
                response = self.client._session.get(self.dev_status_detail_url, params=params) # type: ignore
                response.raise_for_status()
                data = response.json()
                result[result_key] = data
            except Exception as e:
                pass # Just skip if we can't fetch a specific type
                
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
