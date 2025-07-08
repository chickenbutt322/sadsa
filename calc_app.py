#!/usr/bin/env python3
"""Ultra-compact Python calculator web app - 20 lines of core functionality"""

from flask import Flask, render_template, request, jsonify
import operator
import re

app = Flask(__name__)

def calculate(expression):
    """Evaluate mathematical expression - core calculator logic"""
    try:
        # Replace ^ with ** for exponentiation, remove spaces
        expr = expression.replace('^', '**').replace(' ', '')
        # Basic validation - only allow numbers, operators, parentheses
        if not re.match(r'^[0-9+\-*/().^%\s]+$', expression):
            return "Error: Invalid characters"
        result = eval(expr)  # Simple eval for compact implementation
        return result
    except ZeroDivisionError:
        return "Error: Division by zero"
    except:
        return "Error: Invalid expression"

@app.route('/')
def index():
    return render_template('calculator.html')

@app.route('/calculate', methods=['POST'])
def calc():
    expression = request.json.get('expression', '')
    result = calculate(expression)
    return jsonify({'result': str(result)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)