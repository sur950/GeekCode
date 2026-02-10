# Calculator module with bugs - needs debugging
# This is sample input for Task 4: Debug Failing Test Suite

from typing import Union, List

Number = Union[int, float]


class Calculator:
    """A simple calculator with various operations."""

    def __init__(self):
        self.history: List[str] = []

    def add(self, a: Number, b: Number) -> Number:
        """Add two numbers."""
        result = a + b
        self._record(f"{a} + {b} = {result}")
        return result

    def subtract(self, a: Number, b: Number) -> Number:
        """Subtract b from a."""
        result = a - b
        self._record(f"{a} - {b} = {result}")
        return result

    def multiply(self, a: Number, b: Number) -> Number:
        """Multiply two numbers."""
        result = a * b
        self._record(f"{a} * {b} = {result}")
        return result

    def divide(self, a: Number, b: Number) -> Number:
        """Divide a by b."""
        # BUG 1: No check for division by zero
        result = a / b
        self._record(f"{a} / {b} = {result}")
        return result

    def percentage(self, value: Number, percent: Number) -> Number:
        """Calculate percentage of a value."""
        # BUG 2: Float precision issue - returns imprecise results
        result = value * percent / 100
        self._record(f"{percent}% of {value} = {result}")
        return result

    def sum_range(self, n: int) -> int:
        """Sum all integers from 1 to n (inclusive)."""
        # BUG 3: Off-by-one error - range should include n
        total = 0
        for i in range(n):  # Should be range(n + 1) or range(1, n + 1)
            total += i
        self._record(f"sum(1..{n}) = {total}")
        return total

    def calculate_expression(self, a: Number, b: Number, c: Number) -> Number:
        """Calculate: a + b * c (should follow order of operations)."""
        # BUG 4: Incorrect operator precedence - adds before multiplying
        result = (a + b) * c  # Should be a + (b * c)
        self._record(f"{a} + {b} * {c} = {result}")
        return result

    def safe_divide(self, a: Number, b: Number) -> Number:
        """Safely divide with default value on error."""
        # BUG 5: Doesn't handle None input
        if b == 0:
            return 0
        return a / b  # Will crash if a is None

    def average(self, numbers: List[Number]) -> float:
        """Calculate the average of a list of numbers."""
        if not numbers:
            return 0.0
        return sum(numbers) / len(numbers)

    def power(self, base: Number, exponent: int) -> Number:
        """Raise base to the power of exponent."""
        return base ** exponent

    def factorial(self, n: int) -> int:
        """Calculate factorial of n."""
        if n < 0:
            raise ValueError("Factorial not defined for negative numbers")
        if n <= 1:
            return 1
        result = 1
        for i in range(2, n + 1):
            result *= i
        return result

    def _record(self, operation: str) -> None:
        """Record an operation in history."""
        self.history.append(operation)

    def get_history(self) -> List[str]:
        """Get operation history."""
        return self.history.copy()

    def clear_history(self) -> None:
        """Clear operation history."""
        self.history.clear()
