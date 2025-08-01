#include <iostream>
#include <vector>
#include <cmath>
#include <iomanip>
using namespace std;

class FibonacciCalculator {
public:
    static long long calculate(int n) {
        if (n <= 1) return n;
        return calculate(n-1) + calculate(n-2);
    }
};

bool isPrime(long long num) {
    if (num < 2) return false;
    for (long long i = 2; i <= sqrt(num); i++) {
        if (num % i == 0) return false;
    }
    return true;
}

int main() {
    vector<int> numbers = {5, 10, 15, 20};
    
    cout << "C++ Complex Example - Fibonacci and Prime Check" << endl;
    cout << string(50, '=') << endl;
    
    for (int num : numbers) {
        long long fib = FibonacciCalculator::calculate(num);
        bool prime = isPrime(fib);
        
        cout << fixed << setprecision(0);
        cout << "fibonacci(" << num << ") = " << fib 
             << ", is_prime = " << (prime ? "true" : "false") << endl;
    }
    
    cout << "\n🚀 C++ calculation completed successfully!" << endl;
    cout << "Docker containerization working perfectly!" << endl;
    
    return 0;
}
