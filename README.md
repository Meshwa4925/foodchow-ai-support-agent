# FoodChow AI Support Agent

An AI-powered support agent for restaurant and outlet support operations. The system understands support queries, retrieves relevant knowledge from a local knowledge base, executes registered tools to verify operational data, maintains conversation context, creates support tickets when escalation is required, and provides grounded responses.

## Features

- Natural-language support query handling
- Issue classification
- Knowledge-base retrieval using RAG
- Tool calling for operational checks
- Conversation memory
- Agent planning and workflow orchestration
- Support-ticket creation
- Duplicate-ticket prevention
- Human escalation
- Guardrails for sensitive actions
- Error handling
- Local JSON-based operational data
- CLI and Streamlit support

## Architecture

```text
User Query
    |
    v
Agent / Conversation Layer
    |
    +----> Issue Classification
    |
    +----> Conversation Memory
    |
    +----> Agent Planner
    |          |
    |          v
    |      Execution Plan
    |
    +----> RAG Connector
    |          |
    |          v
    |      Knowledge Base
    |
    +----> Tool Registry
    |          |
    |          +--> Restaurant Tools
    |          +--> Order Tools
    |          +--> Payment Tools
    |          +--> Printer Tools
    |          +--> KDS Tools
    |          +--> POS Tools
    |          +--> Menu Tools
    |
    +----> Result Analysis
    |
    +----> Escalation / Support Ticket
    |
    v
Grounded Support Response

Technologies

Python
Streamlit
RAG (Retrieval-Augmented Generation)
FAISS
Sentence Transformer embeddings
JSON
Markdown knowledge base

Knowledge Base and RAG

The Knowledge_base/ directory contains support documentation for:

Accounts
KDS
Menu Management
Online Ordering
Payments
POS
Printers
Restaurant Setup
Troubleshooting

The RAG pipeline creates embeddings for the knowledge-base documents and stores the searchable vector index inside:
rag/vector_store/

The agent retrieves relevant knowledge before generating troubleshooting guidance.

This helps the system provide responses based on the available support documentation.

Implemented Tools

The project includes tools for:

Restaurant
Verify outlet
Get restaurant information
Orders
Get order
Get order status
Payments
Get payment status
Printers
Get printer status
KDS
Get KDS status
POS
POS-related operational checks
Menu
Menu-related operational checks
Online Ordering
Online-order operational checks
Support
Create support ticket
Handle escalation

The tools use local JSON data to simulate operational APIs.

Agent Workflow

The agent follows this general workflow:

Receive the user's support query.
Identify the issue type.
Extract relevant information such as outlet ID or order ID.
Search the knowledge base using RAG.
Create an execution plan.
Execute the required tools.
Validate tool results.
Analyze the result.
Decide whether the issue is resolved or requires escalation.
Create a support ticket when required.
Store conversation context.
Return a grounded response to the user.

Conversation Memory

The agent maintains conversation context for follow-up messages.

example:
User:
My printer is not working at outlet O001.

Agent:
Checks the outlet and printer status and provides troubleshooting.

User:
No, printer is still not working.

Agent:
Understands this as a continuation of the same issue and
reuses the existing support-ticket context instead of
creating a duplicate ticket.
This allows the agent to handle multi-turn conversations more effectively.

Human Escalation

If an issue cannot be resolved through automated troubleshooting, the system can create a support ticket.

The agent returns the ticket ID to the user.

The system also checks whether an existing support ticket already exists for the same active issue. This helps prevent duplicate tickets during follow-up conversations.

Example:
Support Ticket:
FC-2632E97D

Guardrails

The system is designed to avoid blindly performing sensitive or unsupported actions.

The agent should verify required information before taking controlled actions.

If the system cannot verify an operation, it should explain the limitation instead of claiming that the operation was completed.

Error Handling
The project includes handling and testing for situations such as:

Missing order
Unknown restaurant
Unknown outlet
Invalid tool response
Tool failure
API/unavailable service simulation
Invalid JSON
Missing data
Conflicting information
Unresolved support issues

The agent should not hallucinate successful results when a tool fails or data is unavailable.

Important Payment Scenario
A key support scenario is:
Payment was deducted but my order is still pending.
Expected workflow:

User Query
    |
    v
Identify Payment / Order Issue
    |
    v
Check Order Status
    |
    v
Check Payment Status
    |
    v
Compare Results
    |
    +---- Payment successful + Order pending
    |              |
    |              v
    |        Explain verified state
    |              |
    |              v
    |        Escalate if required
    |
    v
Grounded Response

The agent should never claim that the order was confirmed unless the available operational data verifies it.

Demonstration Scenarios
1. Printer Issue
My printer is not working at outlet O001

The agent verifies the outlet, restaurant and printer status, retrieves relevant troubleshooting knowledge and escalates when necessary.

2. POS Issue
My POS is not working at outlet O001

The agent identifies the POS issue, checks the available operational information and provides troubleshooting or escalation guidance.

3. Payment Issue
Payment was deducted but my order is still pending.

The agent checks payment and order information before deciding the next action.

4. Conversation Memory
User:
My printer is not working at outlet O001

User:
No, printer is still not working

The second message continues the same issue and should reuse the existing context.

5. Sensitive Action
Refund my order.

The system should not blindly perform a refund without the required verification and authorization. The issue should be handled through the appropriate controlled workflow or escalation.

Installation

Clone the repository:

git clone https://github.com/Meshwa4925/foodchow-ai-support-agent.git

Go to the project directory:

cd foodchow-ai-support-agent

Create a virtual environment:

python -m venv venv

Activate the virtual environment on Windows:

venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Running the Project

To run the Streamlit application:

streamlit run app.py

The main agent workflow can also be executed through the Python agent/CLI implementation.

Testing

The repository includes tests for:

test_tools.py
test_memory.py
test_guardrails.py
test_error_handling.py

Run them individually:python test_tools.py
python test_memory.py
python test_guardrails.py
python test_error_handling.py

Limitations
Operational APIs are simulated using local JSON data.
Production FoodChow APIs are not connected.
The knowledge base is limited to the supplied support documentation.
Tool functionality depends on the available local data.
Production deployment would require authentication and authorization.
Production systems would require monitoring, logging and stronger security controls.

Future Improvements
Connect to real FoodChow APIs
Add production authentication
Add role-based authorization
Add database-backed conversation memory
Improve RAG retrieval and ranking
Add more automated end-to-end tests
Add structured logging and monitoring
Add production chat interface
Add approval workflows for sensitive actions
Improve support-ticket management

Assignment Requirement Coverage

| Requirement         | Implementation                                     |
| ------------------- | -------------------------------------------------- |
| Source Code         | Python agent, planner, tools and RAG modules       |
| Knowledge Base      | Markdown files in `Knowledge_base/`                |
| RAG                 | Embeddings and vector search                       |
| Tool Calling        | Tool modules and tool registry                     |
| Agent Workflow      | Planner and agent orchestration                    |
| Conversation Memory | `agent/memory.py`                                  |
| Human Handoff       | Support-ticket creation and escalation             |
| Guardrails          | Agent checks and `test_guardrails.py`              |
| Error Handling      | Agent/tool validation and `test_error_handling.py` |
| Demonstration       | Printer, POS, Payment and Memory scenarios         |

Repository

GitHub Repository:

https://github.com/Meshwa4925/foodchow-ai-support-agent

Conclusion

FoodChow AI Support Agent demonstrates an AI-driven restaurant support workflow combining RAG-based knowledge retrieval, operational tool calling, agent planning, conversation memory, guardrails, error handling and human escalation.

The system is designed to provide grounded and verifiable support responses instead of blindly generating answers.