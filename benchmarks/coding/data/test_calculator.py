# Test suite for calculator module - has 5 failing tests
# This is sample input for Task 4: Debug Failing Test Suite

import pytest
from calculator import Calculator


class TestCalculator:
    """Test suite for Calculator class."""

    @pytest.fixture
    def calc(self):
        """Create a fresh calculator instance."""
        return Calculator()

    # ===== Passing Tests =====

    def test_add(self, calc):
        """Test addition."""
        assert calc.add(2, 3) == 5
        assert calc.add(-1, 1) == 0
        assert calc.add(0.1, 0.2) == pytest.approx(0.3)

    def test_subtract(self, calc):
        """Test subtraction."""
        assert calc.subtract(5, 3) == 2
        assert calc.subtract(3, 5) == -2

    def test_multiply(self, calc):
        """Test multiplication."""
        assert calc.multiply(4, 5) == 20
        assert calc.multiply(-2, 3) == -6

    def test_average(self, calc):
        """Test average calculation."""
        assert calc.average([1, 2, 3, 4, 5]) == 3.0
        assert calc.average([]) == 0.0

    def test_power(self, calc):
        """Test power function."""
        assert calc.power(2, 3) == 8
        assert calc.power(5, 0) == 1

    def test_factorial(self, calc):
        """Test factorial calculation."""
        assert calc.factorial(5) == 120
        assert calc.factorial(0) == 1

    def test_history(self, calc):
        """Test operation history."""
        calc.add(1, 2)
        calc.multiply(3, 4)
        history = calc.get_history()
        assert len(history) == 2
        calc.clear_history()
        assert len(calc.get_history()) == 0

    # ===== Failing Tests (5 bugs to fix) =====

    def test_divide_by_zero(self, calc):
        """Test that division by zero raises an error."""
        # BUG 1: Should raise ZeroDivisionError or return appropriate error
        with pytest.raises(ZeroDivisionError):
            calc.divide(10, 0)

    def test_percentage_precision(self, calc):
        """Test percentage calculation with precision."""
        # BUG 2: Float precision - 15% of 200 should be exactly 30.0
        result = calc.percentage(200, 15)
        assert result == 30.0  # This might fail due to float precision

    def test_sum_range_inclusive(self, calc):
        """Test that sum_range includes n."""
        # BUG 3: Sum of 1 to 5 should be 1+2+3+4+5 = 15
        assert calc.sum_range(5) == 15

    def test_expression_order_of_operations(self, calc):
        """Test correct order of operations."""
        # BUG 4: 2 + 3 * 4 should be 2 + 12 = 14, not (2+3)*4 = 20
        assert calc.calculate_expression(2, 3, 4) == 14

    def test_safe_divide_with_none(self, calc):
        """Test safe_divide handles None input."""
        # BUG 5: Should handle None gracefully
        result = calc.safe_divide(None, 2)
        assert result == 0  # Or raise a proper error
