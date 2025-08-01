# Example with runtime error
print("Starting the program...")
print("This line will execute fine")

# This will cause a runtime error
try:
    result = 10 / 0  # Division by zero
    print(f"Result: {result}")
except ZeroDivisionError as e:
    print(f"Caught an error: {e}")

print("Program completed!")
