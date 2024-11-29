import argparse
from model import HomeInvestmentCalculator
from rich import print as rprint
from rich.panel import Panel

# Setup argument parser
parser = argparse.ArgumentParser(description='Home Investment Calculator')
parser.add_argument('--csv', help='Path to CSV file with home costs')
args = parser.parse_args()
if not args.csv:
    raise ValueError("CSV file is required")

# Run
print("\n" + "=" * 50)
print("💰 Home Investment Calculator")
print("=" * 50)
calculator = HomeInvestmentCalculator()

# Import from CSV using command line argument
print(f"\n📊 Importing data from {args.csv}...")
calculator.import_from_csv(args.csv)

# Calculate returns
print("\n🔄 Calculating investment returns...")
df, summary = calculator.calculate_returns()

print("=" * 50)
print("\n📝 Investment Analysis Report")
print("=" * 50)
rprint(Panel(calculator.generate_report(df, summary), style="green"))
