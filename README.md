# Proxmox SRE Incident Response Playbooks
This repository offers a collection of Proxmox VE Site Reliability Engineering (SRE) runbooks and automation tooling. This acts as a definitive operational hub for diagnosing, mitigating, and recovering from cluster-level incidents. The repository combines executable Markdown runbooks with a Python automation framework.

The Quarto-powered documentation portal is published via [GitHub Pages](https://aminbenmansour.github.io/sre-playbooks-proxmox/).

# 📂 Repository Structure

| Directory | Description |
| :--- | :--- |
| `docs/` | Quarto source files for the live documentation portal and incident post-mortems. |
| `runbooks/` | Actionable, step-by-step resolution guides organized by domain (e.g., `compute/`, `network/`). |
| `library/` | Core Python framework for API authentication and pre-flight safety checks. |
| `tests/` | PyTest suite ensuring the reliability of automation scripts before execution. |
| `.github/workflows/` | CI/CD pipelines for testing, linting, and auto-publishing to GitHub Pages. |

# 🏗️ Technology Stack
* **Platform**: Proxmox Virtual Environment (`PVE`) and Proxmox Backup Server (`PBS`).
* **Automation**: Python 3.10+.
* **Documentation**: Quarto (Markdown-based technical publishing).
* **Interactive Runbooks**: Marimo (reactive Python notebooks served locally).
* **Safety & Validation**:
  * **PyTest**: For mocking API states and verifying recovery logic.
  * **Pre-commit**: For enforcing code quality (`Black`/`Flake8`).
* **Deployment**: GitHub Actions for automated documentation rendering and testing coverage.

# 🚀 Getting Started
## Prerequisites
* Python 3.10+
* Quarto CLI (for local documentation preview)
* Pre-commit (`pip install pre-commit`)

## Environment Setup
```bash
git clone https://github.com/aminbenmansour/proxmox-sre-playbooks.git
cd proxmox-sre-playbooks

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/base.txt -r requirements/testing.txt -r requirements/formatting.txt

pre-commit install
```

# 🛠️ On-Call & Incident Response Workflow

## Pre-requisite: Export credentials and launch the runbook server
Before navigating the docs portal, export your PVE credentials and start Marimo:

```bash
source .venv/bin/activate

export PVE_CLUSTER_ENDPOINT="https://pve-cluster.example.com"
export PVE_USER="sre-api@pam"
export PVE_TOKEN_NAME="runbook-token"
export PVE_TOKEN="your-token-here"

marimo run runbooks/compute/unlock_pve_vms.py
```

Keep this terminal open. The docs site embeds the runbook at `localhost:2718` — the iframe will be live as soon as Marimo starts.

## Step 1: Locate the Runbook
Navigate to the `runbooks/` directory or open the rendered GitHub Pages documentation portal. Runbooks are organised by engineering domain (`compute/`, `network/`, `storage/`).

## Step 2: Run Pre-Flight Validation
Before applying destructive commands, invoke the Python safety module:
```bash
python3 -m library.pve_safety --check-quorum
```

## Step 3: Execute Recovery Steps
Open the relevant runbook page in the docs portal. The embedded Marimo app guides you through each step interactively — auth, detect, safety check, and unlock — with a required confirmation checkbox before any destructive action.

# 📖 Documentation Portal (Quarto & GitHub Pages)
The public documentation is authored in Quarto and hosted via GitHub Pages using `.github/workflows/render_quarto.yml`.

* `docs/runbook-explanation/`: Theoretical background, architectural risks, and the embedded interactive runbook.
* `docs/incident-reviews/`: Blameless post-mortems for edge-case failures.

To preview locally:
```bash
quarto preview docs
```

# 🧪 Testing & Code Quality
```bash
pytest --cov=library tests/
```

# 🤝 Contributing
1. All Python code modifications must include corresponding tests within `tests/`.
2. New runbooks must follow: **Auth → Detect → Safety check → Remediate → Validate**.
3. New Marimo runbooks (`.py`) go in `runbooks/<domain>/`. The `validate_runbooks.yml` CI job checks their syntax automatically.
4. Ensure the pre-commit hook runs successfully before opening a Pull Request.

## 🛡️ License
Apache License Version 2.0 — see [LICENSE](./LICENSE).
