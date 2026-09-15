from agent.agent import run_agent
import json


print("\n========================================")
print("FOODCHOW GUARDRAILS TEST")
print("========================================")


message = (
    "My payment for order 1024 was successful "
    "but the order is still pending. I want a refund."
)

print("\nCustomer:", message)

result = run_agent(message)

print("\nFINAL RESULT")
print(json.dumps(result, indent=4))


print("\n========================================")
print("GUARDRAILS TEST COMPLETED")
print("========================================")