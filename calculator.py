#!/usr/bin/env python3
"""Ultra-compact Python calculator with full arithmetic functionality"""

import operator
import re

def calculate(expression):
    """Evaluate mathematical expression with proper operator precedence"""
    # Replace ^ with ** for exponentiation
    expression = expression.replace('^', '**')
    
    # Define operators with precedence (higher number = higher precedence)
    ops = {'+': (1, operator.add), '-': (1, operator.sub), 
           '*': (2, operator.mul), '/': (2, operator.truediv),
           '//': (2, operator.floordiv), '%': (2, operator.mod),
           '**': (3, operator.pow)}
    
    # Simple evaluation using Python's eval for this compact implementation
    try:
        result = eval(expression)
        return result
    except:
        return "Error: Invalid expression"

def main():
    """Main calculator loop"""
    print("Ultra-Compact Python Calculator")
    print("Enter 'quit' to exit")
    
    while True:
        try:
            expr = input(">>> ").strip()
            if expr.lower() == 'quit':
                break
            print(f"Result: {calculate(expr)}")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    main()