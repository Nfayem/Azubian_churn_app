
---

# Contributing to Churn Predictor App

Thank you for your interest in contributing to the Churn Predictor App! We welcome and appreciate all contributions from the community. Whether you're reporting a bug, suggesting a feature, improving documentation, or contributing code, your input is valuable to us.

## Table of Contents
- [Contributing to Churn Predictor App](#contributing-to-churn-predictor-app)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [How to Contribute](#how-to-contribute)
    - [Reporting Bugs](#reporting-bugs)
    - [Suggesting Features](#suggesting-features)
    - [Improving Documentation](#improving-documentation)
    - [Contributing Code](#contributing-code)
  - [Development Workflow](#development-workflow)
    - [Setting Up Your Environment](#setting-up-your-environment)
    - [Making Changes](#making-changes)
    - [Testing](#testing)
    - [Submitting Changes](#submitting-changes)
  - [Style Guidelines](#style-guidelines)
    - [Coding Standards](#coding-standards)
    - [Commit Messages](#commit-messages)
  - [License](#license)

## Code of Conduct

Please note that this project adheres to a [Code of Conduct](https://github.com/Nfayem/Churn_Predictor/blob/DevOps/CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report any unacceptable behavior to [sdi@azubiafrica.com](mailto:sdi@azubiafrica.com).

## How to Contribute

### Reporting Bugs

If you encounter a bug or have a question while using the Churn Predictor App, please follow these steps:

1. **Search Existing Issues**: Before submitting a new issue, check if the problem has already been reported. This helps avoid duplicates.
2. **Create a New Issue**: If the issue doesn’t already exist, open a new issue. Please provide as much detail as possible, including steps to reproduce the problem, the environment in which it occurred, and any relevant logs or screenshots.

### Suggesting Features

If you have an idea to enhance the app, we’d love to hear it! To suggest a new feature:

1. **Check for Existing Suggestions**: Review the existing issues to see if your idea has already been suggested.
2. **Open a New Issue**: If your idea is new, open an issue describing the feature. Please include details on the proposed functionality, potential use cases, and any relevant mockups or diagrams.

### Improving Documentation

Clear and thorough documentation is critical for the success of the Churn Predictor App. If you spot errors, outdated information, or opportunities for improvement:

1. **Edit Directly**: If you’re comfortable, feel free to edit the documentation directly and submit a pull request (PR).
2. **Open an Issue**: If you’re unsure about the change or want to discuss it first, open an issue with your suggestions.

### Contributing Code

We welcome contributions in the form of code. Before starting, please:

1. **Discuss**: Consider discussing your proposed changes with us first. You can start a conversation by opening an issue or joining an existing discussion.
2. **Fork the Repository**: Fork the repository to your GitHub account and create a new branch for your changes.
3. **Write Tests**: If you’re adding new functionality or fixing a bug, please include tests to ensure the changes work as expected.

## Development Workflow

### Setting Up Your Environment

To set up a local development environment:

1. **Fork the Repository**: Fork the [Churn Predictor App repository](https://github.com/Nfayem/Churn_Predictor.git) to your own GitHub account.
2. **Clone the Repository**: Clone your fork locally.
   ```bash
   git clone https://github.com/<your-username>/Churn_Predictor.git
   ```
3. **Install Dependencies**: Navigate to the project directory and install the required packages.
   ```bash
   cd Churn_Predictor
   pip install -r LP4_STAPP_requirements.txt
   ```
4. **Run the App Locally**: Start the Streamlit app to ensure everything is working.
   ```bash
   streamlit run Churn_Predictor.py
   ```

### Making Changes

When you’re ready to make changes:

1. **Create a New Branch**: Always create a new branch for your work.
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Implement Changes**: Make your changes in the branch.

### Testing

Please ensure your changes don’t break existing functionality:

1. **Run Tests**: Run the app and any existing tests to ensure everything works.
2. **Add New Tests**: If applicable, add new tests for your changes.

### Submitting Changes

When your changes are ready:

1. **Commit Your Changes**: Write clear and concise commit messages.
   ```bash
   git add .
   git commit -m "Add detailed description of your changes"
   ```
2. **Push to Your Fork**: Push your changes to your forked repository.
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Open a Pull Request**: Submit a PR to the main repository. In the PR description, link to any relevant issues and provide a summary of your changes.

## Style Guidelines

### Coding Standards

Please adhere to the following standards:

- **Python Style**: Follow PEP 8 for Python code.
- **Documentation**: Write clear and concise comments where necessary. Use docstrings for functions, classes, and methods.

### Commit Messages

Good commit messages are essential for understanding the history of a project. Please:

- **Use the Imperative Mood**: "Fix bug" instead of "Fixed bug".
- **Be Descriptive**: Explain the "what" and "why" of the change.
- **Reference Issues**: If your change addresses an issue, reference it in the commit message.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---
