# Synthetic Clickstream & E-Commerce Simulator (In Souteast Asian and PH Market)

## Overview

This repository was built as a portfolio project for **Eskwelabs Innovation Fellowship** Internship Program. As an EIF, the goal is of this project is "to help learners practice with datasets that feel close to real business, social impact, education, workforce, or operations problems without using sensitive or confidential real-world data."

We are asked to create a mathematical model, develop a dataset generator, use the generator to generate a dataset, carry out a sample EDA of the dataset, and create a challenge statement that can allow learners to practice with the dataset.

This project contains a synthetic data pipeline built in Python (`numpy`, `pandas`). It is explicitly designed to model the behavioral economics of Tier-1 Southeast Asian digital retail platforms (e.g., Shopee, Lazada, TikTok Shop).

### Core Mathematical Engine

* **Markov Chain Funnel Decay:** Simulates a realistic ~2.25% checkout conversion rate.
* **Log-Normal Pricing Models:** Uses hidden latent variables to generate heavy-tailed financial transactions.
* **Exponential Decay Timestamps:** Models UI navigation and session duration.
* **Intentional Data Degradation:** Injects a hardcoded `ERR_VERSION_NOT_FOUND` in telemetry bugs for legacy Android devices to test downstream data cleaning. (See <https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0279942>)

### Setup

#### Create a virtual environment (venv)

* Windows:
```python -m venv venv```

* Mac/Linux:
```python3 -m venv venv```

#### Create a virtual environment

* Windows:
```venv\Scripts\activate```

* Mac/Linux:
```source venv/bin/activate```

#### Install requirements inside venv

```pip install -r requirements.txt```
