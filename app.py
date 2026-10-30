import os
import json
import base64
import re
from datetime import date, timedelta
from io import BytesIO

import pandas as pd
import requests
import streamlit as st

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from reporadar_utils import parse_repo_url


st.set_page_config(
    page_title="RepoRadar",
    page_icon="🔍",
    layout="wide",
)

try:
    GITHUB_TOKEN = st.secrets.get(
        "REPO_RADAR_TOKEN",
        os.getenv("REPO_RADAR_TOKEN")
    )
except Exception:
    GITHUB_TOKEN = os.getenv("REPO_RADAR_TOKEN")

# ---------------- PREMIUM UI DESIGN ----------------

st.markdown("""
<style>
:root {
    --rr-bg: #08111f;
    --rr-panel: #111e31;
    --rr-panel-2: #15243a;
    --rr-border: #263a55;
    --rr-text: #edf4ff;
    --rr-muted: #9aacc4;
    --rr-blue: #60a5fa;
    --rr-teal: #2dd4bf;
}

.stApp {
    background: radial-gradient(circle at 12% 0%, #142b49 0, transparent 32%),
                linear-gradient(135deg, #08111f 0%, #0b1627 55%, #101d30 100%);
    color: var(--rr-text);
}

.block-container {
    max-width: 1440px;
    padding: 2.2rem 2.2rem 3.5rem;
}

h1, h2, h3, h4 {
    color: var(--rr-text) !important;
    letter-spacing: -0.025em;
}

h1 {
    font-size: 2.55rem !important;
    font-weight: 800 !important;
}

h2 {
    font-size: 1.55rem !important;
    font-weight: 750 !important;
    margin-top: 1.4rem !important;
}

h3 {
    font-size: 1.12rem !important;
    font-weight: 700 !important;
}

p, label, [data-testid="stMarkdownContainer"] {
    color: #d5e1f0;
}

[data-testid="stCaptionContainer"] {
    color: var(--rr-muted) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--rr-border) !important;
    border-radius: 16px !important;
}

hr {
    border-color: #263a55 !important;
    margin: 1.7rem 0 !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #172941 0%, #101d30 100%);
    border: 1px solid var(--rr-border);
    border-radius: 16px;
    padding: 18px 20px;
    min-height: 112px;
    box-shadow: 0 8px 24px rgba(0,0,0,.16);
    transition: transform .18s ease, border-color .18s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: #4775a8;
}

[data-testid="stMetricLabel"] {
    color: var(--rr-muted) !important;
    font-size: .88rem !important;
}

[data-testid="stMetricValue"] {
    color: var(--rr-blue) !important;
    font-size: 1.85rem !important;
    font-weight: 800 !important;
}

[data-testid="stMetricDelta"] {
    font-size: .8rem !important;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox [data-baseweb="select"] > div {
    background: #101d30 !important;
    color: var(--rr-text) !important;
    border: 1px solid #344c6b !important;
    border-radius: 11px !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--rr-blue) !important;
    box-shadow: 0 0 0 2px rgba(96,165,250,.18) !important;
}

.stButton button,
.stDownloadButton button {
    min-height: 44px;
    border-radius: 11px;
    font-weight: 700;
    border: 1px solid #3b82f6;
    transition: transform .18s ease, box-shadow .18s ease;
}

.stButton button[kind="primary"] {
    color: white !important;
    border: 0 !important;
    background: linear-gradient(100deg, #2563eb, #0f9f9a) !important;
    box-shadow: 0 7px 20px rgba(37,99,235,.2);
}

.stButton button:hover,
.stDownloadButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 7px 18px rgba(37,99,235,.16);
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #3b82f6, #2dd4bf);
    border-radius: 20px;
}

[data-testid="stAlert"] {
    border-radius: 13px;
    border: 1px solid var(--rr-border);
}

[data-testid="stExpander"] {
    background: rgba(17,30,49,.78);
    border: 1px solid var(--rr-border);
    border-radius: 13px;
}

[data-testid="stExpander"] summary {
    color: var(--rr-text) !important;
    font-weight: 650;
}

[data-testid="stPlotlyChart"],
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"],
[data-testid="stDataFrame"] {
    background: rgba(17,30,49,.72);
    border: 1px solid var(--rr-border);
    border-radius: 14px;
    padding: 8px;
}

[data-testid="stDataFrame"] {
    overflow: hidden;
}

[data-testid="stSidebar"] {
    background: #0a1423;
    border-right: 1px solid var(--rr-border);
}

footer {
    visibility: hidden;
}

@media (max-width: 768px) {
    .block-container {
        padding: 1.1rem .9rem 2rem;
    }

    h1 {
        font-size: 2rem !important;
    }

    h2 {
        font-size: 1.3rem !important;
    }

    [data-testid="stMetric"] {
        padding: 14px;
        min-height: 96px;
    }
}
</style>
""", unsafe_allow_html=True)


