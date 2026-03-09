# Contributing to Think Better

First off, thank you for considering contributing to **Think Better**! It's people like you that make the open-source community such a great place to learn, inspire, and create.

This document provides guidelines and instructions for contributing to this project.

## How Can I Contribute?

### Reporting Bugs & Requesting Features
- Use the [GitHub Issues](https://github.com/HoangTheQuyen/think-better/issues) tab.
- Check if the issue or feature request already exists before creating a new one.
- Describe the issue clearly, including steps to reproduce, what you expected to happen, and what actually happened.

### Contributing Code or New AI Skills

We welcome pull requests! Here is the standard workflow to contribute code:

#### 1. Fork and Clone
1. **Fork** the repository on GitHub by clicking the "Fork" button in the top right corner.
2. **Clone** your forked repository to your local machine:
   ```bash
   git clone https://github.com/<your-username>/think-better.git
   cd think-better
   ```

#### 2. Create a Branch
Create a new branch for your feature or bug fix:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

#### 3. Make Changes & Test
- Make your code changes. If you are adding a new AI skill, follow the structure in `.agents/skills/`.
- Run the tests to ensure everything is working correctly:
  ```bash
  go test ./...
  ```
- Before committing, make sure the embedded skills are prepared:
  ```bash
  make embed-prep
  ```

#### 4. Commit Your Changes
We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
```bash
git add .
git commit -m "feat: add new decision framework for product launch"
```

#### 5. Push and Create a Pull Request (PR)
1. **Push** your branch to your forked repository:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Go to the original `HoangTheQuyen/think-better` repository on GitHub.
3. Click the **"Compare & pull request"** button next to your recently pushed branch.
4. Fill out the PR template describing your changes, why they are needed, and how they were tested.
5. Submit the Pull Request!

## Development Setup

To work on `think-better` locally, you will need:
- **Go 1.25+**
- **Python 3** (for running the skill analysis checker scripts)

Thank you for your contributions! 🚀
