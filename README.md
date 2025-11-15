# Bulut: AI Payment Agent

**Bulut** is an AI-powered payment assistant designed to turn natural-language commands into structured and secure blockchain transactions. It uses a **Large Language Model (LLM)** for accurate parsing and integrates with **Circle Developer-Controlled Wallets (W3S)** to enable non-custodial and gasless payments.

---

## Key Features

* **Natural Language Processing (NLP):** Converts phrases like "Send 50 USD to @alice for rent" into a precise Payment Intent JSON.
* **Payment Types:** Supports one-time payments, subscriptions, and split payments.
* **Gasless Transactions:** Uses Circle W3S and its **Paymaster** functionality to cover gas fees, providing a seamless user experience.
* **Fallback Mode:** Includes a **Mock Parser** and **Mock Circle Service** for local testing without API keys.
* **Asynchronous Design:** Built using `asyncio` and `httpx` for robust performance in web service environments.

---

## Project Configuration and Setup

The project requires API keys for two main services: the AI parsing engine and the Web3 wallet service.

### Environment Variables

You must set these variables either in a local `.env` file or directly in your Render service configuration:

| Variable | Service | Description | Required |
| :--- | :--- | :--- | :--- |
| `AIMLAPI_KEY` | AI/ML API | Your API key for the `gpt-4o` model via `aimlapi.com`. | Yes |
| `CIRCLE_API_KEY` | Circle W3S | Your API key for Circle’s developer-controlled wallets. | Yes (for real mode) |
| `CIRCLE_ENTITY_ID` | Circle W3S | Your Circle entity ID, used for transaction requests. | Yes (for real mode) |
| `CIRCLE_BASE_URL` | Circle W3S | Base URL for Circle's API (Default: `https://api.circle.com/v1/w3s`). | No |

### Dependencies

Install the necessary Python packages. These should be included in your `requirements.txt` for deployment on Render:

```bash
pip install openai httpx
````

---

## Code Structure

The project is logically divided into two main service modules:

### 1. `agent.py` (AI Parsing Module)

This module handles natural-language processing and output structuring.

| Class/Function          | Purpose                                                                                                                     |
| :---------------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| `RealAIAgent`           | The main interface that uses `AIMLAPI_KEY` and a detailed `SYSTEM_PROMPT` to parse text into validated payment-intent JSON. |
| `MockAIParser`          | Simple parsing logic based on Regular Expressions (RegEx), used as a fallback when the AI key is unavailable.               |
| `parse_payment_command` | The main entry-point function that routes the request to the real agent or the mock parser.                                 |

### 2. `circle_service.py` (Transaction Module)

This module manages actual Web3 transaction execution via Circle's API.

| Class/Function      | Purpose                                                                                                                   |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------ |
| `CircleService`     | Initializes the `httpx.AsyncClient` with authentication headers and manages connection logic.                             |
| `initiate_transfer` | Sends the transfer request to Circle W3S using the **Paymaster** function to sponsor gas fees, enabling gasless payments. |
| `_mock_wallets`     | In-memory storage used to simulate sender/receiver addresses (`@alice`, `@bob`) in development mode.                      |

---

## Local Execution and Testing

### Running Tests

The `agent.py` file includes a self-test block to demonstrate parsing functionality:

```bash
python agent.py
```

If successful, you will see output confirming whether the **Real AI Agent** or the **Mock Parser** was used, along with structured results for test commands such as "Send $50 to @alice for lunch".

### Integration Workflow

A typical payment flow involves using the output from the AI module as input for the Circle module:

1. A user sends a command (e.g., "Pay @bob 100 USD").
2. `parse_payment_command` returns a validated **Payment Intent JSON**:
   `{"amount": 100.0, "currency": "USD", "recipient": {"alias": "@bob"}, ...}`.
3. The application uses (`amount`, `recipient`) to look up the recipient’s **Circle Wallet Address**.
4. `CircleService.initiate_transfer` is called with the sender address, recipient address, and amount to execute the gasless blockchain payment.

---

## Deployment on Render

The project is structured for smooth deployment as a web service or background worker on Render.

### Deployment Checklist

* **Connect Repository:** Link your Git repository (GitHub/GitLab) to your Render account.
* **Service Type:** Choose a **Web Service** or **Background Worker** depending on how you expose functionality (e.g., via a REST API endpoint).
* **Build Command:** Ensure Render installs dependencies correctly (e.g., `pip install -r requirements.txt`).
* **Environment Variables:** Set the three required variables (`AIMLAPI_KEY`, `CIRCLE_API_KEY`, `CIRCLE_ENTITY_ID`) in the Render Dashboard.