def github_get(url, allow_not_found=False):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )

    if response.status_code == 404 and allow_not_found:
        return None

    if response.status_code == 401:
        raise ValueError("GitHub token is invalid or expired.")

    if response.status_code == 403:
        raise ValueError(
            "GitHub API access denied or rate limit reached. "
            "Please try again later."
        )

    if response.status_code == 404:
        raise ValueError("Repository or GitHub resource not found.")

    response.raise_for_status()

    if response.status_code == 204:
        return []

    return response.json()


def analyze_readme(readme_response):
    if not readme_response:
        return {
            "exists": False,
            "word_count": 0,
            "sections": [],
            "score": 0,
            "checks": {
                "README exists": False,
                "Good documentation length": False,
                "Features section": False,
                "Installation instructions": False,
                "Usage examples": False,
                "Screenshots or demo": False,
                "Structured headings": False,
            },
            "suggestions": [
                "Create a README.md file."
            ],
        }

    try:
        content = base64.b64decode(
            readme_response["content"]
        ).decode("utf-8", errors="replace")

    except (KeyError, ValueError):
        content = ""

    word_count = len(
        re.findall(r"\b[\w'-]+\b", content)
    )

    headings = re.findall(
        r"(?m)^#{1,6}\s+(.+)$",
        content,
    )

    lower_content = content.lower()

    features_present = bool(
        re.search(
            r"(?im)^#{1,6}\s+.*feature",
            content,
        )
    )

    installation_present = any(
        term in lower_content
        for term in [
            "installation",
            "getting started",
            "how to install",
            "pip install",
            "npm install",
            "setup",
        ]
    )

    usage_present = any(
        term in lower_content
        for term in [
            "usage",
            "how to use",
            "example",
            "quick start",
        ]
    )

    screenshots_present = any(
        term in lower_content
        for term in [
            "screenshot",
            "screenshots",
            "demo",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
        ]
    )

    length_good = word_count >= 150
    structured = len(headings) >= 3

    checks = {
        "README exists": True,
        "Good documentation length": length_good,
        "Features section": features_present,
        "Installation instructions": installation_present,
        "Usage examples": usage_present,
        "Screenshots or demo": screenshots_present,
        "Structured headings": structured,
    }

    score = 20

    if length_good:
        score += 20

    if features_present:
        score += 15

    if installation_present:
        score += 15

    if usage_present:
        score += 15

    if screenshots_present:
        score += 10

    if structured:
        score += 5

    suggestions = []

    if not length_good:
        suggestions.append(
            "Expand your README with more project details."
        )

    if not features_present:
        suggestions.append(
            "Add a Features section explaining the main capabilities."
        )

    if not installation_present:
        suggestions.append(
            "Add installation and setup instructions."
        )

    if not usage_present:
        suggestions.append(
            "Add usage instructions and code examples."
        )

    if not screenshots_present:
        suggestions.append(
            "Add screenshots or a demo link."
        )

    if not structured:
        suggestions.append(
            "Organize your README using at least three headings."
        )

    return {
        "exists": True,
        "word_count": word_count,
        "sections": headings,
        "score": score,
        "checks": checks,
        "suggestions": suggestions,
    }


