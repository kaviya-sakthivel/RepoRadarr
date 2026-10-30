# 🚀 RepoRadar – GitHub Repository Health Analyzer

**Analyze, evaluate, and improve the quality of GitHub repositories with RepoRadar.**

RepoRadar is a Python-based web application that analyzes public GitHub repositories and generates an overall repository health score. It evaluates repository structure, documentation quality, development activity, contributors, programming languages, and project organization.

The application helps developers understand the strengths and weaknesses of their repositories through interactive visualizations, health reports, and actionable recommendations.

## ✨ Key Features

### 1. Repository Health Analysis
- Analyze public GitHub repositories using their URL.
- Evaluate repository quality using automated health checks.
- Generate an overall health score out of 100.
- Assign grades from A to F.
- Identify missing or incomplete repository components.

### 2. README Analyzer
- Calculate README word count.
- Detect headings and important sections.
- Check for Features, Installation, Usage, and Screenshots sections.
- Generate documentation quality scores.
- Provide suggestions to improve README documentation.

### 3. GitHub Activity Analysis
- Analyze recent commit activity.
- Identify repository contributors.
- Display contributor statistics.
- Analyze open and closed issues.
- Retrieve repository metadata.

### 4. Advanced Project Structure Analysis
- Detect total files and directories.
- Identify project type using repository files.
- Detect important files such as README, LICENSE, and `.gitignore`.
- Check for dependency manifests.
- Identify test directories.
- Detect Dockerfile and GitHub Actions workflows.
- Display project directory and file structure.

### 5. Interactive Dashboard
- Repository overview and statistics.
- Programming language distribution.
- Commit activity visualization.
- Contributor analysis.
- Issue analytics.
- Repository health scorecard.

### 6. Report Generation
- Download repository analysis as JSON.
- Generate downloadable PDF reports.
- View detailed repository health recommendations.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Interactive web application |
| GitHub REST API | Repository data collection |
| Requests | API communication |
| Pandas | Data processing |
| Plotly | Interactive visualizations |
| ReportLab | PDF report generation |
| Pytest | Testing |

## ⚙️ Installation and Setup

### Prerequisites
- Python 3.9 or above
- Git
- GitHub account

### Step 1: Clone the Repository

```bash
git clone https://github.com/kaviya-sakthivel/RepoRadarr.git
cd RepoRadarr
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure GitHub Token

Create a GitHub Personal Access Token with access to public repositories.

Set it as an environment variable named:

```text
REPO_RADAR_TOKEN
```

Do not hardcode your token in the source code or upload it to GitHub.

### Step 4: Run the Application

```bash
python -m streamlit run app.py
```

### Step 5: Open the Dashboard

Open the local URL displayed in your terminal, usually:

```text
http://localhost:8501
```

## 🧪 Run Tests

Execute the following command to run the test suite:

```bash
python -m pytest -q
```

## 📊 Scoring Methodology

RepoRadar calculates the overall repository score using two major components:

| Component | Weight |
|---|---:|
| Repository Health Score | 60% |
| README Documentation Score | 40% |

**Grade Classification:**

| Score | Grade |
|---|---|
| 85–100 | A |
| 70–84 | B |
| 50–69 | C |
| 35–49 | D |
| Below 35 | F |

The score helps developers identify areas that need improvement.

## 📁 Project Structure

```text
RepoRadarr/
│
├── app.py
├── reporadar_utils.py
├── requirements.txt
├── README.md
├── .gitignore
│
└── tests/
    └── test_app.py
```

## 🔐 Security

- GitHub access tokens are stored using environment variables.
- Tokens should never be committed to the repository.
- `.gitignore` helps prevent sensitive local files from being uploaded.

## 🚀 Future Enhancements

- AI-powered repository improvement suggestions.
- Historical repository health tracking.
- Automated code quality analysis.
- More advanced security and dependency analysis.
- Repository comparison and benchmarking.
- Support for additional programming languages.

## 🎯 Project Objective

The main objective of RepoRadar is to help developers maintain healthy, well-documented, and properly structured GitHub repositories.

By combining GitHub API integration, automated analysis, interactive visualizations, and downloadable reports, RepoRadar makes repository evaluation easier and more understandable.

## 👩‍💻 Developed By

**Kaviya Sakthivel**

GitHub: [@kaviya-sakthivel](https://github.com/kaviya-sakthivel)

---

⭐ If you find RepoRadar useful, consider giving this repository a star!