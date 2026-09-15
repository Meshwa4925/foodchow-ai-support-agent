from agent.agent import run_agent
import json


print("\n========================================")
print("FOODCHOW ERROR HANDLING TEST")
print("========================================")


message = "My POS is not working at outlet O999"

print("\nCustomer:", message)

result = run_agent(message)

print("\nFINAL RESULT")
print(json.dumps(result, indent=4))


print("\n========================================")
print("ERROR HANDLING TEST COMPLETED")
print("========================================")