def get_grade(score):
    if score >= 85:
        return "A"

    if score >= 70:
        return "B"

    if score >= 50:
        return "C"

    if score >= 35:
        return "D"

    return "F"


def analyze_project_structure(base_url, default_branch):
    """Inspect repository files and identify project technologies."""

    tree_data = github_get(
        f"{base_url}/git/trees/{default_branch}?recursive=1"
    )

    tree = (
        tree_data.get("tree", [])
        if isinstance(tree_data, dict)
        else []
    )

    files = [
        item.get("path", "")
        for item in tree
        if item.get("type") == "blob"
    ]

    directories = sorted({
        path.rsplit("/", 1)[0]
        for path in files
        if "/" in path
    })

    root_files = {
        path.lower().split("/")[-1]
        for path in files
        if "/" not in path
    }

    manifests = {
        "Python": [
            "requirements.txt",
            "pyproject.toml",
            "pipfile",
            "setup.py",
        ],
        "JavaScript": [
            "package.json",
            "package-lock.json",
            "yarn.lock",
        ],
        "Java": [
            "pom.xml",
            "build.gradle",
            "gradlew",
        ],
        "C/C++": [
            "makefile",
            "cmakelists.txt",
        ],
        "Ruby": ["gemfile"],
        "PHP": ["composer.json"],
        "Go": ["go.mod"],
        "Rust": ["cargo.toml"],
    }

    detected = [
        language
        for language, names in manifests.items()
        if any(name in root_files for name in names)
    ]

    important = {
        "README": any(
            name.startswith("readme")
            for name in root_files
        ),
        "License": any(
            name.startswith("license")
            for name in root_files
        ),
        ".gitignore": ".gitignore" in root_files,
        "Dependency manifest": any(
            name in root_files
            for names in manifests.values()
            for name in names
        ),
        "Tests folder": any(
            path.lower().split("/")[0] in {"test", "tests"}
            for path in files
        ),
        "Dockerfile": "dockerfile" in root_files,
        "CI workflow": any(
            path.startswith(".github/workflows/")
            for path in files
        ),
    }

    return {
        "file_count": len(files),
        "directory_count": len(directories),
        "directories": directories[:40],
        "files": files[:100],
        "detected_project_types": detected,
        "important_files": important,
        "truncated": len(files) > 100,
    }


