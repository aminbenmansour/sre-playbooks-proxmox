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

# 🛠 Technology Stack
This project uses a layered approach to ensure infrastructure changes are safe, repeatable, and well-documented.
* **Platform**: Proxmox Virtual Environment (`PVE`) and Proxmox Backup Server (`PBS`).
* **Automation**: Python 3.10+.
* **Documentation**: Quarto (Markdown-based technical publishing).
* **Safety & Validation**:
  * **PyTest**: For mocking API states and verifying recovery logic.
  * **Pre-commit**: For enforcing code quality (`Black`/`Flake8`).
* **Deployment**: GitHub Actions for automated documentation rendering and testing coverage.
