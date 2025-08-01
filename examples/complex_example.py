# More complex example with libraries
import math
import datetime
import json

print("=== Python Libraries Demo ===")

# Math operations
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
print(f"Numbers: {numbers}")
print(f"Sum: {sum(numbers)}")
print(f"Average: {sum(numbers) / len(numbers)}")
print(f"Square root of 64: {math.sqrt(64)}")
print(f"Pi: {math.pi}")

# Date and time
now = datetime.datetime.now()
print(f"\nCurrent date and time: {now}")
print(f"Formatted: {now.strftime('%Y-%m-%d %H:%M:%S')}")

# JSON handling
data = {
    "name": "Python Docker Compiler",
    "version": "1.0",
    "features": ["syntax checking", "code execution", "error reporting"],
    "timestamp": now.isoformat()
}

json_str = json.dumps(data, indent=2)
print(f"\nJSON data:\n{json_str}")

# List comprehension
squares = [x**2 for x in range(1, 6)]
print(f"\nSquares of 1-5: {squares}")

print("\n=== Demo completed successfully! ===")
