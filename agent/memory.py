class ConversationMemory:
    """
    Simple conversation memory for the FoodChow AI Support Agent.

    Stores:
    - Conversation messages
    - Issue type
    - Restaurant ID
    - Outlet ID
    - Order ID
    - Important investigation information
    """

    def __init__(self):
        self.messages = []
        self.context = {
            "issue_type": None,
            "restaurant_id": None,
            "outlet_id": None,
            "order_id": None
        }

    # ========================================================
    # ADD MESSAGE
    # ========================================================

    def add_message(self, role, message):
        self.messages.append({
            "role": role,
            "message": message
        })

    # ========================================================
    # SET CONTEXT
    # ========================================================

    def set_context(self, key, value):

        if key in self.context:
            self.context[key] = value

    # ========================================================
    # GET CONTEXT
    # ========================================================

    def get_context(self, key):

        return self.context.get(key)

    # ========================================================
    # GET ALL CONTEXT
    # ========================================================

    def get_all_context(self):

        return self.context.copy()

    # ========================================================
    # GET CONVERSATION
    # ========================================================

    def get_messages(self):

        return self.messages.copy()

    # ========================================================
    # GET LAST MESSAGE
    # ========================================================

    def get_last_message(self):

        if not self.messages:
            return None

        return self.messages[-1]

    # ========================================================
    # CLEAR MEMORY
    # ========================================================

    def clear(self):

        self.messages = []

        self.context = {
            "issue_type": None,
            "restaurant_id": None,
            "outlet_id": None,
            "order_id": None
        }

    # ========================================================
    # DISPLAY MEMORY
    # ========================================================

    def show_memory(self):

        print("\n========================================")
        print("CONVERSATION MEMORY")
        print("========================================")

        print("\nContext:")

        for key, value in self.context.items():
            print(f"{key}: {value}")

        print("\nConversation:")

        for message in self.messages:
            print(
                f"{message['role']}: "
                f"{message['message']}"
            )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("========================================")
    print("CONVERSATION MEMORY TEST")
    print("========================================")

    memory = ConversationMemory()

    # Add conversation
    memory.add_message(
        "customer",
        "My menu is not showing online."
    )

    memory.add_message(
        "agent",
        "Please provide your outlet ID."
    )

    memory.add_message(
        "customer",
        "O002"
    )

    # Store context
    memory.set_context(
        "issue_type",
        "online_ordering"
    )

    memory.set_context(
        "outlet_id",
        "O002"
    )

    # Display
    memory.show_memory()

    print("\n========================================")
    print("TEST VALUES")
    print("========================================")

    print(
        "Issue Type:",
        memory.get_context("issue_type")
    )

    print(
        "Outlet ID:",
        memory.get_context("outlet_id")
    )

    print(
        "Last Message:",
        memory.get_last_message()
    )