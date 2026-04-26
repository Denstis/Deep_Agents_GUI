"""
Math Tools - Mathematical computation using SymPy for DeepAgents
"""

import logging
from typing import Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Check if SymPy is available
try:
    from sympy import symbols, Eq, solve, sympify
    SYMPY_AVAILABLE = True
    logger.info("SymPy math solver available")
except ImportError:
    SYMPY_AVAILABLE = False
    logger.warning("SymPy not available - install with: pip install sympy")


class MathTools:
    """Mathematical computation tools using SymPy."""
    
    @staticmethod
    @tool
    def calculate(expression: str) -> str:
        """Evaluate a mathematical expression safely.
        
        Args:
            expression: Mathematical expression to evaluate (e.g., "2 + 2", "sqrt(16)", "sin(pi/2)").
            
        Returns:
            Result of the calculation.
        """
        if not SYMPY_AVAILABLE:
            logger.warning("Calculation requested but SymPy not available")
            return "Error: Calculator is not available. Please install sympy package."
        
        try:
            logger.info(f"Calculating expression: '{expression}'")
            # Safely evaluate the expression using sympify
            result = sympify(expression, evaluate=True)
            result_str = str(result)
            logger.info(f"Calculation result: {result_str}")
            return f"Result of '{expression}': {result_str}"
        except Exception as e:
            logger.error(f"Calculation failed: {str(e)}")
            return f"Error calculating '{expression}': {str(e)}"
    
    @staticmethod
    @tool
    def solve_equation(equation: str, variable: str = "x") -> str:
        """Solve an algebraic equation.
        
        Args:
            equation: Equation to solve (e.g., "x**2 - 4 = 0", "2*x + 3 = 7").
            variable: Variable to solve for (default: "x").
            
        Returns:
            Solution(s) to the equation.
        """
        if not SYMPY_AVAILABLE:
            return "Error: Equation solver is not available. Please install sympy package."
        
        try:
            logger.info(f"Solving equation: '{equation}' for variable '{variable}'")
            # Parse the equation
            if "=" in equation:
                left, right = equation.split("=", 1)
                eq = Eq(sympify(left.strip()), sympify(right.strip()))
            else:
                # Assume expression equals zero
                eq = sympify(equation)
            
            # Define the variable
            var = symbols(variable)
            
            # Solve the equation
            solution = solve(eq, var)
            
            if isinstance(solution, list):
                solution_str = ", ".join(str(s) for s in solution)
            else:
                solution_str = str(solution)
            
            logger.info(f"Equation solution: {solution_str}")
            return f"Solution for '{equation}': {variable} = {solution_str}"
        except Exception as e:
            logger.error(f"Equation solving failed: {str(e)}")
            return f"Error solving '{equation}': {str(e)}"
