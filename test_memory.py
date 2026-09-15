from agent.agent import run_agent, memory
import json


print("\n========================================")
print("FOODCHOW CONVERSATION MEMORY TEST")
print("========================================")


# -----------------------------------------
# Message 1
# -----------------------------------------
print("\n\nCUSTOMER 1")
print("----------------------------------------")

message1 = "My POS is not working at outlet O001"

print("Customer:", message1)

result1 = run_agent(message1)

print("\nAgent Result:")
print(json.dumps(result1, indent=4))


# -----------------------------------------
# Show Memory After Message 1
# -----------------------------------------
print("\n\nMEMORY AFTER MESSAGE 1")
print("----------------------------------------")

memory.show_memory()


# -----------------------------------------
# Message 2
# -----------------------------------------
print("\n\nCUSTOMER 2")
print("----------------------------------------")

message2 = "What should I do now?"

print("Customer:", message2)

result2 = run_agent(message2)

print("\nAgent Result:")
print(json.dumps(result2, indent=4))


# -----------------------------------------
# Show Memory After Message 2
# -----------------------------------------
print("\n\nMEMORY AFTER MESSAGE 2")
print("----------------------------------------")

memory.show_memory()


# -----------------------------------------
# Message 3
# -----------------------------------------
print("\n\nCUSTOMER 3")
print("----------------------------------------")

message3 = "Is it still offline?"

print("Customer:", message3)

result3 = run_agent(message3)

print("\nAgent Result:")
print(json.dumps(result3, indent=4))


# -----------------------------------------
# Final Memory
# -----------------------------------------
print("\n\nFINAL CONVERSATION MEMORY")
print("----------------------------------------")

memory.show_memory()


print("\n========================================")
print("MEMORY TEST COMPLETED")
print("========================================")