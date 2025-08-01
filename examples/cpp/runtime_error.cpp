#include <iostream>
#include <vector>
using namespace std;

int main() {
    vector<int> numbers = {1, 2, 3, 4, 5};
    
    cout << "Accessing vector elements:" << endl;
    cout << "This will cause a runtime error (segmentation fault)" << endl;
    
    // This will go out of bounds and cause a runtime error
    for (int i = 0; i < 10; i++) {
        cout << "numbers[" << i << "] = " << numbers[i] << endl;
    }
    
    return 0;
}