def analyze_repository(repo_url):
    owner, repo = parse_repo_url(repo_url)

    base_url = (
        f"https://api.github.com/repos/{owner}/{repo}"
    )

    metadata = github_get(base_url)

    project_structure = analyze_project_structure(
        base_url,
        metadata.get("default_branch", "main"),
    )
    contents = github_get(
        base_url + "/contents"
    )

    languages = github_get(
        base_url + "/languages"
    )

    commits = github_get(
        base_url + "/commits?per_page=100"
    )

    contributors = github_get(
        base_url + "/contributors?per_page=100"
    )

    issues = github_get(
        base_url + "/issues?state=all&per_page=100"
    )

    readme_response = github_get(
        base_url + "/readme",
        allow_not_found=True,
    )

    readme_analysis = analyze_readme(
        readme_response
    )

    root_names = [
        item.get("name", "").lower()
        for item in contents
    ]

    readme_present = any(
        name.startswith("readme")
        for name in root_names
    )

    license_present = any(
        name.startswith("license")
        for name in root_names
    )

    tests_present = any(
        name in ["tests", "test"]
        for name in root_names
    )

    description_present = bool(
        metadata.get("description")
    )

    language_present = bool(languages)

    archived = metadata.get("archived", False)

    checks = {
        "README present": readme_present,
        "License present": license_present,
        "Test directory indicator": tests_present,
        "Description present": description_present,
        "Languages detected": language_present,
        "Repository not archived": not archived,
    }

    health_score = int(
        sum(checks.values()) / len(checks) * 100
    )

    # Commit activity analysis

    today = date.today()
    start_date = today - timedelta(days=29)

    activity = {
        (start_date + timedelta(days=i)).isoformat(): 0
        for i in range(30)
    }

    for commit in commits:
        commit_data = commit.get("commit", {})

        author_data = (
            commit_data.get("committer")
            or commit_data.get("author")
            or {}
        )

        commit_date = author_data.get("date")

        if commit_date and commit_date[:10] in activity:
            activity[commit_date[:10]] += 1

    recent_commit_count = sum(
        activity.values()
    )

    # Contributor analysis

    contributor_data = []

    if isinstance(contributors, list):
        for contributor in contributors:

            if contributor.get("type") == "Bot":
                continue

            contributor_data.append({
                "Username": contributor.get(
                    "login", "Unknown"
                ),
                "Contributions": contributor.get(
                    "contributions", 0
                ),
                "Profile": contributor.get(
                    "html_url", ""
                ),
            })

    contributor_data.sort(
        key=lambda x: x["Contributions"],
        reverse=True,
    )

    # Issue analytics

    actual_issues = [
        issue
        for issue in issues
        if "pull_request" not in issue
    ]

    open_issues = sum(
        1
        for issue in actual_issues
        if issue.get("state") == "open"
    )

    closed_issues = sum(
        1
        for issue in actual_issues
        if issue.get("state") == "closed"
    )

    # Latest commit

    latest_commit_date = None

    if commits:
        latest_commit = commits[0].get("commit", {})

        latest_author = (
            latest_commit.get("committer")
            or latest_commit.get("author")
            or {}
        )

        latest_commit_date = latest_author.get("date")

    # Combined score

    overall_score = round(
        health_score * 0.60
        + readme_analysis["score"] * 0.40
    )

    report = {
        "repository": metadata.get("full_name"),
        "description": metadata.get("description"),
        "url": metadata.get("html_url"),
        "stars": metadata.get("stargazers_count", 0),
        "forks": metadata.get("forks_count", 0),
        "open_issues": metadata.get("open_issues_count", 0),
        "default_branch": metadata.get("default_branch"),
        "created_at": metadata.get("created_at"),
        "updated_at": metadata.get("updated_at"),
        "archived": archived,
        "languages": languages,
        "readme_present": readme_present,
        "license_present": license_present,
        "tests_present": tests_present,
        "latest_commit_date": latest_commit_date,
        "commit_activity": activity,
        "recent_commit_count": recent_commit_count,
        "commits_fetched": len(commits),
        "checks": checks,
        "score": health_score,
        "overall_score": overall_score,
        "grade": get_grade(overall_score),
        "contributors": contributor_data,
        "contributors_fetched": len(contributor_data),
        "issues_analyzed": len(actual_issues),
        "open_issues_analyzed": open_issues,
        "closed_issues_analyzed": closed_issues,
        "readme_analysis": readme_analysis,
        "project_structure": project_structure,
    }

    return report


def create_pdf_report(report):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    story = [
        Paragraph(
            "RepoRadar - Repository Analysis Report",
            styles["Title"],
        ),
        Spacer(1, 12),
        Paragraph(
            report["repository"],
            styles["Heading2"],
        ),
        Paragraph(
            report.get("description")
            or "No repository description provided.",
            styles["BodyText"],
        ),
        Spacer(1, 12),
    ]

    summary_data = [
        ["Overall Score", f'{report["overall_score"]}/100'],
        ["Grade", report["grade"]],
        ["Repository Health", f'{report["score"]}/100'],
        [
            "README Quality",
            f'{report["readme_analysis"]["score"]}/100',
        ],
        ["Stars", str(report["stars"])],
        ["Forks", str(report["forks"])],
        [
            "Commits (last 30 days)",
            str(report["recent_commit_count"]),
        ],
        [
            "Contributors",
            str(report["contributors_fetched"]),
        ],
        [
            "Issues analyzed",
            str(report["issues_analyzed"]),
        ],
    ]

    table = Table(
        summary_data,
        colWidths=[220, 230],
    )

    table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#17365D"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "BACKGROUND",
                (0, 0),
                (0, -1),
                colors.HexColor("#EAF0F6"),
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey,
            ),
            (
                "PADDING",
                (0, 0),
                (-1, -1),
                7,
            ),
        ])
    )

    story += [
        table,
        Spacer(1, 16),
        Paragraph(
            "Repository Health Checks",
            styles["Heading2"],
        ),
    ]

    for label, passed in report["checks"].items():
        status = "PASS" if passed else "NEEDS ATTENTION"

        story.append(
            Paragraph(
                f"{status} - {label}",
                styles["BodyText"],
            )
        )

    story += [
        Spacer(1, 12),
        Paragraph(
            "README Improvement Suggestions",
            styles["Heading2"],
        ),
    ]

    suggestions = (
        report["readme_analysis"]["suggestions"]
        or ["No README suggestions."]
    )

    for item in suggestions:
        story.append(
            Paragraph(
                f"- {item}",
                styles["BodyText"],
            )
        )

    story += [
        Spacer(1, 16),
        Paragraph(
            "Scoring note",
            styles["Heading2"],
        ),
        Paragraph(
            "Overall score = 60% repository health score "
            "+ 40% README quality score. Both component "
            "scores are heuristic checks created by RepoRadar "
            "and are not an industry-standard certification. "
            "GitHub activity and issue counts are based on "
            "the API results available during this analysis.",
            styles["BodyText"],
        ),
    ]

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# ---------------- STREAMLIT UI ----------------


