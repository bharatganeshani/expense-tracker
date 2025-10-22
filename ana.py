from expense_tracker import fetch_all_expenses, SUPABASE_URL, SUPABASE_KEY
import matplotlib.pyplot as plt
from datetime import datetime
from collections import defaultdict
import numpy as np
import sys
from typing import Union

DEBUG = False  # Set to True to see detailed error messages

# Enhanced style configuration with better text handling
plt.rcParams.update({
    'figure.figsize': (14, 8),  # Larger default size
    'figure.dpi': 100,
    'axes.facecolor': '#ffffff',
    'figure.facecolor': '#ffffff',
    'axes.grid': True,
    'grid.color': '#e0e0e0',
    'grid.alpha': 0.5,
    'axes.labelsize': 12,
    'axes.titlesize': 16,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'font.family': 'sans-serif',
    'font.size': 12,
    'figure.autolayout': True,  # Better automatic layout
})

def format_inr(amount: Union[int, float]) -> str:
    """Format amount in Indian Rupees with thousands separator"""
    return f'₹{amount:,.2f}'

def process_data(all_data):
    """Helper function to process and organize data"""
    if not all_data or not isinstance(all_data, list):
        raise ValueError("Invalid or empty data received")
        
    dates, amounts, categories = [], [], []
    category_totals = defaultdict(float)
    monthly_totals = defaultdict(float)
    
    for item in all_data:
        try:
            # Validate required fields exist
            if not all(k in item for k in ['amount', 'time', 'category']):
                raise KeyError(f"Missing required fields in data: {item}")
                
            amount = float(item['amount'])
            if amount < 0:
                print(f"Warning: Negative amount found: ${amount}")
                
            date = datetime.fromisoformat(item['time'].split('T')[0])
            category = str(item['category']).strip()
            if not category:
                category = "Uncategorized"
            
            dates.append(date)
            amounts.append(amount)
            categories.append(category)
            
            category_totals[category] += amount
            monthly_totals[date.strftime("%Y-%m")] += amount
            
        except Exception as e:
            if DEBUG:
                print(f"Debug - Data item: {item}")
                print(f"Debug - Error: {str(e)}")
            else:
                print(f"Skipping invalid data point: {type(e).__name__}")
            continue
    
    if not dates:
        raise ValueError("No valid data points found after processing")
        
    return dates, amounts, categories, category_totals, monthly_totals

def plot_daily_expenses(dates, amounts):
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Create gradient colors based on amount
    colors = plt.cm.YlOrRd(np.linspace(0.3, 0.8, len(amounts)))
    bars = ax.bar(dates, amounts, color=colors, alpha=0.7)
    
    # Add trend line
    z = np.polyfit(range(len(dates)), amounts, 1)
    p = np.poly1d(z)
    ax.plot(dates, p(range(len(dates))), "r--", alpha=0.8, label='Trend')
    
    # Customize appearance
    ax.set_title('Daily Expenses Overview', pad=20, fontweight='bold', fontsize=16)
    ax.set_xlabel('Date', fontweight='bold', labelpad=10)
    ax.set_ylabel('Amount (₹)', fontweight='bold', labelpad=10)
    
    # Smart label placement
    every_nth = max(len(dates) // 10, 1)  # Show only every nth label
    for idx, label in enumerate(ax.get_xticklabels()):
        if idx % every_nth != 0:
            label.set_visible(False)
    
    # Add value labels with smart positioning
    max_amount = max(amounts)
    for bar in bars:
        height = bar.get_height()
        label_position = height + (max_amount * 0.02)  # Add small offset
        ax.text(bar.get_x() + bar.get_width()/2., label_position,
                format_inr(height), 
                ha='center', va='bottom',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))
    
    # Add total amount annotation
    total = sum(amounts)
    ax.text(0.02, 0.95, f'Total: {format_inr(total)}', 
            transform=ax.transAxes,
            bbox=dict(facecolor='white', edgecolor='gray', alpha=0.9))
    
    plt.xticks(rotation=45, ha='right')
    plt.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

def plot_category_pie(category_totals):
    fig, ax = plt.subplots(figsize=(10, 10))
    
    # Sort and prepare data
    categories_sorted = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    labels = []
    sizes = []
    
    # Only show top 3 categories, group others
    if len(categories_sorted) > 3:
        top_categories = categories_sorted[:3]
        other_sum = sum(x[1] for x in categories_sorted[3:])
        labels = [x[0] for x in top_categories] + ['Other']
        sizes = [x[1] for x in top_categories] + [other_sum]
    else:
        labels = [x[0] for x in categories_sorted]
        sizes = [x[1] for x in categories_sorted]

    # Bright, distinct colors
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#f39c12']
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(sizes, 
                                     labels=labels,
                                     colors=colors[:len(sizes)],
                                     autopct='',  # We'll add labels manually
                                     radius=0.75,
                                     labeldistance=1.1,
                                     wedgeprops={'edgecolor': 'white', 
                                               'linewidth': 2,
                                               'alpha': 0.9})
    
    # Add percentage and amount labels inside wedges
    for i, (wedge, size) in enumerate(zip(wedges, sizes)):
        ang = (wedge.theta2 + wedge.theta1)/2.
        percentage = size/sum(sizes)*100
        
        # Amount closer to center
        center_r = 0.45
        x = center_r * np.cos(np.deg2rad(ang))
        y = center_r * np.sin(np.deg2rad(ang))
        plt.text(x, y, format_inr(size), 
                ha='center', va='center',
                fontsize=11, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.5))
        
        # Percentage further out
        outer_r = 0.65
        x = outer_r * np.cos(np.deg2rad(ang))
        y = outer_r * np.sin(np.deg2rad(ang))
        plt.text(x, y, f'{percentage:.1f}%', 
                ha='center', va='center',
                fontsize=10, fontweight='bold',
                color='#2c3e50')
    
    # Enhance category labels
    plt.setp(texts, size=12, weight="bold")
    
    # Add title
    plt.title('Expense Distribution', 
             pad=20, fontweight='bold', fontsize=14)
    
    # Add total in center with fancy box
    total = sum(sizes)
    center_text = f'Total\n{format_inr(total)}'
    bbox_props = dict(boxstyle="round,pad=0.5", 
                     fc='white', 
                     ec='#95a5a6', 
                     alpha=0.95)
    plt.text(0, 0, center_text, 
             ha='center', va='center',
             bbox=bbox_props,
             fontsize=13, fontweight='bold',
             color='#2c3e50')
    
    plt.axis('equal')
    plt.tight_layout(pad=1.5)
    plt.show()

