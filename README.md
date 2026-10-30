# RepoRadar 🛰️

**RepoRadar** is a small web app that analyzes public GitHub repositories and produces a transparent repository-health checklist.

## Features

- Fetches public repository metadata through the GitHub REST API
- Checks for a README, license, test-file/directory indicators, description, language data, and archived status
- Shows stars, forks, open issues, repository dates, and language breakdown
- Generates practical improvement suggestions
- Exports the report as JSON
- Includes automated tests for GitHub URL parsing

## Tech stack

- Python
- Streamlit
- Requests
- Pytest
- GitHub REST API

## Run locally

1. Install Python 3.10 or newer.
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Start the app:

   ```bash
   streamlit run app.py
   ```

7. Paste a public GitHub repository URL into the app.

## Run tests

```bash
python -m pytest -q
```

## How the score works

The score is a simple heuristic based on six checks: README present, license present, test indicator detected, description present, language data detected, and repository not archived. Each check contributes equally.

This score is **not** an official GitHub score or a validated measure of code quality. Finding test files does not prove that tests pass or that test coverage is adequate. Language statistics are reported by GitHub and do not assess code quality.

## Limitations

- The app currently analyzes public repositories.
- GitHub API rate limits may apply, especially for repeated unauthenticated requests.
- The first version checks root-level entries for README/license/test indicators; it does not recursively inspect every file.
- The app does not execute code from the analyzed repository.

## Roadmap

- [ ] Add recursive file-tree analysis
- [ ] Add GitHub Actions CI
- [ ] Add downloadable HTML report
- [ ] Add configurable scoring weights
- [ ] Add historical trend tracking

## License

No license has been selected yet. Add a license file before redistributing the project as open source.
