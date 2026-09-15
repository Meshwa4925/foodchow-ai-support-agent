"""
FoodChow AI Support Agent
Phase 4 - Step 2
Agent Planner

This module creates a tool execution plan based on the detected issue type.
"""


class AgentPlanner:
    """
    Creates a step-by-step execution plan for the FoodChow support agent.
    """

    def __init__(self):
        self.plans = {
            "pos": [
                "verify_outlet",
                "get_restaurant",
                "get_pos_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ],

            "printer": [
                "verify_outlet",
                "get_restaurant",
                "get_printer_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ],

            "kds": [
                "verify_outlet",
                "get_restaurant",
                "get_kds_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ],

            "menu": [
                "verify_outlet",
                "get_restaurant",
                "get_menu_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ],

            "online_ordering": [
                "verify_outlet",
                "get_restaurant",
                "get_online_order_status",
                "get_menu_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ],

            "order": [
                "get_order",
                "get_order_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ],

            "payment": [
                "get_order",
                "get_order_status",
                "get_payment_status",
                "search_knowledge_base",
                "analyze_result",
                "decide_escalation"
            ]
        }

    def create_plan(self, issue_type):
        """
        Create a tool execution plan based on issue type.
        """

        issue_type = str(issue_type).lower().strip()

        if issue_type in self.plans:
            return {
                "success": True,
                "issue_type": issue_type,
                "plan": self.plans[issue_type].copy()
            }

        return {
            "success": False,
            "issue_type": issue_type,
            "plan": [],
            "error": f"No execution plan available for issue type: {issue_type}"
        }

    def display_plan(self, issue_type):
        """
        Display the generated plan in a readable format.
        """

        result = self.create_plan(issue_type)

        print("\n" + "=" * 50)
        print("AGENT EXECUTION PLAN")
        print("=" * 50)

        print(f"Issue Type: {issue_type}")

        if not result["success"]:
            print(f"Error: {result['error']}")
            return result

        print("\nSteps:")

        for index, step in enumerate(result["plan"], start=1):
            print(f"{index}. {step}")

        print("=" * 50)

        return result


# ---------------------------------------------------------
# Simple standalone test
# ---------------------------------------------------------

if __name__ == "__main__":

    planner = AgentPlanner()

    test_issue_types = [
        "pos",
        "printer",
        "kds",
        "menu",
        "online_ordering",
        "order",
        "payment"
    ]

    print("\nFOODCHOW AGENT PLANNER TEST")
    print("=" * 50)

    for issue_type in test_issue_types:

        result = planner.create_plan(issue_type)

        print(f"\nIssue Type: {issue_type}")
        print(f"Success: {result['success']}")

        if result["success"]:
            for number, step in enumerate(result["plan"], start=1):
                print(f"  {number}. {step}")

    print("\n" + "=" * 50)
    print("PLANNER TEST COMPLETED")
    print("=" * 50)