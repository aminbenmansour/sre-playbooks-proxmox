# Proxmox SRE Incident Response Playbooks
This repository offers a collection of Proxmox VE Site Reliability Engineering (SRE) runbooks and automation tooling. This acts as a definitive operational hub for diagnosing, mitigating, and recovering from cluster-level incidents.  The repository combines executable Markdown runbooks with a Python automation framework.

The Quarto-powered documentation portal published via [GitHub Pages](https://aminbenmansour.github.io/sre-playbooks-proxmox/).

# 📂 Repository Structure
The project is structured to separate production-ready runbooks, automation logic, robust testing, and user-facing documentation:

| Directory | Description |
| :--- | :--- |
| `docs/` | Quarto source files for the live documentation portal and incident post-mortems. |
| `runbooks/` | Actionable, step-by-step resolution guides organized by domain (e.g., `compute/`, `network/`). |
| `library/` | Core Python framework for API authentication and pre-flight safety checks. |
| `tests/` | PyTest suite ensuring the reliability of automation scripts before execution. |
| `.github/workflows/	` | CI/CD pipelines for testing, linting, and auto-publishing to GitHub Pages. |

# 🏗️ Technology Stack
This project uses a layered approach to ensure infrastructure changes are safe, repeatable, and well-documented.
* **Platform**: Proxmox Virtual Environment (`PVE`) and Proxmox Backup Server (`PBS`).
* **Automation**: Python 3.10+.
* **Documentation**: Quarto (Markdown-based technical publishing).
* **Safety & Validation**:
  * **PyTest**: For mocking API states and verifying recovery logic.
  * **Pre-commit**: For enforcing code quality (`Black`/`Flake8`).
* **Deployment**: GitHub Actions for automated documentation rendering and testing coverage.

# 🚀 Getting Started
## Prerequisites
Ensure your local environment matches the production runtime constraints:
* Python 3.10+
* Quarto CLI (for local documentation preview)
* Pre-commit (pip install pre-commit)

## Environment Setup
Clone the repository and initialize the virtual environment alongside formatting hooks:
```bash
# Clone the repository
git clone https://github.com/aminbenmansour/proxmox-sre-playbooks.git
cd proxmox-sre-playbooks

# Setup Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt -r requirements/testing.txt -r requirements/formatting.txt

# Install Git pre-commit hooks
pre-commit install
```
# 🛠️ On-Call & Incident Response Workflow
When an alert fires or a cluster anomaly is detected, use this workflow to mitigate the issue:

## Step 1: Locate the Runbook
Navigate directly to the `runbooks/` directory or search the rendered GitHub Pages documentation portal. Runbooks are structured strictly by engineering domains (e.g., `compute/`, `network/`, `storage/`).

## Step 2: Run Pre-Flight Validation
Before applying destructive commands (such as clearing cluster locks), invoke the Python safety module to verify cluster health and avoid split-brain scenarios:
```bash
export PVE_CLUSTER_ENDPOINT="https://pve-cluster.example.com"
export PVE_USER="sre-api@pam"
export PVE_TOKEN_ID="monitoring@pve!sre-token"
export PVE_TOKEN="super-secret-token"

# Verify API connectivity and cluster quorum safety
python3 -m library.pve_safety --check-quorum
```

### Step 3: Execute Recovery Steps
Open the relevant markdown file (e.g., `runbooks/compute/unlock_pve_vms.md`) and follow the triage tree. Runbooks utilize clear, declarative blocks:
* **Symptoms**: High-level log entries or GUI patterns confirming the issue.
* **Impact**: Criticality assessment of what services or nodes are degraded.
* **Mitigation**: Safe, sequential commands to restore standard operational capabilities.

# 📖 Documentation Portal (Quarto & GitHub Pages)
The public documentation is authored using Quarto and hosted automatically via GitHub Pages using the `.github/workflows/render_quarto.yml` action. It maps raw operational runbooks into highly readable explanatory guides and tracking records.

* `docs/runbook-explanation/`: Contains the theoretical background and architectural risks behind running automated recovery commands.

* `docs/incident-reviews/`: Holds internal blameless post-mortems to ensure continuous learning from edge-case failures.

To serve and preview the documentation portal locally with hot-reloading:
```bash
quarto preview docs
```

# 🧪 Testing & Code Quality
To guarantee automation logic never compounds a live incident, all code alterations must pass comprehensive local validation frameworks:

* Static Analysis & Linting: Managed automatically via .pre-commit-config.yaml using `Black` and `Flake8`.
* Unit Testing: Driven via `pytest` to mock Proxmox API failure modes, state responses, and validation boundaries.
* Execute the test suite locally:
```bash
pytest --cov=library tests/
```

# 🤝 Contributing
Because this repository is public, contributions that improve cluster resilience are welcome. Please adhere to these guidelines:
1. All Python code modifications must include corresponding tests within the `tests/` path.
2. New runbooks must follow the uniform standard: Problem Statement --> Diagnostic Check --> Safe Resolution.
3. Ensure the pre-commit hook runs successfully before opening a Pull Request.

## 🛡️ License
This project is licensed under the [LICENSE](./LICENSE) file included in this repository.

Currently **Apache License Version 2.0**.
