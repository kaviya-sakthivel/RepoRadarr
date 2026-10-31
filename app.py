
import base64
import json
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="RepoRadar | GitHub Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. CUSTOM UI
# =========================================================

st.markdown("""
<style>
    .stApp {
        background-color: #0b1120;
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #263449;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    h1, h2, h3 {
        color: #f8fafc !important;
    }

    p, label, li {
        color: #cbd5e1;
    }

    div[data-testid="stMetric"] {
        background: #151f31;
        border: 1px solid #263449;
        padding: 16px;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #94a3b8;
    }

    div[data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    div.stButton > button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 9px;
        font-weight: 600;
        min-height: 42px;
    }

    div.stButton > button:hover {
        background: #1d4ed8;
        color: white;
    }

    .hero {
        background: linear-gradient(120deg, #172554, #172033);
        border: 1px solid #30456c;
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 25px;
    }

    .hero-title {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
    }

    .hero-subtitle {
        color: #bfdbfe;
        font-size: 15px;
    }

    .section-card {
        background: #151f31;
        border: 1px solid #263449;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }

    .muted {
        color: #94a3b8;
        font-size: 13px;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)


# =========================================================
# 3. GITHUB API
# =========================================================

API_BASE = "https://api.github.com"


def get_token_from_secrets():
    try:
        return st.secrets.get("REPO_RADAR_TOKEN", "")
    except Exception:
        return ""


def create_github_session(token=""):
    session = requests.Session()

    session.headers.update({
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "RepoRadar-Application"
    })

    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    return session


def github_get(session, endpoint, params=None, allow_404=False):
    try:
        response = session.get(
            API_BASE + endpoint,
            params=params,
            timeout=25
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"Unable to connect to GitHub: {error}"
        )

    if allow_404 and response.status_code == 404:
        return None

    if response.status_code == 403:
        if response.headers.get("X-RateLimit-Remaining") == "0":
            raise RuntimeError(
                "GitHub API rate limit reached. Add a GitHub token "
                "in the sidebar or Streamlit secrets."
            )

    if response.status_code == 404:
        raise RuntimeError(
            "Repository not found or inaccessible. "
            "Check the URL and make sure the repository is public."
        )

    if not response.ok:
        try:
            message = response.json().get(
                "message",
                response.text
            )
        except ValueError:
            message = response.text

        raise RuntimeError(
            f"GitHub API error {response.status_code}: {message}"
        )

    return response.json()


# =========================================================
# 4. REPOSITORY URL VALIDATION
# =========================================================

def parse_repository_url(value):
    value = (value or "").strip()

    if not value:
        raise ValueError("Please enter a GitHub repository URL.")

    if "://" not in value:
        value = "https://" + value

    parsed = urlparse(value)

    if parsed.netloc.lower() not in (
        "github.com",
        "www.github.com"
    ):
        raise ValueError("Please enter a valid GitHub URL.")

    parts = [
        part for part in parsed.path.strip("/").split("/")
        if part
    ]

    if len(parts) != 2:
        raise ValueError(
            "Use this format: https://github.com/owner/repository"
        )

    owner, repo = parts

    if repo.endswith(".git"):
        repo = repo[:-4]

    pattern = r"^[A-Za-z0-9_.-]+$"

    if not re.fullmatch(pattern, owner):
        raise ValueError("Invalid GitHub owner name.")

    if not re.fullmatch(pattern, repo):
        raise ValueError("Invalid repository name.")

    return owner, repo


# =========================================================
# 5. GRADING SYSTEM
# =========================================================

def get_grade(score):
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 50:
        return "C"
    elif score >= 35:
        return "D"
    return "F"


# =========================================================
# 6. README QUALITY ANALYZER
# =========================================================

def analyze_readme(readme):
    checks = [
        (
            "Project title",
            bool(re.search(r"(?m)^#\s+\S", readme)),
            "Add a clear project title."
        ),
        (
            "Project description",
            len(readme.strip()) >= 100,
            "Explain what your project does."
        ),
        (
            "Installation instructions",
            bool(re.search(
                r"(?i)installation|install|setup|getting started",
                readme
            )),
            "Add installation instructions."
        ),
        (
            "Usage instructions",
            bool(re.search(
                r"(?i)usage|how to use|quick start",
                readme
            )),
            "Explain how to run the project."
        ),
        (
            "Code examples",
            "```" in readme or bool(
                re.search(r"`[^`]+`", readme)
            ),
            "Add code or command examples."
        ),
        (
            "Organized sections",
            len(re.findall(r"(?m)^#{1,3}\s+", readme)) >= 3,
            "Organize the README with headings."
        ),
        (
            "Contribution guidelines",
            bool(re.search(r"(?i)contribut", readme)),
            "Explain how others can contribute."
        ),
        (
            "License information",
            bool(re.search(r"(?i)licen[cs]e", readme)),
            "Mention the project license."
        ),
        (
            "Contact information",
            bool(re.search(
                r"(?i)contact|support|maintainer|author",
                readme
            )),
            "Add maintainer or contact information."
        ),
        (
            "Images or screenshots",
            bool(re.search(r"!\[[^\]]*\]\([^)]+\)", readme)),
            "Consider adding screenshots."
        )
    ]

    passed = sum(
        1 for _, status, _ in checks if status
    )

    score = round(
        passed / len(checks) * 100
    )

    results = []

    suggestions = []

    for label, status, suggestion in checks:
        results.append({
            "Check": label,
            "Passed": status,
            "Status": "Passed" if status else "Missing",
            "Suggestion": "Present" if status else suggestion
        })

        if not status:
            suggestions.append(suggestion)

    return score, results, suggestions


# =========================================================
# 7. REPOSITORY HEALTH ANALYZER
# =========================================================

def analyze_health(metadata, readme, tree, commits, contributors):

    checks = [
        (
            "README available",
            bool(readme),
            "Add a README.md file."
        ),
        (
            "Repository description",
            bool(metadata.get("description")),
            "Add a repository description."
        ),
        (
            "License available",
            bool(metadata.get("license")),
            "Add a license if appropriate."
        ),
        (
            "Repository updated",
            bool(metadata.get("pushed_at")),
            "Maintain your repository."
        ),
        (
            "Tests directory",
            any(
                item.get("type") == "tree"
                and item.get("path", "").split("/")[-1].lower()
                in ("test", "tests")
                for item in tree
            ),
            "Consider adding a tests directory."
        ),
        (
            "Multiple contributors",
            len(contributors) > 1,
            "Consider collaboration and contribution guidelines."
        ),
        (
            "Commit history",
            len(commits) > 0,
            "Add meaningful commits."
        ),
        (
            "GitHub topics",
            bool(metadata.get("topics")),
            "Add relevant GitHub topics."
        ),
        (
            "Default branch",
            bool(metadata.get("default_branch")),
            "Configure a default branch."
        ),
        (
            "Repository not archived",
            not metadata.get("archived", False),
            "This repository is archived."
        )
    ]

    passed = sum(
        1 for _, status, _ in checks if status
    )

    score = round(
        passed / len(checks) * 100
    )

    results = []

    for label, status, suggestion in checks:
        results.append({
            "Check": label,
            "Passed": status,
            "Status": "Passed" if status else "Needs attention",
            "Suggestion": "Detected" if status else suggestion
        })

    return score, results


# =========================================================
# 8. COMPLETE REPOSITORY ANALYSIS
# =========================================================

def analyze_repository(owner, repo, token):

    session = create_github_session(token)

    base = f"/repos/{owner}/{repo}"

    metadata = github_get(session, base)

    # README
    readme_data = github_get(
        session,
        base + "/readme",
        allow_404=True
    )

    readme_text = ""

    if readme_data and readme_data.get("content"):
        try:
            readme_text = base64.b64decode(
                readme_data["content"]
            ).decode("utf-8", errors="replace")
        except Exception:
            readme_text = ""

    # Languages
    languages = github_get(
        session,
        base + "/languages"
    ) or {}

    # Contributors
    contributors = github_get(
        session,
        base + "/contributors",
        params={"per_page": 30}
    ) or []

    # Open issues (exclude pull requests)
    issues_raw = github_get(
        session,
        base + "/issues",
        params={
            "state": "open",
            "per_page": 30,
            "sort": "created",
            "direction": "desc"
        }
    ) or []

    issues = [
        item for item in issues_raw
        if "pull_request" not in item
    ]

    # Latest commits
    commits = github_get(
        session,
        base + "/commits",
        params={"per_page": 100}
    ) or []

    # Recent commit count from the latest 100 returned commits
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    recent_commits = 0

    for item in commits:
        date_text = (
            item.get("commit", {})
            .get("author", {})
            .get("date")
        )

        if date_text:
            try:
                commit_date = datetime.fromisoformat(
                    date_text.replace("Z", "+00:00")
                )

                if commit_date >= cutoff:
                    recent_commits += 1

            except ValueError:
                pass

    # Project tree
    branch = metadata.get("default_branch") or "main"

    tree_data = github_get(
        session,
        f"{base}/git/trees/{branch}",
        params={"recursive": "1"},
        allow_404=True
    ) or {}

    tree = tree_data.get("tree", [])

    # Scores
    health_score, health_checks = analyze_health(
        metadata,
        readme_text,
        tree,
        commits,
        contributors
    )

    readme_score, readme_checks, suggestions = analyze_readme(
        readme_text
    )

    overall_score = round(
        health_score * 0.60 +
        readme_score * 0.40
    )

    return {
        "metadata": metadata,
        "languages": languages,
        "contributors": contributors,
        "issues": issues,
        "commits": commits,
        "recent_commits": recent_commits,
        "health_score": health_score,
        "health_checks": health_checks,
        "readme_score": readme_score,
        "readme_checks": readme_checks,
        "readme_suggestions": suggestions,
        "readme_text": readme_text,
        "overall_score": overall_score,
        "tree": tree,
        "tree_truncated": tree_data.get("truncated", False),
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


# =========================================================
# 9. PDF REPORT
# =========================================================

def create_pdf_report(data):

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle
    )

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    metadata = data["metadata"]

    story = [
        Paragraph("RepoRadar Analysis Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(
            metadata.get("full_name", "Repository"),
            styles["Heading2"]
        ),
        Paragraph(
            metadata.get("description") or "No description available.",
            styles["BodyText"]
        ),
        Spacer(1, 15),
        Paragraph(
            f"Overall Score: {data['overall_score']}/100 "
            f"(Grade {get_grade(data['overall_score'])})",
            styles["Heading2"]
        ),
        Paragraph(
            f"Repository Health: {data['health_score']}/100",
            styles["BodyText"]
        ),
        Paragraph(
            f"README Quality: {data['readme_score']}/100",
            styles["BodyText"]
        ),
        Spacer(1, 15),
        Paragraph("Repository Health Checklist", styles["Heading2"])
    ]

    table_data = [
        ["Check", "Status", "Suggestion"]
    ]

    for item in data["health_checks"]:
        table_data.append([
            item["Check"],
            item["Status"],
            item["Suggestion"]
        ])

    table = Table(
        table_data,
        colWidths=[130, 90, 285],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("PADDING", (0, 0), (-1, -1), 5)
    ]))

    story.append(table)
    story.append(Spacer(1, 15))

    story.append(
        Paragraph("README Improvement Suggestions", styles["Heading2"])
    )

    if data["readme_suggestions"]:
        for suggestion in data["readme_suggestions"]:
            story.append(
                Paragraph("• " + suggestion, styles["BodyText"])
            )
    else:
        story.append(
            Paragraph("No missing README checks detected.", styles["BodyText"])
        )

    document.build(story)

    return buffer.getvalue()


# =========================================================
# 10. SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🛰️ RepoRadar")
    st.caption("GitHub Repository Intelligence")

    st.divider()

    repository_url = st.text_input(
        "GitHub Repository URL",
        placeholder="https://github.com/owner/repository"
    )

    github_token = st.text_input(
        "GitHub Token (Optional)",
        value=get_token_from_secrets(),
        type="password",
        help="A token increases the GitHub API rate limit."
    )

    analyze_button = st.button(
        "🔍 Analyze Repository",
        type="primary",
        use_container_width=True
    )

    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Overview",
            "Repository Health",
            "Activity Analytics",
            "README Analyzer",
            "Project Structure",
            "Reports"
        ]
    )

    st.divider()

    st.caption("RepoRadar Version 1.0")
    st.caption("Built with Python + Streamlit")


# =========================================================
# 11. SESSION STATE
# =========================================================

if "repo_data" not in st.session_state:
    st.session_state.repo_data = None


if analyze_button:

    st.session_state.repo_data = None

    try:
        owner, repo = parse_repository_url(repository_url)

        with st.spinner("Analyzing repository..."):
            result = analyze_repository(
                owner,
                repo,
                github_token.strip()
            )

        st.session_state.repo_data = result

        st.success("Analysis completed successfully!")

    except Exception as error:
        st.error(str(error))


# =========================================================
# 12. HERO SECTION
# =========================================================

st.markdown("""
<div class="hero">
    <div class="hero-title">🛰️ RepoRadar</div>
    <div class="hero-subtitle">
        GitHub Repository Health & Documentation Intelligence
    </div>
    <p>
        Analyze repository quality, development activity,
        contributors, documentation and project structure.
    </p>
</div>
""", unsafe_allow_html=True)


# =========================================================
# 13. EMPTY DASHBOARD
# =========================================================

data = st.session_state.repo_data

if not data:

    st.info(
        "Enter a public GitHub repository URL in the sidebar "
        "and click Analyze Repository."
    )

    st.markdown("### What RepoRadar analyzes")

    columns = st.columns(3)

    features = [
        ("🩺", "Repository Health",
         "Evaluate important repository quality indicators."),

        ("📘", "README Intelligence",
         "Check documentation completeness and suggestions."),

        ("📈", "Activity Analytics",
         "Inspect commits, contributors and issues."),

        ("💻", "Language Analysis",
         "Understand programming language distribution."),

        ("🌳", "Project Structure",
         "Explore files and folders in the repository."),

        ("📄", "Report Generation",
         "Download JSON and PDF analysis reports.")
    ]

    for index, (icon, title, description) in enumerate(features):

        with columns[index % 3]:

            st.markdown(
                f"""
                <div class="section-card">
                    <h3>{icon} {title}</h3>
                    <p class="muted">{description}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.stop()


# =========================================================
# 14. REPOSITORY HEADER
# =========================================================

metadata = data["metadata"]

st.markdown(
    f"## 📦 {metadata.get('full_name', 'Repository')}"
)

st.write(
    metadata.get("description") or "No repository description provided."
)

if metadata.get("html_url"):
    st.markdown(
        f"[🌐 Open repository on GitHub]({metadata['html_url']})"
    )

st.caption(
    f"Analysis generated: {data['generated_at']}"
)


# =========================================================
# 15. OVERVIEW PAGE
# =========================================================

if page == "Overview":

    st.subheader("Repository Overview")

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
    "⭐ Stars",
    f"{metadata.get('stargazers_count', 0):,}"
)

    col2.metric(
        "🍴 Forks",
        f"{metadata.get('forks_count', 0):,}"
    )

    col3.metric(
        "🐛 Open Issues",
        f"{metadata.get('open_issues_count', 0):,}"
    )

    col4.metric(
        "🩺 Health Score",
        f"{data['health_score']}/100"
    )

    col5.metric(
        "📘 README Score",
        f"{data['readme_score']}/100"
    )

    st.divider()

    left, right = st.columns(2)

    with left:

        st.markdown("### Overall Repository Score")

        st.metric(
            "Overall Score",
            f"{data['overall_score']}/100",
            f"Grade {get_grade(data['overall_score'])}"
        )

        st.progress(
            data["overall_score"] / 100
        )

        st.caption(
            "60% Repository Health + 40% README Quality"
        )

    with right:

        st.markdown("### Repository Information")

        owner_info = metadata.get("owner") or {}

        st.write({
            "Owner": owner_info.get("login", "Unknown"),
            "Default Branch": metadata.get("default_branch"),
            "Primary Language": metadata.get("language"),
            "Created": str(metadata.get("created_at", ""))[:10],
            "Last Updated": str(metadata.get("updated_at", ""))[:10],
            "Archived": metadata.get("archived", False)
        })

    st.divider()

    st.markdown("### Programming Language Distribution")

    languages = data["languages"]

    if languages:

        language_df = pd.DataFrame([
            {
                "Language": name,
                "Bytes": size
            }
            for name, size in languages.items()
        ])

        fig = px.pie(
            language_df,
            names="Language",
            values="Bytes",
            hole=0.5,
            title="Languages used in this repository"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:
        st.info("No language statistics are available.")


# =========================================================
# 16. REPOSITORY HEALTH PAGE
# =========================================================

elif page == "Repository Health":

    st.subheader("🩺 Repository Health Analysis")

    st.metric(
        "Repository Health Score",
        f"{data['health_score']}/100",
        f"Grade {get_grade(data['health_score'])}"
    )

    st.progress(
        data["health_score"] / 100
    )

    st.markdown("### Health Checklist")

    for item in data["health_checks"]:

        if item["Passed"]:

            st.success(
                f"✅ {item['Check']} — {item['Suggestion']}"
            )

        else:

            st.warning(
                f"⚠️ {item['Check']} — {item['Suggestion']}"
            )

    st.caption(
        "RepoRadar health score is a heuristic, not an official GitHub rating."
    )


# =========================================================
# 17. ACTIVITY ANALYTICS PAGE
# =========================================================

elif page == "Activity Analytics":

    st.subheader("📈 Development Activity")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Recent Commits (sample)",
        data["recent_commits"]
    )

    col2.metric(
        "Contributors Returned",
        len(data["contributors"])
    )

    col3.metric(
        "Open Issues Returned",
        len(data["issues"])
    )

    st.caption(
        "Commit activity is counted from at most the latest 100 "
        "commits returned by GitHub."
    )

    st.divider()

    st.markdown("### Contributor Analysis")

    contributors = data["contributors"]

    if contributors:

        contributor_df = pd.DataFrame([
            {
                "Contributor": item.get("login", "Unknown"),
                "Contributions": item.get("contributions", 0)
            }
            for item in contributors
        ])

        fig = px.bar(
            contributor_df,
            x="Contributor",
            y="Contributions",
            title="Contributions by contributor"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.dataframe(
            contributor_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No contributor information returned.")

    st.divider()

    st.markdown("### Open Issues")

    issues = data["issues"]

    if issues:

        issue_df = pd.DataFrame([
            {
                "Issue Number": issue.get("number"),
                "Title": issue.get("title"),
                "Author": (issue.get("user") or {}).get("login"),
                "Created": str(issue.get("created_at", ""))[:10],
                "URL": issue.get("html_url")
            }
            for issue in issues
        ])

        st.dataframe(
            issue_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "URL": st.column_config.LinkColumn("Issue Link")
            }
        )

    else:
        st.success("No open issues were returned.")


# =========================================================
# 18. README ANALYZER PAGE
# =========================================================

elif page == "README Analyzer":

    st.subheader("📘 README Documentation Intelligence")

    st.metric(
        "README Quality Score",
        f"{data['readme_score']}/100",
        f"Grade {get_grade(data['readme_score'])}"
    )

    st.progress(
        data["readme_score"] / 100
    )

    st.markdown("### Documentation Checklist")

    for item in data["readme_checks"]:

        if item["Passed"]:

            st.success(
                f"✅ {item['Check']} — {item['Suggestion']}"
            )

        else:

            st.warning(
                f"⚠️ {item['Check']} — {item['Suggestion']}"
            )

    st.divider()

    st.markdown("### Improvement Suggestions")

    if data["readme_suggestions"]:

        for suggestion in data["readme_suggestions"]:
            st.write(f"• {suggestion}")

    else:
        st.success("All README checks passed.")

    with st.expander("View complete README"):

        if data["readme_text"]:
            st.code(
                data["readme_text"],
                language="markdown"
            )
        else:
            st.info("README file was not found.")


# =========================================================
# 19. PROJECT STRUCTURE PAGE
# =========================================================

elif page == "Project Structure":

    st.subheader("🌳 Repository Project Structure")

    tree = data["tree"]

    st.metric(
        "Files and Folders Returned",
        len(tree)
    )

    if data["tree_truncated"]:

        st.warning(
            "GitHub marked this project tree as truncated. "
            "The displayed structure may be incomplete."
        )

    if tree:

        paths = []

        for item in tree[:250]:

            path = item.get("path", "")

            if item.get("type") == "tree":
                paths.append("📁 " + path + "/")
            else:
                paths.append("📄 " + path)

        st.code(
            "\n".join(paths),
            language="text"
        )

        extension_counts = {}

        for item in tree:

            if item.get("type") != "blob":
                continue

            filename = item.get("path", "")
            basename = filename.split("/")[-1]

            if "." in basename:
                extension = "." + basename.rsplit(".", 1)[-1]
            else:
                extension = "No extension"

            extension_counts[extension] = (
                extension_counts.get(extension, 0) + 1
            )

        if extension_counts:

            extension_df = pd.DataFrame([
                {
                    "File Type": ext,
                    "Count": count
                }
                for ext, count in extension_counts.items()
            ])

            extension_df = extension_df.sort_values(
                "Count",
                ascending=False
            ).head(15)

            fig = px.bar(
                extension_df,
                x="File Type",
                y="Count",
                title="File Type Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:
        st.info("No project structure data returned.")


# =========================================================
# 20. REPORT GENERATION PAGE
# =========================================================

elif page == "Reports":

    st.subheader("📄 Repository Analysis Reports")

    st.markdown("### Score Summary")

    st.write({
        "Repository": metadata.get("full_name"),
        "Overall Score": data["overall_score"],
        "Grade": get_grade(data["overall_score"]),
        "Health Score": data["health_score"],
        "README Score": data["readme_score"]
    })

    export_data = {
        "repository": {
            "name": metadata.get("full_name"),
            "url": metadata.get("html_url"),
            "description": metadata.get("description"),
            "stars": metadata.get("stargazers_count"),
            "forks": metadata.get("forks_count"),
            "open_issues": metadata.get("open_issues_count"),
            "primary_language": metadata.get("language"),
            "default_branch": metadata.get("default_branch")
        },
        "scores": {
            "overall": data["overall_score"],
            "grade": get_grade(data["overall_score"]),
            "health": data["health_score"],
            "readme": data["readme_score"]
        },
        "health_checks": data["health_checks"],
        "readme_checks": data["readme_checks"],
        "readme_suggestions": data["readme_suggestions"],
        "languages": data["languages"],
        "activity": {
            "recent_commits_in_latest_100_sample":
                data["recent_commits"],
            "commit_sample_size": len(data["commits"])
        },
        "contributors": [
            {
                "login": item.get("login"),
                "contributions": item.get("contributions")
            }
            for item in data["contributors"]
        ],
        "issues": [
            {
                "number": item.get("number"),
                "title": item.get("title"),
                "url": item.get("html_url")
            }
            for item in data["issues"]
        ],
        "project_tree": {
            "paths": [
                item.get("path")
                for item in data["tree"][:250]
            ],
            "truncated": data["tree_truncated"]
        },
        "generated_at": data["generated_at"]
    }

    json_content = json.dumps(
        export_data,
        indent=4,
        ensure_ascii=False
    )

    st.download_button(
        "⬇️ Download JSON Report",
        data=json_content,
        file_name="reporadar_report.json",
        mime="application/json",
        use_container_width=True
    )

    try:

        pdf_content = create_pdf_report(data)

        st.download_button(
            "⬇️ Download PDF Report",
            data=pdf_content,
            file_name="reporadar_report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    except Exception as error:

        st.warning(
            f"PDF report unavailable: {error}"
        )


# =========================================================
# 21. FOOTER
# =========================================================

st.divider()

st.markdown("""
<div style="text-align:center; color:#64748b; padding:15px;">
    <b>🛰️ RepoRadar</b><br>
    GitHub Repository Health & Documentation Intelligence<br>
    <span style="font-size:12px;">
        Built using Python, Streamlit and GitHub REST API
    </span>
</div>
""", unsafe_allow_html=True)