def plot_monthly_trend(monthly_totals):
    fig, ax = plt.subplots(figsize=(14, 8))
    
    months = sorted(monthly_totals.keys())
    values = [monthly_totals[m] for m in months]
    
    # Plot line with better spacing
    ax.plot(months, values, '-', color='#2ecc71', linewidth=2, zorder=2)
    
    # Add markers with white edge for better visibility
    ax.scatter(months, values, color='#2ecc71', s=100, 
               edgecolor='white', linewidth=2, zorder=3)
    
    # Smart label placement
    max_val = max(values)
    for i, (month, value) in enumerate(zip(months, values)):
        # Alternate label positions above and below points
        if i % 2 == 0:
            va = 'bottom'
            offset = max_val * 0.02
        else:
            va = 'top'
            offset = -max_val * 0.02
        ax.text(month, value + offset, format_inr(value), 
                ha='center', va=va, fontweight='bold',
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))
    
    # Customize appearance
    ax.set_title('Monthly Expense Trends', pad=20, fontweight='bold')
    ax.set_xlabel('Month', fontweight='bold', labelpad=10)
    ax.set_ylabel('Total Amount (₹)', fontweight='bold', labelpad=10)
    
    # Add average line with better placement
    avg = np.mean(values)
    ax.axhline(y=avg, color='#e74c3c', linestyle='--', alpha=0.5, zorder=1)
    ax.text(months[0], avg, f' Average: {format_inr(avg)} ', 
            va='bottom', ha='left', color='#e74c3c',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))
    
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.show()

def show_statistics(amounts, category_totals):
    stats_text = f"""
    📊 EXPENSE STATISTICS 📊
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🔸 Total Expenses: {format_inr(sum(amounts))}
    🔸 Average Daily:  {format_inr(np.mean(amounts))}
    🔸 Maximum:        {format_inr(max(amounts))}
    🔸 Minimum:        {format_inr(min(amounts))}
    🔸 Transactions:   {len(amounts)}
    🔸 Top Category:   {max(category_totals.items(), key=lambda x: x[1])[0]}
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """
    print(stats_text)

def main():
    try:
        print("Fetching expense data...")
        all_data = fetch_all_expenses()
        
        if not all_data:
            print("No data found in the database.")
            return

        print(f"Processing {len(all_data)} records...")
        dates, amounts, categories, category_totals, monthly_totals = process_data(all_data)
        print(f"Successfully processed {len(dates)} valid records.")

        while True:
            try:
                print("\n📈 EXPENSE ANALYTICS MENU 📈")
                print("1. Daily Expenses Bar Chart")
                print("2. Category Distribution Pie Chart")
                print("3. Monthly Trend Line Chart")
                print("4. Show Statistics Summary")
                print("5. Show All Visualizations")
                print("6. Toggle Debug Mode")
                print("7. Exit")

                choice = input("\nEnter your choice (1-7): ").strip()

                if choice == '1':
                    print("Generating daily expenses chart...")
                    plot_daily_expenses(dates, amounts)
                elif choice == '2':
                    print("Generating category distribution chart...")
                    plot_category_pie(category_totals)
                elif choice == '3':
                    print("Generating monthly trend chart...")
                    plot_monthly_trend(monthly_totals)
                elif choice == '4':
                    show_statistics(amounts, category_totals)
                elif choice == '5':
                    print("Generating all visualizations...")
                    plot_daily_expenses(dates, amounts)
                    plot_category_pie(category_totals)
                    plot_monthly_trend(monthly_totals)
                    show_statistics(amounts, category_totals)
                elif choice == '6':
                    global DEBUG
                    DEBUG = not DEBUG
                    print(f"Debug mode {'enabled' if DEBUG else 'disabled'}")
                elif choice == '7':
                    print("Exiting analytics...")
                    break
                else:
                    print("Invalid choice. Please enter a number between 1 and 7.")

            except Exception as e:
                print(f"Error displaying chart: {str(e) if DEBUG else type(e).__name__}")
                print("Please try again.")

    except Exception as e:
        print("\nERROR: Analytics failed to run properly!")
        if DEBUG:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error type: {type(e).__name__}")
            print("Enable debug mode for more details.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    finally:
        plt.close('all')  # Clean up any open plots