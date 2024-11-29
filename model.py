import pandas as pd
from datetime import datetime, date
import numpy as np
import numpy_financial as npf

class HomeInvestmentCalculator:
    def __init__(self):
        self.initial_costs = []
        self.recurring_costs = []
        self.improvements = []
        self.mortgage = None
        
    def add_initial_cost(self, description, amount, date):
        """Add initial costs like down payment, closing costs"""
        self.initial_costs.append({
            'description': description,
            'amount': amount,
            'date': pd.to_datetime(date)
        })
        
    def add_mortgage(self, principal, annual_rate, term_years, start_date):
        """Add mortgage details for amortization calculation"""
        self.mortgage = {
            'principal': principal,
            'annual_rate': annual_rate,
            'term_years': term_years,
            'start_date': pd.to_datetime(start_date),
            'monthly_rate': annual_rate / 12 / 100,
            'total_payments': term_years * 12
        }
        
        # Calculate monthly payment using amortization formula
        r = self.mortgage['monthly_rate']
        n = self.mortgage['total_payments']
        p = principal
        self.mortgage['monthly_payment'] = p * (r * (1 + r)**n) / ((1 + r)**n - 1)
        
    def calculate_mortgage_payment_split(self, payment_number):
        """Calculate the principal and interest split for a given payment number"""
        if not self.mortgage:
            return 0, 0
            
        r = self.mortgage['monthly_rate']
        p = self.mortgage['principal']
        pmt = self.mortgage['monthly_payment']
        
        # Calculate remaining principal before this payment
        remaining_principal = p * (1 + r)**payment_number - \
                            pmt * ((1 + r)**payment_number - 1) / r
                            
        # Calculate interest portion
        interest_payment = remaining_principal * r
        
        # Calculate principal portion
        principal_payment = pmt - interest_payment
        
        return principal_payment, interest_payment
        
    def add_recurring_cost(self, description, amount, start_date, frequency='monthly'):
        """Add recurring costs like property tax, insurance"""
        self.recurring_costs.append({
            'description': description,
            'amount': amount,
            'start_date': pd.to_datetime(start_date),
            'frequency': frequency
        })
        
    def add_improvement(self, description, amount, date):
        """Add home improvements like renovations"""
        self.improvements.append({
            'description': description,
            'amount': amount,
            'date': pd.to_datetime(date)
        })

    def import_from_csv(self, filepath):
        """
        Import costs from a CSV file.
        Required columns: category, description, amount, date
        Special categories: initial, recurring, mortgage, improvement, sale
        """
        try:
            df = pd.read_csv(filepath)
            required_columns = ['category', 'description', 'amount', 'date']
            
            # Track sale info
            self.sale_info = None
            
            if not all(col in df.columns for col in required_columns):
                missing = [col for col in required_columns if col not in df.columns]
                raise ValueError(f"Missing required columns: {missing}")
            
            for _, row in df.iterrows():
                category = row['category'].lower().strip()
                description = row['description']
                amount = float(row['amount'])
                date = row['date']
                
                if category == 'sale':
                    # Store sale information
                    self.sale_info = {
                        'price': amount,
                        'date': pd.to_datetime(date),
                        'closing_costs_percent': float(description) if description else 6.0
                    }
                    continue
                    
                if category == 'initial':
                    self.add_initial_cost(description, amount, date)
                    
                elif category == 'recurring':
                    frequency = row.get('frequency', 'monthly').lower().strip()
                    if frequency not in ['monthly', 'annual']:
                        print(f"Warning: Invalid frequency '{frequency}' for {description}. Defaulting to monthly.")
                        frequency = 'monthly'
                    self.add_recurring_cost(description, amount, date, frequency)
                    
                elif category == 'improvement':
                    self.add_improvement(description, amount, date)
                    
                elif category == 'mortgage':
                    # Expect description format: "term_years:30;annual_rate:3.5"
                    try:
                        params = dict(item.split("=") for item in description.split(";"))
                        self.add_mortgage(
                            principal=amount,
                            annual_rate=float(params['annual_rate']),
                            term_years=int(params['term_years']),
                            start_date=date
                        )
                    except Exception as e:
                        print(f"Error parsing mortgage parameters: {str(e)}")
                        raise
                    
                else:
                    print(f"Warning: Unknown category '{category}' for {description}. Row skipped.")
                    
            print(f"Successfully imported {len(df)} rows.")
            
        except Exception as e:
            print(f"Error importing CSV: {str(e)}")
            raise
        
    def calculate_market_comparison(self, df, sp500_annual_return=0.07):
        """
        Calculate equivalent market returns if each cash flow was invested in S&P 500
        Parameters:
            df: DataFrame with all cash flows
            sp500_annual_return: Annual return rate for S&P 500 (default 7%)
        """
        market_df = df.copy()
        monthly_rate = (1 + sp500_annual_return) ** (1/12) - 1
        end_date = market_df['date'].max()
        
        # Calculate what each investment would be worth at the end
        market_values = []
        for _, row in market_df.iterrows():
            months_invested = (end_date - row['date']).days / 30.44  # approximate months
            
            # Only negative amounts (costs) are considered as investments
            if row['amount'] < 0:
                future_value = -row['amount'] * (1 + monthly_rate) ** months_invested
                market_values.append(future_value)
        
        # Calculate key metrics
        total_invested = -df[df['amount'] < 0]['amount'].sum()  # Sum of all costs
        total_withdrawn = df[df['amount'] > 0]['amount'].sum()  # Sum of all income (sale proceeds)
        sp500_final_value = sum(market_values)  # What investments would be worth in S&P 500
        
        return {
            'S&P 500 Final Value': sp500_final_value,
            'S&P 500 Net Profit': sp500_final_value - total_invested,
            'Total Invested': total_invested,
            'Total Withdrawn': total_withdrawn,
            'Annual Return Rate Used': sp500_annual_return * 100
        }
    
    def calculate_returns(self):
        """Calculate investment returns and compare to S&P 500"""
        if not self.sale_info:
            raise ValueError("Sale information must be provided in CSV file")
        
        return self._calculate_returns(
            estimated_sale_price=self.sale_info['price'],
            sale_date=self.sale_info['date'],
            closing_costs_percent=self.sale_info['closing_costs_percent']
        )
    
    def _calculate_returns(self, estimated_sale_price, sale_date, closing_costs_percent=6):
        """Internal method containing the original calculate_returns logic"""
        sale_date = pd.to_datetime(sale_date)
        all_costs = []
        accumulated_equity = 0
        
        # Add initial costs
        for cost in self.initial_costs:
            all_costs.append({
                'date': cost['date'],
                'amount': -cost['amount'],
                'description': cost['description'],
                'type': 'Initial Cost'
            })
            
        # Add improvements
        for improvement in self.improvements:
            all_costs.append({
                'date': improvement['date'],
                'amount': -improvement['amount'],
                'description': improvement['description'],
                'type': 'Improvement'
            })
            
        # Add mortgage payments with principal/interest split
        if self.mortgage:
            current_date = self.mortgage['start_date']
            payment_number = 0
            
            while current_date <= sale_date and payment_number < self.mortgage['total_payments']:
                principal_payment, interest_payment = self.calculate_mortgage_payment_split(payment_number)
                
                # Add principal payment (becomes equity)
                all_costs.append({
                    'date': current_date,
                    'amount': -principal_payment,
                    'description': 'Mortgage Principal',
                    'type': 'Equity Building'
                })
                
                # Add interest payment (true cost)
                all_costs.append({
                    'date': current_date,
                    'amount': -interest_payment,
                    'description': 'Mortgage Interest',
                    'type': 'Interest Cost'
                })
                
                accumulated_equity += principal_payment
                current_date += pd.DateOffset(months=1)
                payment_number += 1
            
        # Add other recurring costs
        for cost in self.recurring_costs:
            current_date = cost['start_date']
            while current_date <= sale_date:
                all_costs.append({
                    'date': current_date,
                    'amount': -cost['amount'],
                    'description': cost['description'],
                    'type': 'Recurring Cost'
                })
                if cost['frequency'] == 'monthly':
                    current_date += pd.DateOffset(months=1)
                elif cost['frequency'] == 'annual':
                    current_date += pd.DateOffset(years=1)
                    
        # Create DataFrame and sort by date
        df = pd.DataFrame(all_costs)
        if not df.empty:
            df = df.sort_values('date')
        
        # Calculate remaining mortgage balance at sale
        remaining_mortgage = 0
        if self.mortgage:
            months_elapsed = (sale_date - self.mortgage['start_date']).days / 30.44  # approximate months
            if months_elapsed < self.mortgage['total_payments']:
                p = self.mortgage['principal']
                r = self.mortgage['monthly_rate']
                pmt = self.mortgage['monthly_payment']
                n = months_elapsed
                remaining_mortgage = p * (1 + r)**n - pmt * ((1 + r)**n - 1) / r
        
        # Add sale proceeds (after remaining mortgage and closing costs)
        closing_costs = estimated_sale_price * (closing_costs_percent / 100)
        net_sale_proceeds = estimated_sale_price - closing_costs - remaining_mortgage
        
        # Use concat instead of append
        sale_row = pd.DataFrame([{
            'date': sale_date,
            'amount': net_sale_proceeds,
            'description': 'Sale Proceeds (After Mortgage Payoff)',
            'type': 'Sale'
        }])
        
        df = pd.concat([df, sale_row], ignore_index=True)
        
        # Calculate cumulative investment
        df['cumulative_investment'] = df['amount'].cumsum()
        
        # Calculate holding period in years using pandas
        total_years = (sale_date - df['date'].min()).days / 365.25
        
        # Calculate IRR using numpy
        dates = df['date'].values
        amounts = df['amount'].values
        
        # Convert dates to years from start for IRR calculation
        first_date = pd.to_datetime(dates[0])
        years = np.array([(pd.to_datetime(d) - first_date).days / 365.25 for d in dates])
        
        # Calculate IRR
        try:
            irr = npf.irr(amounts)
            annual_irr = (1 + irr) ** (1) - 1
        except Exception as e:
            print(f"Warning: Could not calculate IRR: {str(e)}")
            annual_irr = float('nan')
        
        # Calculate S&P 500 equivalent return
        sp500_annual_return = 0.07  # 7% assumed return
        market_comparison = self.calculate_market_comparison(df, sp500_annual_return)

        # Add purchase information to summary
        initial_costs = df[df['type'] == 'Initial Cost']
        down_payment = 0
        purchase_price = 0
        purchase_date = None
        
        if not initial_costs.empty:
            down_payment = -initial_costs[initial_costs['description'].str.contains('down payment', case=False)]['amount'].iloc[0] \
                if not initial_costs[initial_costs['description'].str.contains('down payment', case=False)].empty else 0
            purchase_price = down_payment + (self.mortgage['principal'] if self.mortgage else 0)
            purchase_date = initial_costs.iloc[0]['date']

        initial_investment = -df[df['type'].isin(['Initial Cost', 'Improvement'])]['amount'].sum()

        # Update summary dictionary
        summary = {
            'Total Initial Investment': initial_investment,
            'Total Cash Outflow': -df[df['amount'] < 0]['amount'].sum(),
            'Accumulated Equity': accumulated_equity,
            'Remaining Mortgage': remaining_mortgage,
            'Sale Proceeds': net_sale_proceeds,
            'Net Profit': df['amount'].sum(),
            'Holding Period (Years)': total_years,
            'Annual IRR': annual_irr * 100 if not np.isnan(annual_irr) else float('nan'),
            'S&P 500 Final Value': market_comparison['S&P 500 Final Value'],
            'S&P 500 Net Profit': market_comparison['S&P 500 Net Profit'],
            'S&P 500 Annual Return Used': market_comparison['Annual Return Rate Used'],
            'Outperformance vs S&P 500': df['amount'].sum() - market_comparison['S&P 500 Net Profit'],
            'Purchase Price': purchase_price,
            'Down Payment': down_payment,
            'Purchase Date': purchase_date,
            'Sale Price': estimated_sale_price,
            'Sale Date': sale_date,
            'Total Invested': market_comparison['Total Invested'],
            'Total Withdrawn': market_comparison['Total Withdrawn']
        }
        
        return df, summary
    
    def generate_report(self, df, summary):
        """Generate a formatted report of the investment analysis"""
        report = "Home Investment Analysis Report\n"
        report += "=" * 30 + "\n\n"

        # Purchase Information
        if summary['Purchase Date']:
            purchase_date = summary['Purchase Date'].strftime('%Y-%m-%d')
            report += "Purchase Information:\n"
            report += f"Purchase Price: ${summary['Purchase Price']:,.2f}\n"
            report += f"Down Payment: ${summary['Down Payment']:,.2f}\n"
            report += f"Purchase Date: {purchase_date}\n\n"
        else:
            report += "Purchase Information: Not available\n\n"

        # Sale Information
        sale_date = summary['Sale Date'].strftime('%Y-%m-%d')
        report += "Sale Information:\n"
        report += f"Sale Price: ${summary['Sale Price']:,.2f}\n"
        report += f"Sale Date: {sale_date}\n"
        
        # Add holding period note
        years = int(summary['Holding Period (Years)'])
        months = int((summary['Holding Period (Years)'] - years) * 12)
        report += f"(House owned for {years} years and {months} months)\n\n"

        report += "Detailed Cost Breakdown:\n"
        type_totals = df.groupby('type')['amount'].sum()
        for cost_type, total in type_totals.items():
            report += f"{cost_type}: ${abs(total):,.2f}\n"

        report += "\nInvestment Summary:\n"
        report += f"Total Initial Investment: ${summary['Total Initial Investment']:,.2f}\n"
        report += f"Total Cash Outflow: ${summary['Total Cash Outflow']:,.2f}\n"
        report += f"Accumulated Equity: ${summary['Accumulated Equity']:,.2f}\n"
        report += f"Remaining Mortgage: ${summary['Remaining Mortgage']:,.2f}\n"
        report += f"Sale Proceeds: ${summary['Sale Proceeds']:,.2f}\n"
        report += f"Net Profit: ${summary['Net Profit']:,.2f}\n"
        report += f"Holding Period: {summary['Holding Period (Years)']:.1f} years\n"
        report += f"Annual IRR: {summary['Annual IRR']:.1f}%\n\n"
        
        report += "\nS&P 500 Investment Comparison:\n"
        report += "=" * 30 + "\n"
        report += "If you had invested all your housing costs in the S&P 500 instead:\n"
        report += f"Total Money Spent (Invested): ${summary['Total Invested']:,.2f}\n"
        report += f"Final Sale Proceeds (Withdrawn): ${summary['Total Withdrawn']:,.2f}\n"
        report += f"S&P 500 Investment Worth Today: ${summary['S&P 500 Final Value']:,.2f}\n"
        report += f"S&P 500 Net Profit: ${summary['S&P 500 Net Profit']:,.2f}\n"
        report += f"(Using {summary['S&P 500 Annual Return Used']:.1f}% annual return)\n"
        
        # Calculate ROIs using the same base (total cash outflow)
        total_cash_outflow = summary['Total Cash Outflow']
        
        home_roi = (summary['Net Profit'] / total_cash_outflow) * 100
        sp500_roi = (summary['S&P 500 Net Profit'] / total_cash_outflow) * 100
        
        report += "\nReturn Comparison:\n"
        report += f"Total Cash Invested: ${total_cash_outflow:,.2f}\n"
        report += f"Home Investment Return: ${summary['Net Profit']:,.2f} ({home_roi:.1f}%)\n"
        report += f"S&P 500 Return: ${summary['S&P 500 Net Profit']:,.2f} ({sp500_roi:.1f}%)\n"
        report += f"ROI Difference: {(home_roi - sp500_roi):.1f}%\n"
        report += f"Absolute Dollar Difference: ${summary['Outperformance vs S&P 500']:,.2f}\n"
        
        # Add additional context
        report += "\nNote: ROIs are calculated based on total cash invested "
        report += "($978,190.68) over the entire period.\n"
        
        return report
