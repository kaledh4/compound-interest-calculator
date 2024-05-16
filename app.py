from flask import Flask, render_template, request, make_response
from datetime import datetime, timedelta
import csv
import io

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def investment_calculator():
    if request.method == 'POST':
        initial_balance = float(request.form['initial_balance'])
        currency = request.form['currency']
        interest_rate = float(request.form['interest_rate']) / 100
        days = int(request.form['days'])
        months = int(request.form['months'])
        years = int(request.form['years'])
        include_all_days = 'include_all_days' in request.form
        daily_reinvest_rate = float(request.form['daily_reinvest_rate']) / 100
        additional_contributions = request.form['additional_contributions']
        additional_contribution_amount = float(request.form['additional_contribution_amount'])
        additional_contribution_skip_days = int(request.form['additional_contribution_skip_days'])
        drawdown_percentage = float(request.form['drawdown_percentage']) / 100
        
        total_days = years * 365 + months * 30 + days
        business_days = total_days if include_all_days else total_days * 5 // 7
        
        current_balance = initial_balance
        total_interest = 0
        additional_deposits = 0
        total_cash_taken_out = 0
        earnings_data = []
        
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=total_days)
        
        for day in range(total_days):
            if include_all_days or (day % 7 not in [4, 5]):  # Skip Fridays and Saturdays if not including all days
                daily_interest = current_balance * interest_rate
                total_interest += daily_interest
                
                if day >= additional_contribution_skip_days:
                    if additional_contributions == 'Deposits':
                        current_balance += additional_contribution_amount
                        additional_deposits += additional_contribution_amount
                    elif additional_contributions == 'Withdrawals':
                        current_balance -= additional_contribution_amount
                        total_cash_taken_out += additional_contribution_amount
                
                reinvested_amount = daily_interest * daily_reinvest_rate
                drawdown_amount = daily_interest * drawdown_percentage
                personal_amount = daily_interest - reinvested_amount - drawdown_amount
                
                current_balance += reinvested_amount
                total_cash_taken_out += personal_amount
                
                earnings_data.append([
                    (start_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                    f'{current_balance:.2f}',
                    f'{daily_interest:.2f}',
                    f'{reinvested_amount:.2f}',
                    f'{drawdown_amount:.2f}',
                    f'{personal_amount:.2f}'
                ])
        
        investment_value = current_balance
        percentage_profit = (investment_value - initial_balance) / initial_balance * 100
        
        csv_data = io.StringIO()
        writer = csv.writer(csv_data)
        writer.writerow(['Date', 'Balance', 'Daily Interest', 'Reinvested Amount', 'Drawdown Amount', 'Personal Amount'])
        writer.writerows(earnings_data)
        
        csv_filename = 'earnings_data.csv'
        csv_content = csv_data.getvalue()
        
        return render_template('result.html',
                               investment_value=f'{currency}{investment_value:.2f}',
                               total_interest=f'{currency}{total_interest:.2f}',
                               additional_deposits=f'{currency}{additional_deposits:.2f}',
                               percentage_profit=f'{percentage_profit:.2f}%',
                               total_cash_taken_out=f'{currency}{total_cash_taken_out:.2f}',
                               total_days=total_days,
                               business_days=business_days,
                               daily_interest_rate=f'{interest_rate:.2%}',
                               end_date=end_date.strftime('%b %d, %Y'),
                               initial_balance=f'{currency}{initial_balance:.2f}',
                               start_date=start_date.strftime('%b %d, %Y'),
                               earnings_data=earnings_data,
                               csv_filename=csv_filename,
                               csv_content=csv_content)
    
    return render_template('index.html')

@app.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename):
    csv_content = request.args.get('csv_content', '')
    response = make_response(csv_content)
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'
    return response

if __name__ == '__main__':
    app.run()