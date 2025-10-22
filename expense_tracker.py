import datetime
from supabase import create_client, Client
import dotenv
import os

# --- 1. CONNECT TO SUPABASE ---
# This is how it should look after you paste your links:
dotenv.load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ------------------------------------

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Successfully connected to Supabase!")
except Exception as e:
    print(f"Error connecting to Supabase: {e}")
    exit()

# --- 2. DEFINE YOUR FUNCTIONS ---

def format_inr(amount):
    """Format amount in Indian Rupees with thousands separator"""
    return f'₹{amount:,.2f}'

def store_expense(category, amount, note):
    """
    Stores a new expense in the 'labels' table.
    'time' is added automatically with the current timestamp.
    """
    try:
        if not category or not amount:
            print("Error: Category and amount are required!")
            return
            
        data = {
            "time": datetime.datetime.now().isoformat(),
            "category": category.strip(),
            "amount": float(amount),
            "note": note.strip() if note else ""
        }
        print("Attempting to store expense...")
        response = supabase.table("labels").insert(data).execute()
        if response.data:
            print(f"\nSuccessfully stored expense!")
            print(f"Debug info: {response.data}")  # This will help see what's being returned
        else:
            print("Warning: No data returned from insert operation")
    except ValueError as e:
        print(f"Error with data format: {e}")
    except Exception as e:
        print(f"Error storing expense: {e}")
        print(f"Debug info - Data attempted to store: {data}")

def fetch_all_expenses():
    """
    Fetches all expenses from the 'labels' table, ordered by time.
    """
    try:
        # Select from your 'labels' table
        response = supabase.table("labels").select("*").order("time", desc=True).execute()
        print("\n--- All Expenses ---")
        if response.data:
            for row in response.data:
                # Use your column names: label, time, category, amount, note
                print(f"ID: {row['label']}")
                print(f"  Time: {row['time']}")
                print(f"  Category: {row['category']}")
                print(f"  Amount: {format_inr(row['amount'])}")
                print(f"  Note: {row['note']}\n")
        else:
            print("No expenses found.")
        return response.data
    except Exception as e:
        print(f"Error fetching expenses: {e}")
        return None

def update_expense(label_id, new_data):
    """
    Updates an existing expense using its 'label' (UUID).
    new_data is a dictionary, e.g., {'amount': 25.50}
    """
    try:
        # Update in 'labels' table where 'label' column matches the ID
        response = supabase.table("labels").update(new_data).eq("label", label_id).execute()
        print(f"\nSuccessfully updated expense ID {label_id}")
    except Exception as e:
        print(f"Error updating expense: {e}")

def fetch_monthly_total(year, month):
    """
    Fetches the total expenses for a specific month and year.
    This requires the 'get_monthly_total' SQL function in Supabase.
    (See setup instructions below the code)
    """
    try:
        # Calls the SQL function you create in the Supabase dashboard
        response = supabase.rpc("get_monthly_total", {"p_year": year, "p_month": month}).execute()
        total = response.data
        if total:
            print(f"\nTotal for {month:02d}-{year}: {format_inr(total)}")
        else:
            # This can happen if there are no expenses for that month
            print(f"\nTotal for {month:02d}-{year}: ₹0.00")
        return total
    except Exception as e:
        print(f"Error fetching monthly total: {e}")
        print("!! Have you created the 'get_monthly_total' function in Supabase? See setup guide.")
        return None

# --- 3. CREATE A SIMPLE MENU TO USE THE APP ---

def main():
    while True:
        print("\n--- Expense Tracker Menu ---")
        print("1. Add new expense")
        print("2. View all expenses")
        print("3. Update an expense")
        print("4. Get monthly total (Visualize totals)")
        print("5. Exit")
        
        choice = input("Enter your choice (1-5): ")
        
        try:
            if choice == '1':
                # Add Expense (category, amount)
                try:
                    category = input("Enter category (e.g., Food, Transport): ").strip()
                    amount = float(input("Enter amount: "))
                    note = input("Enter a note (optional): ").strip()
                    store_expense(category, amount, note)
                except ValueError:
                    print("Error: Amount must be a valid number!")
                    continue
                    
            elif choice == '2':
                # Fetch all
                fetch_all_expenses()
                
            elif choice == '3':
                # Update Expense
                label_id = input("Enter the ID (label) of the expense to update: ")
                
                print("\nWhat fields do you want to update?")
                print("You can update multiple fields. Leave blank to skip.")
                
                new_data = {}
                
                # Category update
                new_category = input("Enter new category (or press Enter to skip): ")
                if new_category:
                    new_data['category'] = new_category
                
                # Amount update
                new_amount = input("Enter new amount (or press Enter to skip): ")
                if new_amount:
                    try:
                        new_data['amount'] = float(new_amount)
                    except ValueError:
                        print("Invalid amount format. Skipping amount update.")
                
                # Note update
                new_note = input("Enter new note (or press Enter to skip): ")
                if new_note:
                    new_data['note'] = new_note
                    
                if new_data:
                    update_expense(label_id, new_data)
                else:
                    print("No changes requested.")
                    
            elif choice == '4':  # Remove the period here
                # Fetch and display monthly totals
                try:
                    print("\nGet Total for a Specific Month")
                    year = int(input("Enter year (YYYY): "))
                    month = int(input("Enter month (1-12): "))
                    if not (1 <= month <= 12):
                        print("Error: Month must be between 1 and 12!")
                        continue
                    fetch_monthly_total(year, month)
                except ValueError:
                    print("Error: Please enter valid numbers for year and month!")
                    continue
                    
            elif choice == '5':
                # Exit
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please enter a number between 1 and 5.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            print("Please try again.")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()  