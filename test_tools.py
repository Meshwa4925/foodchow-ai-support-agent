from tools.order_tools import get_order, get_order_status
from tools.payment_tools import get_payment_status
from tools.printer_tools import get_printer_status
from tools.kds_tools import get_kds_status


print("ORDER")
print(get_order("1024"))

print("\nORDER STATUS")
print(get_order_status("1024"))

print("\nPAYMENT")
print(get_payment_status("1024"))

print("\nPRINTER")
print(get_printer_status("O001"))

print("\nKDS")
print(get_kds_status("O002"))

from tools.menu_tools import get_menu_status
print("\nMENU")
print(get_menu_status("O001"))