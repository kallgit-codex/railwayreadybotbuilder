"""
Cost calculation utilities for OpenAI API usage
"""
import os
from typing import Dict, Tuple

# Default GPT-4o pricing (per 1,000 tokens)
DEFAULT_INPUT_RATE = 0.03   # $0.03 per 1K input tokens
DEFAULT_OUTPUT_RATE = 0.06  # $0.06 per 1K output tokens

class CostCalculator:
    """Calculate costs for OpenAI API usage with configurable rates"""
    
    def __init__(self):
        # Load rates from environment variables or use defaults
        self.input_rate = float(os.environ.get('OPENAI_INPUT_RATE', DEFAULT_INPUT_RATE))
        self.output_rate = float(os.environ.get('OPENAI_OUTPUT_RATE', DEFAULT_OUTPUT_RATE))
    
    def calculate_costs(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """
        Calculate costs for input and output tokens
        
        Args:
            input_tokens: Number of input/prompt tokens
            output_tokens: Number of output/completion tokens
            
        Returns:
            Dictionary with input_cost, output_cost, and total_cost
        """
        input_cost = (input_tokens / 1000) * self.input_rate
        output_cost = (output_tokens / 1000) * self.output_rate
        total_cost = input_cost + output_cost
        
        return {
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(total_cost, 6)
        }
    
    def get_rates(self) -> Dict[str, float]:
        """Get current pricing rates"""
        return {
            'input_rate': self.input_rate,
            'output_rate': self.output_rate
        }
    
    def update_rates(self, input_rate: float = None, output_rate: float = None):
        """Update pricing rates"""
        if input_rate is not None:
            self.input_rate = input_rate
        if output_rate is not None:
            self.output_rate = output_rate

# Global instance
cost_calculator = CostCalculator()