# ---------------- STREAMLIT DASHBOARD UI ----------------

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    [data-testid="stSidebar"] {
        background-color: #f5f7fb;
    }
    .dashboard-title {
        font-size: 32px;
        font-weight: 750;
        color: #172554;
    }
    .dashboard-subtitle {
        color: #64748b;
        font-size: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🔍 RepoRadar")
st.sidebar.caption("GitHub Repository Intelligence")

page = st.sidebar.radio(
    "NAVIGATION",
    [
        "Overview",
        "Repository Health",
        "Activity",
        "README Analyzer",
        "Project Structure",
        "Reports"
    ]
)

st.sidebar.divider()
st.sidebar.caption("Built with Python & Streamlit")

# Main heading
st.markdown(
    '<div class="dashboard-title">RepoRadar Dashboard</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="dashboard-subtitle">'
    'Analyze repository quality, activity and documentation.'
    '</div>',
    unsafe_allow_html=True
)

st.write("")

if not GITHUB_TOKEN:
    st.sidebar.warning(
        "GitHub token not configured. "
        "Unauthenticated API limits may apply."
    )

# Repository input
with st.form("repository_form"):
    repo_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/username/repository"
    )

    analyze_button = st.form_submit_button(
        "🚀 Analyze Repository",
        type="primary",
        use_container_width=True
    )

if analyze_button:
    if not repo_url.strip():
        st.warning("Please enter a GitHub repository URL.")

    else:
        try:
            with st.spinner("Analyzing repository..."):
                report = analyze_repository(repo_url.strip())

            st.session_state["repo_report"] = report
            st.success("Repository analysis completed!")

        except Exception as error:
            st.error(f"Analysis failed: {error}")

# Keep report available when navigating
report = st.session_state.get("repo_report")

if not report:
    st.info(
        "👆 Enter a GitHub repository URL and click "
        "'Analyze Repository' to get started."
    )

    st.markdown("### What RepoRadar analyzes")

    c1, c2, c3 = st.columns(3)
    c1.metric("Repository Health", "Quality checks")
    c2.metric("README Analyzer", "Documentation")
    c3.metric("Activity", "GitHub insights")

