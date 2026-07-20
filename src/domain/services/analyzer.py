import logging
from src.domain.ports.git import GitProvider
from src.domain.ports.jira import JiraProvider
from src.domain.ports.ai import AIProvider
from src.infrastructure.git.github_http import GitHubHTTPProvider
import typing

logger = logging.getLogger(__name__)

class DiffAnalyzerService:
    """
    Orchestrates the process of reading a git diff, fetching Jira task context,
    generating an AI comment, and posting it back to Jira.
    """
    def __init__(
        self, 
        git_provider: GitProvider, 
        jira_provider: JiraProvider, 
        ai_provider: AIProvider
    ):
        self.git = git_provider
        self.jira = jira_provider
        self.ai = ai_provider

    def analyze_and_comment(
        self,
        issue_key: str,
        git_references: typing.Optional[typing.List[str]] = None,
        base_branch: typing.Optional[str] = None,
        extra_prompt: typing.Optional[str] = None,
        dry_run: bool = False,
    ) -> str:
        """
        Executes the analysis pipeline.

        Args:
            issue_key:      The target Jira issue key (e.g., PROJ-123).
            git_references: Optional list of GitHub URLs to diff (PR, commit, or compare).
                            Can span multiple repositories. If None, auto-discovers via Jira
                            Dev Status API.
            base_branch:    Optional base branch/ref for commit comparisons (e.g. 'master').
                            When provided alongside a commit URL, the diff is fetched as
                            compare/<base_branch>...<commit_sha>.
            extra_prompt:   Optional additional instructions injected into the AI request
                            alongside the diff. Use this to focus or constrain the generated
                            comment without editing the prompt template
                            (e.g. "Pay special attention to the migration script risk.").
            dry_run:        If True, returns the comment without posting to Jira.

        Returns:
            The generated comment.
        """
        logger.info(f"Fetching title and ID for Jira issue: {issue_key}")
        issue_data = self.jira.get_issue(issue_key)
        issue_title = issue_data["summary"]
        issue_id = issue_data["id"]
        
        diff_content = ""
        
        if git_references:
            # Explicit mode: fetch diffs for all provided URLs and aggregate.
            # Each URL can be from a different repository — this is the fallback
            # path when the Jira Dev Status API is unavailable.
            for ref in git_references:
                if base_branch and isinstance(self.git, GitHubHTTPProvider) and "/commit/" in ref:
                    commit_sha = ref.split("/commit/")[-1]
                    logger.info(f"Fetching compare diff: {base_branch}...{commit_sha[:8]}")
                    try:
                        ref_diff = self.git.get_compare_diff(
                            repo_url=ref,
                            base=base_branch,
                            head=commit_sha,
                        )
                    except Exception as e:
                        logger.warning(f"Could not get compare diff for {ref}: {e}")
                        continue
                else:
                    logger.info(f"Fetching diff for: {ref}")
                    try:
                        ref_diff = self.git.get_diff(ref)
                    except Exception as e:
                        logger.warning(f"Could not get diff for {ref}: {e}")
                        continue

                # Label each diff by its URL so the AI has per-repo context
                repo_label = ref.split("github.com/")[-1].split("/commit/")[0].split("/pull/")[0]
                diff_content += f"\n\n### Project: {repo_label}\n```diff\n{ref_diff}\n```\n"

            if not diff_content.strip():
                raise ValueError("Could not retrieve any diffs from the provided URLs.")
        else:
            logger.info(f"No explicit git reference provided. Auto-discovering from Jira for issue {issue_key}...")
            links = self.jira.get_development_links(issue_id)
            
            # 1. Prioritize Pull Requests
            pr_data = links.get("pullrequests", {})
            for detail_obj in pr_data.get("detail", []):
                for pr in detail_obj.get("pullRequests", []):
                    pr_url = pr.get("url")
                    if not pr_url: continue
                    
                    try:
                        pr_diff = self.git.get_diff(pr_url)
                        diff_content += f"\n\n### Pull Request: {pr.get('name', pr_url)}\n```diff\n{pr_diff}\n```\n"
                        logger.info(f"Successfully retrieved diff for PR {pr_url}")
                    except Exception as e:
                        logger.warning(f"Could not get diff for PR {pr_url}: {e}")
            
            # 2. If no PRs yielded diffs, fall back to commits
            if not diff_content.strip():
                logger.info("No Pull Requests found or fetched. Falling back to Commits...")
                commits_data = links.get("commits", {})
                for detail_obj in commits_data.get("detail", []):
                    for repo in detail_obj.get("repositories", []):
                        repo_name = repo.get("name", "Unknown Repository")
                        commits = repo.get("commits", [])
                        if not commits: continue

                        repo_diffs = ""
                        for commit in commits:
                            commit_url = commit.get("url")
                            if not commit_url: continue

                            try:
                                commit_diff = self.git.get_diff(commit_url)
                                repo_diffs += f"\nCommit: {commit.get('id', commit_url)}\n```diff\n{commit_diff}\n```\n"
                                logger.info(f"Successfully retrieved diff for Commit {commit_url}")
                            except Exception as e:
                                logger.warning(f"Could not get diff for Commit {commit_url}: {e}")
                                
                        if repo_diffs:
                            diff_content += f"\n\n### Project: {repo_name}\n" + repo_diffs

            if not diff_content.strip():
                raise ValueError("Could not auto-discover any diffs from Jira development links. Please provide a direct URL.")
        
        logger.info("Generating AI comment based on diff and issue title...")
        if extra_prompt:
            logger.info(f"Extra prompt provided: {extra_prompt[:80]}{'...' if len(extra_prompt) > 80 else ''}")
        comment = self.ai.generate_comment(
            task_title=issue_title,
            git_diff=diff_content,
            extra_prompt=extra_prompt,
        )
        
        if dry_run:
            logger.info("Dry run enabled. Skipping Jira comment posting.")
        else:
            logger.info(f"Posting generated comment to Jira issue {issue_key}...")
            self.jira.add_comment(issue_key, comment)
            logger.info("Successfully posted comment.")
            
        return comment
