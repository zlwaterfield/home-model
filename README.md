# Home model

A simple Python tool to help you figure out if buying a home was a good investment compared to putting your money in the stock market. It considers your mortgage payments, home improvements, and other costs to give you a clear picture.

## Features

- Track all your home-related costs:
  - Down payment and closing costs
  - Monthly mortgage payments
  - Home improvements
  - Regular expenses (taxes, insurance, HOA)
- Compare against potential stock market returns
- See how much equity you're building
- Get a simple profit/loss analysis

## Quick start

1. Clone and set up:
```bash
git clone https://github.com/zlwaterfield/home-model
cd home-model
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create a CSV with your home costs (see example below)

3. Run it:
```bash
python index.py --csv your_costs.csv
```

### CSV example
```csv
category,description,amount,date,frequency
mortgage,term_years=25;annual_rate=5.2,400000,2024-11-27,
initial,Closing costs,23000,2024-11-27,
initial,Down payment,100000,2024-11-27,
recurring,Property Tax,3500,2024-11-27,annual
recurring,Home Insurance,150,2024-11-27,annual
improvement,Appliances,5500,2024-11-27,
improvement,Electrical,22000,2024-11-27,
improvement,Roof,10000,2024-11-27,
improvement,Kitchen,2000,2026-11-27,
improvement,Bathroom,2000,2028-11-27,
sale,6.0,800000,2029-12-01,
```

### Example output
<img width="913" alt="Screenshot 2024-11-28 at 8 50 10 PM" src="https://github.com/user-attachments/assets/bc59bbcd-e924-4523-8af5-bebd3ef6b2cb">

## Notes

- This is a work in progress! 
- Makes some basic assumptions about market returns
- Doesn't account for things like tax benefits or rental income
- Uses a simplified comparison model

## Requirements

- Python 3.x
- Basic Python packages (numpy, pandas)

Feel free to contribute or suggest improvements!