else:
    st.divider()

    st.subheader(f"📦 {report['repository']}")

    if report.get("description"):
        st.caption(report["description"])

    st.markdown(
        f"[↗ Open GitHub Repository]({report['url']})"
    )

    # ---------------- OVERVIEW ----------------

    if page == "Overview":

        st.header("📊 Repository Overview")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Overall Score",
            f"{report['overall_score']}/100"
        )
        c2.metric(
            "Grade",
            report["grade"]
        )
        c3.metric(
            "Health Score",
            f"{report['score']}/100"
        )
        c4.metric(
            "README Score",
            f"{report['readme_analysis']['score']}/100"
        )

        st.progress(report["overall_score"] / 100)

        st.caption(
            "Overall Score = 60% Repository Health + "
            "40% README Quality. This is a RepoRadar heuristic."
        )

        st.divider()

        st.subheader("Repository Statistics")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("⭐ Stars", report["stars"])
        c2.metric("🍴 Forks", report["forks"])
        c3.metric("🐛 Open Issues", report["open_issues"])
        c4.metric(
            "👥 Contributors",
            report["contributors_fetched"]
        )

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader("💻 Programming Languages")

            if report["languages"]:
                language_df = pd.DataFrame(
                    list(report["languages"].items()),
                    columns=["Language", "Bytes"]
                ).sort_values("Bytes", ascending=False)

                st.bar_chart(
                    language_df.set_index("Language")
                )
            else:
                st.info("No languages detected.")

        with right:
            st.subheader("🐛 Issue Summary")

            issue_df = pd.DataFrame({
                "Status": ["Open", "Closed"],
                "Count": [
                    report["open_issues_analyzed"],
                    report["closed_issues_analyzed"]
                ]
            })

            st.bar_chart(
                issue_df.set_index("Status")
            )

        st.divider()

        st.subheader("📈 Recent Activity")

        st.metric(
            "Commits in Last 30 Days",
            report["recent_commit_count"]
        )

        activity_df = pd.DataFrame(
            list(report["commit_activity"].items()),
            columns=["Date", "Commits"]
        )

        activity_df["Date"] = pd.to_datetime(
            activity_df["Date"]
        )

        st.line_chart(
            activity_df.set_index("Date")
        )

    # ---------------- REPOSITORY HEALTH ----------------

    elif page == "Repository Health":

        st.header("🏥 Repository Health")

        st.metric(
            "Repository Health Score",
            f"{report['score']}/100"
        )

        st.progress(report["score"] / 100)

        st.subheader("Health Checklist")

        for check, passed in report["checks"].items():
            if passed:
                st.success(check)
            else:
                st.warning(check)

        st.divider()

        st.subheader("Repository Information")

        st.write("Default Branch:", report["default_branch"])
        st.write("Created:", report["created_at"])
        st.write("Last Updated:", report["updated_at"])
        st.write("Archived:", "Yes" if report["archived"] else "No")
        st.write(
            "Latest Commit:",
            report["latest_commit_date"] or "No commits found"
        )

        st.subheader("Repository Improvement Suggestions")

        suggestions = []

        if not report["readme_present"]:
            suggestions.append("Add a README file.")
        if not report["license_present"]:
            suggestions.append("Add an open-source license.")
        if not report["tests_present"]:
            suggestions.append("Add a tests directory.")
        if not report["description"]:
            suggestions.append("Add a repository description.")
        if not report["languages"]:
            suggestions.append("Add source code files.")
        if report["archived"]:
            suggestions.append("This repository is archived.")
        if report["recent_commit_count"] == 0:
            suggestions.append("Maintain regular commit activity.")

        if suggestions:
            for suggestion in suggestions:
                st.write("🔸", suggestion)
        else:
            st.success("All basic repository health checks passed!")

    # ---------------- ACTIVITY ----------------

    elif page == "Activity":

        st.header("📈 Repository Activity")

        c1, c2 = st.columns(2)

        c1.metric(
            "Commits in Last 30 Days",
            report["recent_commit_count"]
        )
        c2.metric(
            "Recent Commits Fetched",
            report["commits_fetched"]
        )

        activity_df = pd.DataFrame(
            list(report["commit_activity"].items()),
            columns=["Date", "Commits"]
        )

        activity_df["Date"] = pd.to_datetime(
            activity_df["Date"]
        )

        st.subheader("Commit Activity - Last 30 Days")

        st.line_chart(
            activity_df.set_index("Date")
        )

        st.caption(
            "Activity is calculated from up to 100 recent commits."
        )

        st.divider()

        st.subheader("👥 Contributor Analysis")

        st.metric(
            "Contributors Found",
            report["contributors_fetched"]
        )

        if report["contributors"]:
            contributor_df = pd.DataFrame(
                report["contributors"]
            )

            st.bar_chart(
                contributor_df.head(10).set_index("Username")[
                    ["Contributions"]
                ]
            )

            st.dataframe(
                contributor_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No contributors found.")

        st.divider()

        st.subheader("🐛 Issue Analytics")

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Open Issues",
            report["open_issues_analyzed"]
        )
        c2.metric(
            "Closed Issues",
            report["closed_issues_analyzed"]
        )
        c3.metric(
            "Total Issues",
            report["issues_analyzed"]
        )

        issue_df = pd.DataFrame({
            "Status": ["Open", "Closed"],
            "Count": [
                report["open_issues_analyzed"],
                report["closed_issues_analyzed"]
            ]
        })

        st.bar_chart(issue_df.set_index("Status"))

    # ---------------- README ANALYZER ----------------

    elif page == "README Analyzer":

        st.header("📘 README Quality Analyzer")

        readme = report["readme_analysis"]

        c1, c2 = st.columns(2)

        c1.metric(
            "README Score",
            f"{readme['score']}/100"
        )
        c2.metric(
            "Word Count",
            readme["word_count"]
        )

        st.progress(readme["score"] / 100)

        if readme["exists"]:

            st.subheader("README Quality Checklist")

            for check, passed in readme["checks"].items():
                if passed:
                    st.success(check)
                else:
                    st.warning(check)

            st.divider()

            st.subheader("README Sections")

            if readme["sections"]:
                for section in readme["sections"]:
                    st.write("📌", section)
            else:
                st.info("No Markdown headings detected.")

            st.divider()

            st.subheader("Improvement Suggestions")

            if readme["suggestions"]:
                for suggestion in readme["suggestions"]:
                    st.write("🔸", suggestion)
            else:
                st.success("README passed all quality checks!")

        else:
            st.warning("This repository does not have a readable README.")

    # ---------------- PROJECT STRUCTURE ----------------

    elif page == "Project Structure":

        st.header("🧭 Project Structure Analysis")

        structure = report["project_structure"]

        c1, c2 = st.columns(2)

        c1.metric("Files Detected", structure["file_count"])
        c2.metric(
            "Directories Detected",
            structure["directory_count"]
        )

        st.divider()

        st.subheader("Detected Project Types")

        project_types = structure["detected_project_types"]

        if project_types:
            for project_type in project_types:
                st.success(project_type)
        else:
            st.info("No project manifest detected.")

        st.divider()

        st.subheader("Important Project Files")

        for label, found in structure["important_files"].items():
            if found:
                st.success(label)
            else:
                st.warning(label)

        st.divider()

        st.subheader("Repository Folders")

        for folder in structure["directories"]:
            st.write("📁", folder)

        st.divider()

        st.subheader("Repository Files")

        st.code("\n".join(structure["files"]))

        if structure["truncated"]:
            st.caption("Showing the first 100 files.")

    # ---------------- REPORTS ----------------

    elif page == "Reports":

        st.header("📥 Download Reports")

        st.write(
            "Download your repository analysis in JSON "
            "or PDF format."
        )

        json_report = json.dumps(
            report,
            indent=4
        )

        pdf_data = create_pdf_report(report)

        c1, c2 = st.columns(2)

        with c1:
            st.download_button(
                "⬇️ Download JSON Report",
                data=json_report,
                file_name="reporadar_report.json",
                mime="application/json",
                use_container_width=True
            )

        with c2:
            st.download_button(
                "⬇️ Download PDF Report",
                data=pdf_data,
                file_name="reporadar_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.divider()

        st.subheader("Report Summary")

        st.write("Repository:", report["repository"])
        st.write("Overall Score:", report["overall_score"])
        st.write("Grade:", report["grade"])
        st.write("Health Score:", report["score"])
        st.write(
            "README Score:",
            report["readme_analysis"]["score"]
        )

st.divider()

st.caption(
    "RepoRadar | Python | Streamlit | Pandas | GitHub REST API"
)
